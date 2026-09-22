# Workflow purpose audit

This report groups active workflows by **what they accomplish**, not by filename, repository, or implementation hash.

- Active centralized workflows: **194**
- Live workflows audited: **340** (including 146 local and 0 blocked)
- Purpose groups: **58**
- Manual-review workflows: **0**
- Same-repository/same-purpose groups: **21**

## Purpose groups

| Purpose | Workflows | Repositories | Source variants | Effects |
| --- | ---: | ---: | ---: | --- |
| `pull-request-audit` | 59 | 59 | 1 | glee-audit |
| `android-build-and-github-release` | 47 | 35 | 32 | android-build, artifact-upload, github-release, huggingface-publish, tests |
| `github-pages-deploy` | 38 | 37 | 18 | pages-deploy |
| `azp-sign-release` | 27 | 27 | 2 | azp-sign, github-release |
| `pull-request-labeling` | 22 | 21 | 3 | labeling |
| `jules-task-dispatch` | 13 | 7 | 2 | jules-dispatch |
| `build-cache-clear` | 10 | 9 | 4 | android-build, artifact-upload, cache-clear, tests |
| `jules-issue-automation` | 8 | 8 | 8 | — |
| `jules-issue-triage` | 8 | 8 | 2 | — |
| `repository-backup` | 7 | 7 | 1 | artifact-upload, backup, tests |
| `android-publish-google-play` | 6 | 6 | 5 | android-build, artifact-upload, google-play, maven-publish, pages-deploy |
| `dependency-update` | 6 | 6 | 2 | dependency-update |
| `file-server-deploy` | 6 | 6 | 3 | file-server-deploy |
| `issue-summary` | 6 | 6 | 1 | issue-summary |
| `ci-validation` | 5 | 4 | 5 | artifact-upload, lint, tests |
| `code-security-scan` | 5 | 5 | 2 | codeql |
| `dependency-graph-submission` | 4 | 4 | 3 | — |
| `deployment-other` | 4 | 3 | 4 | — |
| `android-multichannel-release` | 3 | 3 | 3 | android-build, artifact-upload, github-release, google-play, tests |
| `contribution-guideline-review` | 3 | 3 | 2 | — |
| `gemini-issue-triage` | 3 | 3 | 3 | — |
| `gemini-task-dispatch` | 3 | 3 | 3 | — |
| `github-release` | 3 | 3 | 3 | github-release |
| `jules-agent` | 3 | 3 | 3 | jules-agent |
| `maven-publish` | 3 | 2 | 3 | android-build, artifact-upload, maven-publish |
| `artifact-build` | 2 | 2 | 2 | artifact-upload |
| `azp-model-release` | 2 | 2 | 2 | azp-model-release, github-release, huggingface-publish |
| `java-gradle-ci-and-dependency-submission` | 2 | 2 | 1 | — |
| `jules-branch-automation` | 2 | 2 | 2 | — |
| `wasm-ci` | 2 | 2 | 2 | android-build, artifact-upload, github-release, pages-deploy, wasm-build |
| `android-build` | 1 | 1 | 1 | android-build, artifact-upload |
| `android-ci` | 1 | 1 | 1 | — |
| `antigravity-issue-triage` | 1 | 1 | 1 | — |
| `antigravity-task-dispatch` | 1 | 1 | 1 | — |
| `app-catalog-bake` | 1 | 1 | 1 | — |
| `art-data-bootstrap` | 1 | 1 | 1 | — |
| `data-deduplication` | 1 | 1 | 1 | — |
| `data-enrichment` | 1 | 1 | 1 | — |
| `distributed-compute-ci` | 1 | 1 | 1 | — |
| `documentation-sync` | 1 | 1 | 1 | docs-sync |
| `huggingface-space-deploy` | 1 | 1 | 1 | artifact-upload, huggingface-space-deploy |
| `issue-reminder-automation` | 1 | 1 | 1 | — |
| `jules-branch-auto-merge` | 1 | 1 | 1 | jules-auto-merge |
| `jules-security-remediation` | 1 | 1 | 1 | — |
| `live-runtime-verification` | 1 | 1 | 1 | — |
| `model-artifact-inspection` | 1 | 1 | 1 | — |
| `multi-platform-app-release` | 1 | 1 | 1 | android-build, desktop-build, github-release, tests |
| `multi-target-app-release` | 1 | 1 | 1 | android-build, github-release, python-executable |
| `npm-publish` | 1 | 1 | 1 | npm-publish |
| `painting-removal` | 1 | 1 | 1 | file-server-deploy |
| `platform-parity-sync` | 1 | 1 | 1 | android-build, repository-visibility, tests |
| `prop-id-rendering` | 1 | 1 | 1 | — |
| `release-other` | 1 | 1 | 1 | — |
| `repository-visibility-policy` | 1 | 1 | 1 | repository-visibility |
| `static-analysis-sarif` | 1 | 1 | 1 | android-build, artifact-upload, sarif-upload |
| `theater-bake` | 1 | 1 | 1 | file-server-deploy |
| `unattached-visibility-migration` | 1 | 1 | 1 | android-build, repository-visibility |
| `vendor-artifact-build` | 1 | 1 | 1 | artifact-upload, vendor-artifact |

