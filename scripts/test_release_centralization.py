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
assert "resumable=True" in play_workflow
assert "next_chunk(num_retries=REQUEST_RETRIES)" in play_workflow
assert "except transient as exc:" in play_workflow
assert "return request.execute(num_retries=retries)" in play_workflow
assert "MediaFileUpload(aab,mimetype='application/octet-stream')).execute()" not in play_workflow


multi_platform_release = Path(
    '.github/workflows/multi-platform-app-release.yml'
).read_text(encoding='utf-8')
assert 'workflow_call:' in multi_platform_release
assert 'reuse_existing_tag="$(jq -r \'.reuse_existing_tag // false\'' in multi_platform_release
assert 'Keeping stable grouped-release tag $TAG' in multi_platform_release
assert "migrate_build_releases" in multi_platform_release
assert 'gh release delete "$legacy_tag" --repo "$TARGET_REPOSITORY" --yes' in multi_platform_release
assert 'git tag -fa "$TAG"' in multi_platform_release  # retained only for explicit force_tag profiles

aive_release_source = Path(
    'registry/1031039591/multiplatform-ef9dd5d6.source.yml'
).read_text(encoding='utf-8')
assert (
    'uses: HereLiesAz/workflows/.github/workflows/multi-platform-app-release.yml@main'
    in aive_release_source
)
assert 'reuse_existing_tag' in aive_release_source
assert '"migrate_build_releases": true' in aive_release_source
assert '"serialize": false' in aive_release_source
assert '"tag_mode": "prepare-output"' in aive_release_source
assert 'version="${PATCH_VERSION}.${TARGET_RUN_NUMBER}"' in aive_release_source
assert 'tag="v${PATCH_VERSION}"' in aive_release_source
assert 'build_tag="v${version}"' in aive_release_source
assert 'TheAive-${RELEASE_VERSION}.deb' in aive_release_source
assert 'TheAive-${RELEASE_VERSION}.dmg' in aive_release_source
assert 'TheAive-$env:RELEASE_VERSION.msi' in aive_release_source
assert "if: github.event_name == 'pull_request'" in aive_release_source
assert 'Verify immutable release policy' not in aive_release_source

print('release centralization regression test passed')
