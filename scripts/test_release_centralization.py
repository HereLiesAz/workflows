#!/usr/bin/env python3
from __future__ import annotations

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
print('release centralization regression test passed')
