# Central release and version policy

Release/version semantics for centrally managed repositories live in **HereLiesAz/workflows**.

Projects may decide what they build, which files constitute a release, product-specific display names,
and platform-specific packaging. They should not duplicate account-wide release semantics in local
shell code.

## Four-part build identity

Projects that use four-part versions use:

`MAJOR.MINOR.PATCH.BUILD`

The first three components identify the patch line. BUILD identifies one exact CI build.

The reusable action:

`.github/actions/four-part-version`

derives the exact build version from a checked-in four-part baseline plus the supplied build number.
It can return the derived version as outputs and optionally export it into the caller environment.

A project should keep BUILD at `0` in source when BUILD is supplied by CI. A workflow run changes
only BUILD.

## Patch-grouped GitHub Releases

Tags are bare version numbers: no `v` prefix, no `version` word, no app name. For a four-part build
such as `0.9.6.412`:

- immutable exact-build tag: `0.9.6.412`
- grouped GitHub Release/tag: `0.9.6`
- every later `0.9.6.y` build is added to that same `0.9.6` Release; the next patch starts `0.9.7`

The reusable action:

`.github/actions/patch-grouped-release`

owns this behavior. It shares its publisher with `.github/actions/minor-grouped-release`, which
groups under `MAJOR.MINOR` instead and remains available for callers that pin it.

Exact build tags are never moved. The patch tag is created when the patch line is first published and
is not moved later. The GitHub Release attached to the patch tag is an **accumulating release
container**: it may receive additional uniquely named build artifacts and updated notes as new builds
in that patch line ship.

Artifact filenames must be collision-safe. The action either requires the four-part version in the
name or injects it before upload. An existing release asset is never replaced by different bytes.

## Legacy release migration

Older repositories may already have one GitHub Release object per exact build. During a grouped publication, the centralized action can migrate
those Release objects:

1. download each legacy Release's assets;
2. ensure each asset name contains its exact legacy version;
3. upload the asset to the patch-grouped Release idempotently;
4. delete the obsolete legacy **Release object**; and
5. preserve its exact Git tag.

Migration therefore reduces release-list noise without destroying exact-build provenance.

## Shared workflow families

The following generalized release families automatically apply patch grouping when their resolved
version is four-part:

- **Android GitHub Release**
- **Android Play Release** (its built-APK and Play-build GitHub releases)
- **Multi-Platform App Release**
- **Artifact GitHub Release**

Desktop and web builds released through **Multi-Platform App Release** and **Artifact GitHub Release**
share this same four-part contract and patch-grouping behavior with Android, so a product's releases
line up across every platform it ships on.

Profiles that do not resolve to `MAJOR.MINOR.PATCH.BUILD` retain their existing release behavior.
Rolling/latest aliases may still exist when a profile explicitly requires them; they are separate from
the immutable exact-build tag and patch-grouped historical release.

## Project responsibilities

A target repository still owns:

- source version baseline or version-contract inputs;
- build/test commands;
- platform-specific signing;
- artifact selection;
- product-specific artifact names and release title prefix;
- product changelog content.

The centralized workflow repository owns:

- four-part build derivation;
- immutable exact-build tag rules;
- patch grouping;
- asset collision rules;
- legacy four-part Release migration;
- prerelease/latest release flags when supplied by the profile.

Do not reimplement these rules in a target workflow. If the account-wide policy changes, update the
shared action/family here and let registered repositories consume that policy.
