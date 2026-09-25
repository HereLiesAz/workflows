#!/usr/bin/env python3
"""Publish an Android App Bundle and its R8 mapping to Google Play tracks.

Shared by the android-play-release workflow and target repositories through
.github/actions/google-play-publish. Configuration arrives through environment variables:
PLAY_SERVICE_ACCOUNT_JSON, PACKAGE_NAME, AAB_PATH, TRACKS_JSON, MAPPING_FILE,
optional RELEASE_NOTES_DIR and DRAFT_FALLBACK.
"""
import json, os, signal, time
import httplib2
from google.oauth2 import service_account
from google_auth_httplib2 import AuthorizedHttp
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

# Per-socket-operation timeout for ordinary (small, metadata) calls.
# Does not guard against servers that accept the connection and then
# stall mid-stream; the outer bash timeout 1800 is the hard
# wall-clock cap for the whole publish step.
HTTP_TIMEOUT_SECONDS=120
# The AAB itself routinely runs 400-500MB. Observed live: three
# consecutive edits().bundles().upload() calls each raised
# "TimeoutError: The read operation timed out" against the 120s
# socket timeout, while the same file uploaded to GitHub's own blob
# storage in ~14s — Play's upload endpoint is measurably slower and
# 120s isn't enough margin for a non-resumable multipart POST of
# this size. Give the bundle upload its own generous timeout and
# only one attempt at this layer: the outer edit-retry loop (below)
# already retries the whole edit, including a fresh upload, with
# backoff, so retrying the same stalled connection a second time at
# this layer just wastes the socket timeout twice for no benefit.
UPLOAD_TIMEOUT_SECONDS=600
REQUEST_RETRIES=3
EDIT_ATTEMPTS=4

info=json.loads(os.environ['PLAY_SERVICE_ACCOUNT_JSON'])
creds=service_account.Credentials.from_service_account_info(
    info,
    scopes=['https://www.googleapis.com/auth/androidpublisher'],
)
http=AuthorizedHttp(creds, http=httplib2.Http(timeout=HTTP_TIMEOUT_SECONDS))
svc=build('androidpublisher','v3',http=http,cache_discovery=False)
upload_http=AuthorizedHttp(creds, http=httplib2.Http(timeout=UPLOAD_TIMEOUT_SECONDS))
upload_svc=build('androidpublisher','v3',http=upload_http,cache_discovery=False)
package=os.environ['PACKAGE_NAME']
aab=os.environ['AAB_PATH']
tracks=json.loads(os.environ['TRACKS_JSON'])

# Localized "What's new" text: whatsnew-<lang> files (fastlane/r0adkll layout), else default.txt as en-US.
# Play caps each language at 500 characters.
PLAY_NOTES_LIMIT=500
release_notes=[]
notes_dir=os.environ.get('RELEASE_NOTES_DIR', '').strip()
if notes_dir and os.path.isdir(notes_dir):
    for name in sorted(os.listdir(notes_dir)):
        if name.startswith('whatsnew-'):
            with open(os.path.join(notes_dir, name), encoding='utf-8') as handle:
                text=handle.read().strip()[:PLAY_NOTES_LIMIT]
            if text:
                release_notes.append({'language': name[len('whatsnew-'):], 'text': text})
    default_notes=os.path.join(notes_dir, 'default.txt')
    if not release_notes and os.path.isfile(default_notes):
        with open(default_notes, encoding='utf-8') as handle:
            text=handle.read().strip()[:PLAY_NOTES_LIMIT]
        if text:
            release_notes.append({'language': 'en-US', 'text': text})

def execute(request, retries=REQUEST_RETRIES):
    return request.execute(num_retries=retries)

def upload_bundle(edit_id):
    # Android Publisher's resumable upload uses HTTP 308 responses without
    # a Location header. httplib2 treats those as broken redirects before
    # googleapiclient can process the upload range, raising
    # RedirectMissingLocation. Use a single multipart upload here instead;
    # the outer edit retry loop still retries transient transport failures.
    request=upload_svc.edits().bundles().upload(
        packageName=package,
        editId=edit_id,
        media_body=MediaFileUpload(
            aab,
            mimetype='application/octet-stream',
            resumable=False,
        ),
    )
    return execute(request, retries=1)

transient=(HttpError, TimeoutError, ConnectionError, httplib2.HttpLib2Error)

def is_retriable(exc):
    # A 4xx HttpError (bad request, bad mimetype, permission denied, ...) is
    # normally never transient: the exact same request fails the exact same
    # way every time, so retrying it just re-uploads the whole AAB from
    # scratch on each attempt for no benefit. Only 429/5xx responses, and
    # non-HTTP transport failures (timeouts, connection resets), are worth
    # a retry — with one deliberate exception below.
    if isinstance(exc, HttpError):
        status=getattr(getattr(exc, 'resp', None), 'status', None)
        if status == 429 or (status is not None and 500 <= status < 600):
            return True
        if status == 400:
            # Play's edits.commit can 400 with "Some of the Android App
            # Bundle uploads are not completed yet" immediately after a
            # successful bundles().upload() — the backend hasn't finished
            # indexing the bundle it just accepted. This is a real,
            # observed eventual-consistency race on Google's side, not a
            # malformed request; retrying the edit (with backoff) after a
            # brief wait resolves it.
            content=getattr(exc, 'content', b'') or b''
            if isinstance(content, bytes):
                content=content.decode('utf-8', 'ignore')
            return 'not completed yet' in content
        return False
    return True

