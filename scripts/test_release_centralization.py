#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

from sync_repository import TRACKER_MARKER, _build_target_run_tracker, build_proxy, compile_central, load_yaml
from shared_workflow_library import semantic_family_slug

def expression(body: str) -> str:
    return '${' + '{ ' + body + ' }}'

source = '''
name: release
on:
  push:
    tags: ['v*']
  workflow_dispatch:
permissions:
  contents: write
jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - name: Publish release
        uses: softprops/action-gh-release@v2
        with:
          files: '*.azp'
'''

compiled = compile_central(
    source,
    {'full_name': 'HereLiesAz/fixture', 'private': False},
    '.github/workflows/release.yml',
    'release',
)
doc = load_yaml(compiled)
release = doc['jobs']['release']
assert release['permissions']['contents'] == 'write', release.get('permissions')

release_step = next(
    step for step in release['steps']
    if isinstance(step, dict)
    and str(step.get('uses') or '').startswith('softprops/action-gh-release@')
)
assert release_step['with']['repository'] == expression('inputs.target_repository')
assert release_step['with']['token'] == expression('secrets.GH_TOKEN')
assert release_step['with']['tag_name'] == expression('inputs.target_ref_name')
assert any(
    isinstance(step, dict)
    and step.get('name') == 'Validate target release ref'
    for step in release['steps']
)

family = semantic_family_slug(
    'release',
    '.github/workflows/release.yml',
    compiled,
)
assert family == 'node-release', family

tracker_source = '''
name: Release AAB to Play
on:
  push:
    branches: [main]
    paths-ignore:
      - version.properties
  workflow_dispatch:
    inputs:
      publish:
        default: true
jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - run: echo centralized
'''
tracker_proxy = build_proxy(
    tracker_source,
    '.github/workflows/release-aab.yml',
    '09adb91f6846d345ebb261ae428ad9412bfbfac6fe1d1192a726b84546b46928',
    'Release AAB to Play',
)
tracker = _build_target_run_tracker(
    tracker_proxy,
    '.github/workflows/release-aab.yml',
    Path('.github/workflows/android-play-release.yml').read_text(encoding='utf-8'),
)
tracker_doc = load_yaml(tracker)
assert TRACKER_MARKER in tracker
assert tracker_doc['name'] == 'Release AAB to Play'
assert 'push' in tracker_doc['on']
assert 'workflow_dispatch' in tracker_doc['on']
assert tracker_doc['permissions']['statuses'] == 'read'
assert tracker_doc['permissions']['actions'] == 'read'
assert 'central-dispatch' not in tracker_doc['jobs']
# One tracker job per central job, same names and dependency order, bookkeeping hidden.
assert list(tracker_doc['jobs']) == ['central', 'version_contract', 'build_and_publish'], list(tracker_doc['jobs'])
assert tracker_doc['jobs']['build_and_publish']['needs'] == ['central', 'version_contract']
assert tracker_doc['jobs']['version_contract']['needs'] == ['central']
locate_run = tracker_doc['jobs']['central']['steps'][0]['run']
assert 'statuses/$TARGET_SHA' in locate_run
assert 'No run of this workflow was started' in locate_run
follow_run = tracker_doc['jobs']['build_and_publish']['steps'][0]['run']
assert '/logs' in follow_run and 'curl ' not in follow_run and 'dispatches' not in follow_run

# The Play publisher lives in shared actions the workflow calls; check the contract across all of them.
play_workflow = Path('.github/workflows/android-play-release.yml').read_text(encoding='utf-8')
play_contract = "\n".join(
    Path(path).read_text(encoding='utf-8')
    for path in (
        '.github/workflows/android-play-release.yml',
        '.github/actions/resolve-android-mapping/action.yml',
        '.github/actions/resolve-android-mapping/resolve.sh',
        '.github/actions/google-play-publish/action.yml',
        '.github/actions/google-play-publish/publish.py',
    )
)
assert "uses: HereLiesAz/workflows/.github/actions/resolve-android-mapping@main" in play_contract
assert "uses: HereLiesAz/workflows/.github/actions/google-play-publish@main" in play_contract
assert "HTTP_TIMEOUT_SECONDS=120" in play_contract
assert "httplib2.Http(timeout=HTTP_TIMEOUT_SECONDS)" in play_contract
assert "timeout 1800 python" in play_contract  # hard wall-clock cap on the whole publish step
# The AAB upload observably needs more than 120s against Play's upload
# endpoint (measured: a 445MB bundle timed out three times in a row at
# 120s while the same file hit GitHub's blob storage in ~14s). It gets its
# own generous timeout and a single attempt at that layer; the outer
# edit-retry loop still retries the whole edit (fresh upload included).
assert "UPLOAD_TIMEOUT_SECONDS=600" in play_contract
assert "httplib2.Http(timeout=UPLOAD_TIMEOUT_SECONDS)" in play_contract
assert "upload_svc.edits().bundles().upload(" in play_contract
assert "return execute(request, retries=1)" in play_contract
assert "resumable=False" in play_contract
assert "RedirectMissingLocation" in play_contract
assert "next_chunk(num_retries=REQUEST_RETRIES)" not in play_contract
assert "except transient as exc:" in play_contract
assert "return request.execute(num_retries=retries)" in play_contract
assert "MediaFileUpload(aab,mimetype='application/octet-stream')).execute()" not in play_contract
assert "Resolve required mapping.txt" in play_contract
assert "Upload mapping.txt artifact" in play_contract
assert "Play publishing requires a nonempty R8/ProGuard mapping.txt" in play_contract
assert "mapping-file: ${{ env.MAPPING_FILE }}" in play_contract
assert "MAPPING_FILE: ${{ steps.mapping.outputs.path }}" in play_contract
assert "deobfuscationfiles().upload" in play_contract
assert "Required mapping.txt is missing or empty" in play_contract
# Play's deobfuscationFiles endpoint rejects text/plain outright (400 "Media type
# 'text/plain' is not supported."); the mapping.txt upload must use octet-stream,
# same as the AAB upload, or every publish attempt fails identically and forever.
assert "media_body=MediaFileUpload(mapping,mimetype='application/octet-stream')" in play_contract
assert "media_body=MediaFileUpload(mapping,mimetype='text/plain')" not in play_contract
# A 4xx HttpError is normally deterministic, not transient: retrying it just
# re-uploads the whole AAB from scratch for a request that can never succeed.
# Only 429/5xx and real transport failures should trigger a retry — except a
# 400 "not completed yet" from edits.commit, a real observed eventual-consistency
# race on Play's backend right after bundles().upload(), which is worth retrying.
assert "def is_retriable(exc):" in play_contract
assert "not is_retriable(exc):" in play_contract
assert "'not completed yet' in content" in play_contract