## Same repository, same purpose

### HereLiesAz/AzNavRail — `android-build-and-github-release`
- `.github/workflows/android-ci.yml` — Android CI
- `.github/workflows/android-release-apk.yml` — Compile and Release APK

### HereLiesAz/AzNavRail — `jules-task-dispatch`
- `.github/workflows/jules-dispatch.yml` — 🔀 Jules Dispatch
- `.github/workflows/jules-invoke.yml` — ▶️ Jules Invoke

### HereLiesAz/BluSnu — `android-build-and-github-release`
- `.github/workflows/build-release.yml` — On-Demand Release Build
- `.github/workflows/merged-build.yml` — Merged Build (Debug)

### HereLiesAz/CleanUnderwear — `android-build-and-github-release`
- `.github/workflows/android-ci.yml` — Android CI
- `.github/workflows/merged-build.yml` — PR Verification & Merge Release

### HereLiesAz/CueDetat — `android-build-and-github-release`
- `.github/workflows/android-ci.yml` — Android CI
- `.github/workflows/android_debug_apk_release.yml` — Merged Build & Release
- `.github/workflows/android_release.yml` — Android Release Build

### HereLiesAz/GraffitiXR — `android-build-and-github-release`
- `.github/workflows/android-ci.yml` — Android CI
- `.github/workflows/merged-build.yml` — Merged Build & Release
- `.github/workflows/release-apk.yml` — Compile and Release APK

### HereLiesAz/GraffitiXR — `jules-task-dispatch`
- `.github/workflows/jules-dispatch.yml` — 🔀 Jules Dispatch
- `.github/workflows/jules-invoke.yml` — ▶️ Jules Invoke

### HereLiesAz/LogKitty — `android-build-and-github-release`
- `.github/workflows/android-ci.yml` — Android CI
- `.github/workflows/android-release-apk.yml` — Compile and Release APK
- `.github/workflows/build-and-release.yml` — Merged Build & Release

### HereLiesAz/LogKitty — `jules-task-dispatch`
- `.github/workflows/jules-dispatch.yml` — 🔀 Jules Dispatch
- `.github/workflows/jules-invoke.yml` — ▶️ Jules Invoke

### HereLiesAz/NoLAWallet — `android-build-and-github-release`
- `.github/workflows/build-referral-apk.yml` — Build Referral APK
- `.github/workflows/build_and_release.yml` — Merged Build & Release

### HereLiesAz/NoLAWallet — `deployment-other`
- `.github/workflows/deploy-functions.yml` — Deploy Functions
- `.github/workflows/deploy-worker.yml` — Deploy Worker

### HereLiesAz/aive — `build-cache-clear`
- `.github/workflows/android-ci.yml` — Android CI
- `.github/workflows/clear_cache.yml` — Clear Gradle Cache

### HereLiesAz/aive — `ci-validation`
- `.github/workflows/bitcos-engine.yml` — BITCOS Engine
- `.github/workflows/node-creature-engine.yml` — Node Creature Engine

### HereLiesAz/aive — `jules-task-dispatch`
- `.github/workflows/jules-dispatch.yml` — 🔀 Jules Dispatch
- `.github/workflows/jules-invoke.yml` — ▶️ Jules Invoke

### HereLiesAz/aive — `maven-publish`
- `.github/workflows/play-store-assets.yml` — Play Store Assets
- `.github/workflows/terrarium-visual-proof.yml` — Terrarium Visual Proof

### HereLiesAz/convey — `github-pages-deploy`
- `.github/workflows/jekyll-gh-pages.yml` — Deploy Jekyll with GitHub Pages dependencies preinstalled
- `.github/workflows/static.yml` — Deploy static content to Pages

### HereLiesAz/lamplight — `android-build-and-github-release`
- `.github/workflows/android-ci.yml` — Android CI
- `.github/workflows/android-release-apk.yml` — Compile and Release APK

### HereLiesAz/lamplight — `jules-task-dispatch`
- `.github/workflows/jules-dispatch.yml` — 🔀 Jules Dispatch
- `.github/workflows/jules-invoke.yml` — ▶️ Jules Invoke

### HereLiesAz/lamplight — `pull-request-labeling`
- `.github/workflows/jules.yml` — Auto-assign Jules
- `.github/workflows/label.yml` — Labeler

### HereLiesAz/sir-match-a-lot — `android-build-and-github-release`
- `.github/workflows/android-ci.yml` — Android CI
- `.github/workflows/android-release-apk.yml` — Compile and Release APK

### HereLiesAz/sir-match-a-lot — `jules-task-dispatch`
- `.github/workflows/jules-dispatch.yml` — 🔀 Jules Dispatch
- `.github/workflows/jules-invoke.yml` — ▶️ Jules Invoke


## Manual review

None.

## Errors

None.
