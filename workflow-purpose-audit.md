# Workflow purpose audit

This report groups active workflows by **what they accomplish**, not by filename, repository, or implementation hash.

- Active centralized workflows: **65**
- Live workflows audited: **214** (including 149 local and 0 blocked)
- Purpose groups: **40**
- Manual-review workflows: **8**
- Same-repository/same-purpose groups: **23**

## Purpose groups

| Purpose | Workflows | Repositories | Source variants | Effects |
| --- | ---: | ---: | ---: | --- |
| `android-build-and-github-release` | 40 | 32 | 35 | android-build, artifact-upload, github-release, huggingface-publish, lint, tests |
| `github-pages-deploy` | 38 | 37 | 19 | pages-deploy |
| `release-other` | 32 | 17 | 32 | — |
| `pull-request-labeling` | 21 | 21 | 7 | labeling |
| `ci-validation` | 8 | 7 | 8 | artifact-upload, lint, tests |
| `jules-issue-automation` | 8 | 8 | 8 | — |
| `needs-manual-review` | 8 | 7 | 8 | — |
| `android-build` | 6 | 5 | 6 | android-build, artifact-upload |
| `wasm-ci` | 5 | 4 | 5 | android-build, artifact-upload, pages-deploy, tests, wasm-build |
| `dependency-graph-submission` | 4 | 4 | 4 | — |
| `android-publish-google-play` | 3 | 3 | 3 | android-build, artifact-upload, google-play |
| `contribution-guideline-review` | 3 | 3 | 3 | — |
| `gemini-issue-triage` | 3 | 3 | 3 | — |
| `gemini-task-dispatch` | 3 | 3 | 3 | — |
| `jules-agent` | 3 | 3 | 3 | jules-agent |
| `artifact-build` | 2 | 2 | 2 | artifact-upload |
| `build-cache-clear` | 2 | 2 | 2 | android-build, artifact-upload, cache-clear, tests |
| `java-gradle-ci-and-dependency-submission` | 2 | 2 | 1 | — |
| `jules-branch-automation` | 2 | 2 | 2 | — |
| `android-ci` | 1 | 1 | 1 | android-build, artifact-upload, tests |
| `android-multichannel-release` | 1 | 1 | 1 | android-build, github-release, google-play |
| `antigravity-issue-triage` | 1 | 1 | 1 | — |
| `antigravity-task-dispatch` | 1 | 1 | 1 | — |
| `code-security-scan` | 1 | 1 | 1 | codeql |
| `data-deduplication` | 1 | 1 | 1 | — |
| `data-enrichment` | 1 | 1 | 1 | — |
| `github-release` | 1 | 1 | 1 | github-release |
| `issue-reminder-automation` | 1 | 1 | 1 | — |
| `jules-branch-auto-merge` | 1 | 1 | 1 | jules-auto-merge |
| `jules-security-remediation` | 1 | 1 | 1 | — |
| `live-runtime-verification` | 1 | 1 | 1 | — |
| `maven-publish` | 1 | 1 | 1 | android-build, artifact-upload, maven-publish, pages-deploy |
| `multi-platform-app-release` | 1 | 1 | 1 | android-build, desktop-build, github-release, tests |
| `multi-target-app-release` | 1 | 1 | 1 | android-build, github-release, python-executable |
| `npm-publish` | 1 | 1 | 1 | npm-publish |
| `painting-removal` | 1 | 1 | 1 | file-server-deploy |
| `registry-catalog-sync` | 1 | 1 | 1 | artifact-upload, vercel-deploy |
| `repository-visibility-policy` | 1 | 1 | 1 | artifact-upload, repository-visibility |
| `theater-bake` | 1 | 1 | 1 | file-server-deploy |
| `vercel-deploy` | 1 | 1 | 1 | vercel-deploy |

## Same repository, same purpose

### HereLiesAz/BluSnu — `android-build-and-github-release`
- `.github/workflows/build-release.yml` — On-Demand Release Build
- `.github/workflows/merged-build.yml` — Merged Build (Debug)

### HereLiesAz/CleanUnderwear — `android-build-and-github-release`
- `.github/workflows/android-ci.yml` — Android CI
- `.github/workflows/merged-build.yml` — PR Verification & Merge Release

### HereLiesAz/CleanUnderwear — `release-other`
- `.github/workflows/android-github-release.yml` — Android GitHub Release
- `.github/workflows/android-play-release.yml` — Android Play Release

### HereLiesAz/CueDetat — `android-build-and-github-release`
- `.github/workflows/android-ci.yml` — Android CI
- `.github/workflows/android_debug_apk_release.yml` — Merged Build & Release
- `.github/workflows/android_release.yml` — Android Release Build

### HereLiesAz/GraffitiXR — `android-build-and-github-release`
- `.github/workflows/android-ci.yml` — Android CI
- `.github/workflows/release-apk.yml` — Compile and Release APK

### HereLiesAz/Graffux — `release-other`
- `.github/workflows/android-github-release.yml` — Graffux Android GitHub Release
- `.github/workflows/android-play-release.yml` — Graffux Android Play Release

