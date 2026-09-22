#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

from sync_repository import compile_central, load_yaml
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

play_workflow = Path('.github/workflows/android-play-release.yml').read_text(encoding='utf-8')
assert "HTTP_TIMEOUT_SECONDS=180" in play_workflow
assert "httplib2.Http(timeout=HTTP_TIMEOUT_SECONDS)" in play_workflow
assert "resumable=False" in play_workflow
assert "RedirectMissingLocation" in play_workflow
assert "return execute(request)" in play_workflow
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

for play_path, required in {
    ".github/workflows/cuedetat-play-publish.yml": (
        "Upload mapping.txt artifact",
        "PLAY_MAPPING_PATH: ${{ steps.mapping.outputs.path }}",
    ),
    ".github/workflows/qard-play-release.yml": (
        "Upload mapping.txt artifact",
        "mappingFile: ${{ steps.mapping.outputs.path }}",
    ),
    ".github/workflows/hg2gui-release-play.yml": (
        "Upload mapping.txt artifact",
        "mapping: ${{ steps.mapping.outputs.path }}",
    ),
    ".github/workflows/hereliesaz-github-io-android-release-aab.yml": (
        "Upload mapping.txt artifact",
        "deobfuscationfiles().upload",
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