def is_upgrade_path_error(exc):
    # Play's live-rollout precondition: every existing user on the track must have an
    # upgrade path to the new bundle. When device targeting (ABIs, minSdk, densities)
    # no longer covers someone already installed, edits.commit 403s with "You cannot
    # rollout this release because it does not allow any existing users to upgrade to
    # the newly added APKs." Retrying the same live rollout fails identically.
    content=getattr(exc, 'content', b'') or b''
    if isinstance(content, bytes):
        content=content.decode('utf-8', 'ignore')
    text=(str(exc) + ' ' + str(content)).lower()
    return 'existing users' in text and 'upgrade' in text

# Profiles opting in (live_rollout_draft_fallback) stage the same bundle as a draft when
# Play refuses the live rollout, so a targeting regression costs a manual rollout click
# in the Play Console instead of failing the whole release. Ported from the target's
# original publish_play.py, which carried this fallback before centralization.
draft_fallback=os.environ.get('DRAFT_FALLBACK', 'false').strip().lower() == 'true'
downgrade_live=False

for attempt in range(1,EDIT_ATTEMPTS + 1):
    edit=None
    try:
        edit=execute(svc.edits().insert(packageName=package,body={}))['id']
        bundle=upload_bundle(edit)
        code=str(bundle['versionCode'])
        mapping=os.environ['MAPPING_FILE']
        if not os.path.isfile(mapping) or os.path.getsize(mapping) == 0:
            raise RuntimeError(f'Required mapping.txt is missing or empty: {mapping}')
        execute(svc.edits().deobfuscationfiles().upload(
            packageName=package,
            editId=edit,
            apkVersionCode=code,
            deobfuscationFileType='proguard',
            media_body=MediaFileUpload(mapping,mimetype='application/octet-stream'),
        ))
        print(f'Uploaded mapping.txt for versionCode {code}')
        for spec in tracks:
            # Opening a draft on beta/production commonly fails on projects that have
            # never promoted a release to that track yet (Play requires prior track
            # history). That is expected, not a publish failure: skip the track instead
            # of failing the whole run. internal/alpha and any non-draft release still
            # fail hard, since those are the actual publish action.
            optional_track=spec.get('status') == 'draft' and spec.get('track') in ('beta', 'production')
            try:
                status=spec['status']
                if downgrade_live and status == 'completed':
                    status='draft'
                release={'versionCodes':[code],'status':status}
                if release_notes:
                    release['releaseNotes']=release_notes
                if spec.get('name'):
                    release['name']=os.path.expandvars(str(spec['name']))
                releases=[release]
                if spec.get('preserve_existing'):
                    current=execute(svc.edits().tracks().get(
                        packageName=package,
                        editId=edit,
                        track=spec['track'],
                    ))
                    releases=[
                        item for item in current.get('releases', [])
                        if item.get('status') != 'draft'
                        and code not in [str(value) for value in item.get('versionCodes', [])]
                    ] + [release]
                body={'track':spec['track'],'releases':releases}
                execute(svc.edits().tracks().update(
                    packageName=package,
                    editId=edit,
                    track=spec['track'],
                    body=body,
                ))
            except Exception as exc:
                if optional_track:
                    print(
                        f'Warning: could not open a draft on track {spec["track"]!r}; '
                        f'skipping without failing the release: {exc}',
                        flush=True,
                    )
                    continue
                raise
        execute(svc.edits().commit(packageName=package,editId=edit))
        if downgrade_live:
            print(f'Published versionCode {code} to {tracks} with live rollouts staged as drafts', flush=True)
        else:
            print(f'Published versionCode {code} to {tracks}')
        break
    except transient as exc:
        if edit:
            try:
                execute(svc.edits().delete(packageName=package,editId=edit), retries=2)
            except Exception as cleanup_exc:
                print(f'Warning: could not discard failed Play edit {edit}: {cleanup_exc}', flush=True)
        if draft_fallback and not downgrade_live and attempt < EDIT_ATTEMPTS and is_upgrade_path_error(exc):
            print(
                f'::warning::Play refused the live rollout: {exc}. Staging this versionCode as a '
                'draft instead; review device targeting and roll it out in the Play Console.',
                flush=True,
            )
            downgrade_live=True
            continue
        if attempt == EDIT_ATTEMPTS or not is_retriable(exc):
            raise
        wait=min(60, 5 * 2 ** (attempt-1))
        print(
            f'Play edit attempt {attempt} failed with {type(exc).__name__}: '
            f'{exc}; retrying in {wait}s',
            flush=True,
        )
        time.sleep(wait)