for play_path, required in {
    ".github/workflows/android-play-release.yml": (
        "Upload mapping.txt artifact",
        "google-play-publish@main",
    ),
    ".github/actions/google-play-publish/publish.py": (
        "deobfuscationfiles().upload",
        "release['releaseNotes']=release_notes",
    ),
}.items():
    text = Path(play_path).read_text(encoding="utf-8")
    for token in required:
        assert token in text, f"{play_path} missing required Play mapping contract: {token}"

android_github_release = Path(
    ".github/workflows/android-github-release.yml"
).read_text(encoding="utf-8")
assert "Upload mapping.txt as workflow artifact" in android_github_release
assert "mapping_asset" not in android_github_release
assert "MAPPING_ASSET" not in android_github_release
assert 'release-files/$(basename "$MAPPING' not in android_github_release


multi_platform_release = Path(
    '.github/workflows/multi-platform-app-release.yml'
).read_text(encoding='utf-8')
assert 'workflow_call:' in multi_platform_release
assert 'reuse_existing_tag="$(jq -r \'.reuse_existing_tag // false\'' in multi_platform_release
assert 'Keeping stable grouped-release tag $TAG' in multi_platform_release
assert "migrate_build_releases" in multi_platform_release
assert 'gh release delete "$legacy_tag" --repo "$TARGET_REPOSITORY" --yes' in multi_platform_release
assert 'legacy_asset_count=' in multi_platform_release
assert 'Downloaded $downloaded_count of $legacy_asset_count assets' in multi_platform_release
assert 'Source run SHA $run_sha does not match target SHA $TARGET_SHA' in multi_platform_release
assert '--prerelease="$prerelease"' in multi_platform_release
assert 'git tag -fa "$TAG"' in multi_platform_release  # retained only for explicit force_tag profiles

print('release centralization regression test passed')

# Every active binding gets a tracker; other entries get none.
import sync_repository as _sync
import sync_repository_catalog as _core


class _FakeGitHub:
    def __init__(self, files):
        self.files = files

    def get_file(self, full_name, path, ref=None):
        key = (full_name, path)
        if key not in self.files:
            raise _core.ApiError(f"GET {path} -> 404: Not Found")
        return self.files[key], "sha"


_staged = {'.github/workflows/release-aab.yml': (None, 'remove proxy')}
_sync._stage_trackers(
    _FakeGitHub({
        (_core.CENTRAL_REPOSITORY, 'registry/1/release.source.yml'): tracker_source,
        (_core.CENTRAL_REPOSITORY, '.github/workflows/android-play-release.yml'): play_workflow,
    }),
    {'workflows': {
        '.github/workflows/release-aab.yml': {
            'status': 'active',
            'central_workflow': '.github/workflows/android-play-release.yml',
            'registry_source': 'registry/1/release.source.yml',
            'source_sha256': '09adb91f6846d345ebb261ae428ad9412bfbfac6fe1d1192a726b84546b46928',
            'name': 'Release AAB to Play',
        },
        '.github/workflows/ci.yml': {'status': 'obsolete', 'central_workflow': '.github/workflows/ci-validation.yml'},
    }},
    _staged,
)
assert list(_staged) == ['.github/workflows/release-aab.yml'], _staged
_restored = _staged['.github/workflows/release-aab.yml'][0]
assert _restored is not None and TRACKER_MARKER in _restored
assert 'build_and_publish' in load_yaml(_restored)['jobs']