### HereLiesAz/Guillotine — `android-build-and-github-release`
- `.github/workflows/merged-build.yml` — Merged Build & Release
- `.github/workflows/release-desktop.yml` — Release Desktop Installers

### HereLiesAz/IDEaz — `release-other`
- `.github/workflows/android-github-release.yml` — IDEaz Android GitHub Release
- `.github/workflows/android-play-release.yml` — IDEaz Android Play Release

### HereLiesAz/LogKitty — `android-build-and-github-release`
- `.github/workflows/android-ci.yml` — Android CI
- `.github/workflows/android-release-apk.yml` — Compile and Release APK
- `.github/workflows/build-and-release.yml` — Merged Build & Release

### HereLiesAz/LogKitty — `release-other`
- `.github/workflows/android-github-release.yml` — Android GitHub Release
- `.github/workflows/android-play-release.yml` — Android Play Release

### HereLiesAz/MadeMeDance — `release-other`
- `.github/workflows/android-github-release.yml` — Android GitHub Release
- `.github/workflows/android-play-release.yml` — Android Play Release

### HereLiesAz/MeatPiety — `release-other`
- `.github/workflows/android-github-release.yml` — Android GitHub Release
- `.github/workflows/android-play-release.yml` — Android Play Release

### HereLiesAz/SphereSLAM — `android-build`
- `.github/workflows/ci.yml` — CI
- `.github/workflows/testapp.yml` — Test app

### HereLiesAz/TheLexorcist — `release-other`
- `.github/workflows/android-github-release.yml` — Android GitHub Release
- `.github/workflows/android-play-release.yml` — Android Play Release

### HereLiesAz/aive — `needs-manual-review`
- `.github/workflows/orchestration-specialist-training.yml` — Orchestration Specialist Training
- `.github/workflows/security-review.yml` — Security Review

### HereLiesAz/clappiest — `release-other`
- `.github/workflows/android-github-release.yml` — Android GitHub Release
- `.github/workflows/android-play-release.yml` — Android Play Release

### HereLiesAz/convey — `github-pages-deploy`
- `.github/workflows/jekyll-gh-pages.yml` — Deploy Jekyll with GitHub Pages dependencies preinstalled
- `.github/workflows/static.yml` — Deploy static content to Pages

### HereLiesAz/illumera — `release-other`
- `.github/workflows/android-github-release.yml` — illumera Android GitHub Release
- `.github/workflows/android-play-release.yml` — illumera Android Play Release
- `.github/workflows/desktop-release.yml` — Desktop and TV Release

### HereLiesAz/lamplight — `release-other`
- `.github/workflows/android-github-release.yml` — Lamplight Android GitHub Release
- `.github/workflows/android-play-release.yml` — Lamplight Android Play Release

### HereLiesAz/morphont — `release-other`
- `.github/workflows/android-github-release.yml` — Android GitHub Release
- `.github/workflows/android-play-release.yml` — Android Play Release
- `.github/workflows/desktop-release.yml` — Desktop Release

### HereLiesAz/morphont — `wasm-ci`
- `.github/workflows/ci.yml` — CI
- `.github/workflows/pages.yml` — Publish to GitHub Pages

### HereLiesAz/onwordly — `ci-validation`
- `.github/workflows/ci.yml` — CI
- `.github/workflows/experiment.yml` — Experiment 001

### HereLiesAz/sir-match-a-lot — `release-other`
- `.github/workflows/android-github-release.yml` — Android GitHub Release
- `.github/workflows/android-play-release.yml` — Android Play Release
- `.github/workflows/desktop-release.yml` — Desktop Release


## Manual review

- `HereLiesAz/aive:.github/workflows/orchestration-specialist-training.yml` — Orchestration Specialist Training
- `HereLiesAz/aive:.github/workflows/security-review.yml` — Security Review
- `HereLiesAz/hereliesaz.github.io:.github/workflows/publish_admin_staging.yml` — Publish Admin Staging
- `HereLiesAz/azphalt:.github/workflows/security-review.yml` — Security Review
- `HereLiesAz/Graffux:.github/workflows/stroke-data-kaggle.yml` — Stroke data → Kaggle
- `HereLiesAz/convey:.github/workflows/publish-packages.yml` — Publish to GitHub Packages
- `HereLiesAz/CaptureTheFlag:.github/workflows/ci.yml` — CI
- `HereLiesAz/onwordly:.github/workflows/kaggle-experiment.yml` — Kaggle Experiment 001

## Errors

- HereLiesAz/conveyance-expressive:.github/workflows/ci.yml: missing source file registry/1345202069/ci-899ce9c2.source.yml
- HereLiesAz/conveyance-liquid:.github/workflows/ci.yml: missing source file registry/1345203382/ci-899ce9c2.source.yml
- HereLiesAz/conveyance-bacterium:.github/workflows/ci.yml: missing source file registry/1345203982/ci-899ce9c2.source.yml
