# Android release: one workflow, one versioning rule

`.github/workflows/android-release.yml` builds, signs, versions and publishes every HereLiesAz
Android app. Apps are moved onto it one at a time (catalog: `SEMANTIC_WORKFLOWS` in
`scripts/semantic_catalog.py`); the rest still run `android-play-release.yml` /
`android-github-release.yml` or their own workflows until migrated.

## Versioning

~~~
versionCode = max(versionCode recorded in version.properties,
                  highest versionCode Google Play ever accepted for the package) + 1
versionName = versionMajor.versionMinor.versionPatch . (last field of the previous versionName + 1)
~~~

- Play is read across every bundle, APK and track release, drafts included.
- Nothing is added, multiplied, padded or derived from run numbers, timestamps or commit counts.
- `versionMajor`, `versionMinor` and `versionPatch` are edited by hand when a release means it.
- Gradle receives exactly `-PversionCode` and `-PversionName`. An app's build reads those, falling
  back to `versionCode` / `versionName` in `version.properties` for local builds, and never
  increments anything itself.
- After a successful publish, a separate job (no signing key or Play credential) records
  `versionCode`, `versionName` and `versionBuild` back into `version.properties` on the default
  branch with a `[skip ci]` commit. Failed or unpublished builds record nothing.
- Runs for one app are serialized, so two runs never compute the same code.

Implementation: `.github/actions/android-version` (tests: `scripts/test_android_version.py`).

## Signing

Gradle sees the upload key as `KEYSTORE_FILE`, `KEYSTORE_PASSWORD`, `KEY_ALIAS`, `KEY_PASSWORD`.
The workflow builds the keystore from `KEYSTORE_RAW` (base64). Apps whose environment still holds
the legacy `KEYSTORE_PRIVATE` + `KEYSTORE_CHAIN` pair are converted on the fly until `KEYSTORE_RAW`
is added.

## Publishing

Only pushes and dispatches on the default branch publish (a dispatch with `publish: false` or
`dry_run: true` builds only). Everything else builds and stops.

## Profile fields

| Field | Meaning |
|---|---|
| `build_command` | Gradle invocation (required); the version arguments are appended |
| `aab_glob`, `apk_glob` | Outputs; the first match is used |
| `package_name` | Application ID (required for Play) |
| `play_tracks` | `PLAY_TRACKS` for every Play app (internal, alpha, beta live; production draft); empty = no Play. `beta`/`production` are skipped when Play does not offer them for the app, and fail the release otherwise |
| `github_release` | Create `v<versionName>` release with the APK (universal APK from the AAB when no APK) |
| `github_prerelease` | Default true |
| `release_app_name` | Asset and title name |
| `java_version` | Default 21 |
| `setup_android`, `android_packages` | Install SDK packages |
| `submodules` | Recursive submodule checkout |
| `pre_build_command` | Toolchain or generated-file setup |
| `google_services_path` | Write `GOOGLE_SERVICES` there |
| `arcore_local_properties` | Append `ARCORE_API_KEY` to `local.properties` |
| `build_secrets` / `required_build_secrets` | Build-time keys passed when set / required |
| `version_file` | Default `version.properties` |
