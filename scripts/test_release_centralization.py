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
tracker = _build_target_run_tracker(tracker_proxy, '.github/workflows/release-aab.yml')
tracker_doc = load_yaml(tracker)
assert TRACKER_MARKER in tracker
assert tracker_doc['name'] == 'Release AAB to Play'
assert 'push' in tracker_doc['on']
assert 'workflow_dispatch' in tracker_doc['on']
assert tracker_doc['permissions']['statuses'] == 'read'
assert tracker_doc['permissions']['actions'] == 'read'
assert 'central-status' in tracker_doc['jobs']
assert 'central-dispatch' not in tracker_doc['jobs']
tracker_run = tracker_doc['jobs']['central-status']['steps'][0]['run']
assert 'statuses/$TARGET_SHA' in tracker_run
assert 'Central workflow state:' in tracker_run
assert 'curl ' not in tracker_run

play_workflow = Path('.github/workflows/android-play-release.yml').read_text(encoding='utf-8')
assert "HTTP_TIMEOUT_SECONDS=120" in play_workflow
assert "httplib2.Http(timeout=HTTP_TIMEOUT_SECONDS)" in play_workflow
assert "timeout 1800 python" in play_workflow  # hard wall-clock cap on the whole publish step
# The AAB upload observably needs more than 120s against Play's upload
# endpoint (measured: a 445MB bundle timed out three times in a row at
# 120s while the same file hit GitHub's blob storage in ~14s). It gets its
# own generous timeout and a single attempt at that layer; the outer
# edit-retry loop still retries the whole edit (fresh upload included).
assert "UPLOAD_TIMEOUT_SECONDS=600" in play_workflow
assert "httplib2.Http(timeout=UPLOAD_TIMEOUT_SECONDS)" in play_workflow
assert "upload_svc.edits().bundles().upload(" in play_workflow
assert "return execute(request, retries=1)" in play_workflow
assert "resumable=False" in play_workflow
assert "RedirectMissingLocation" in play_workflow
assert "next_chunk(num_retries=REQUEST_RETRIES)" not in play_workflow
assert "except transient as exc:" in play_workflow
assert "return request.execute(num_retries=retries)" in play_workflow
assert "MediaFileUpload(aab,mimetype='application/octet-stream')).execute()" not in play_workflow
assert "Resolve required mapping.txt" in play_workflow
assert "Upload mapping.txt artifact" in play_workflow
assert "Play publishing requires a nonempty R8/ProGuard mapping.txt" in play_workflow
assert "MAPPING_FILE: ${{ env.MAPPING_FILE }}" in play_workflow
assert "deobfuscationfiles().upload" in play_workflow
assert "Required mapping.txt is missing or empty" in play_workflow
# Play's deobfuscationFiles endpoint rejects text/plain outright (400 "Media type
# 'text/plain' is not supported."); the mapping.txt upload must use octet-stream,
# same as the AAB upload, or every publish attempt fails identically and forever.
assert "media_body=MediaFileUpload(mapping,mimetype='application/octet-stream')" in play_workflow
assert "media_body=MediaFileUpload(mapping,mimetype='text/plain')" not in play_workflow
# A 4xx HttpError is normally deterministic, not transient: retrying it just
# re-uploads the whole AAB from scratch for a request that can never succeed.
# Only 429/5xx and real transport failures should trigger a retry — except a
# 400 "not completed yet" from edits.commit, a real observed eventual-consistency
# race on Play's backend right after bundles().upload(), which is worth retrying.
assert "def is_retriable(exc):" in play_workflow
assert "not is_retriable(exc):" in play_workflow
assert "'not completed yet' in content" in play_workflow

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
