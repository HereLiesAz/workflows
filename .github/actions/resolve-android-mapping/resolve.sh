#!/usr/bin/env bash
# Resolve the R8/ProGuard mapping.txt for an App Bundle into $RUNNER_TEMP/mapping.txt.
# Order: explicit MAPPING_FILE, the bundle variant's build output, any build output, then the
# copy AGP embeds in the bundle. Fails when none exists: Play releases must ship a mapping.
set -euo pipefail
mapping="${MAPPING_FILE:-}"
if [ -n "$mapping" ] && [ ! -s "$mapping" ]; then
  echo "::error::Configured mapping_file does not exist or is empty: $mapping" >&2
  exit 1
fi
if [ -z "$mapping" ]; then
  module="${AAB_PATH%%/build/outputs/bundle/*}"
  relative="${AAB_PATH#*/build/outputs/bundle/}"
  variant="${relative%%/*}"
  candidate="$module/build/outputs/mapping/$variant/mapping.txt"
  if [ -s "$candidate" ]; then mapping="$candidate"; fi
fi
if [ -z "$mapping" ]; then
  mapping="$(find . -type f -path '*/build/outputs/mapping/*/mapping.txt' -size +0c | sort | head -1 || true)"
fi
canonical="$RUNNER_TEMP/mapping.txt"
if [ -z "$mapping" ]; then
  embedded='BUNDLE-METADATA/com.android.tools.build.obfuscation/proguard.map'
  if unzip -Z1 "$AAB_PATH" | grep -Fxq "$embedded"; then
    unzip -p "$AAB_PATH" "$embedded" > "$canonical"
    mapping="$canonical"
  fi
fi
test -n "$mapping" && test -s "$mapping" || {
  echo "::error::Play publishing requires a nonempty R8/ProGuard mapping.txt, but none was produced for $AAB_PATH" >&2
  exit 1
}
if [ "$mapping" != "$canonical" ]; then cp "$mapping" "$canonical"; fi
test -s "$canonical"
echo "MAPPING_FILE=$canonical" >> "$GITHUB_ENV"
echo "path=$canonical" >> "$GITHUB_OUTPUT"
