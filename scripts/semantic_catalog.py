from __future__ import annotations

from typing import Final

# These are semantic decisions, not implementation identities. Hashes are only
# safety guards: a source must still be one of the reviewed implementations
# before the synchronizer binds it to the shared purpose-level workflow.
SEMANTIC_WORKFLOWS: Final[dict[str, dict[str, object]]] = {
    ".github/workflows/azp-sign-release.yml": {
        "name": "AZP Sign Release",
        "canonical_hash": "025b006118f31a5a39a1c6bae19866537e9f34e2c4c143c9b840d2bff2728bb2",
        "source_hashes": {
            "39ea6636c4df27ad72afc857325be6c5850c014589e7542ab529bda5e644b565",
            "025b006118f31a5a39a1c6bae19866537e9f34e2c4c143c9b840d2bff2728bb2",
        },
    },
    ".github/workflows/issue-summary.yml": {
        "name": "Issue Summary",
        "canonical_hash": "9158d4587eeca12602514ad7da12f02c600029539ba1567bf63b405d972b65ff",
        "source_hashes": {
            "9158d4587eeca12602514ad7da12f02c600029539ba1567bf63b405d972b65ff",
            "796ddbe048f79d73cbc353f7f6c7a2f9730c92e285c4c69c66e7177834d617f3",
            "c6534bad6ca4dbda9ce365f12a5894a92729d6be5e2e0bb4944b192812aa11e2",
            "d457c0809e0b9d1cd9a70044eaab8f8e0aa11197ba25a0a9c97aab620f155afa",
        },
    },
    ".github/workflows/android-play-release.yml": {
        "name": "Android Play Release",
        "canonical_hash": "c7e435bc33db1508560b4f5e700570d3f9544ce3d2efa16b4b7df2a60ee3c1f4",
        "source_hashes": {
            "c7e435bc33db1508560b4f5e700570d3f9544ce3d2efa16b4b7df2a60ee3c1f4",
        },
    },
    ".github/workflows/android-github-release.yml": {
        "name": "Android GitHub Release",
        "canonical_hash": "41ccb8c30d393fdc42a44d3b208b179f948ebc44e1c316c4e78b76f627f3bb3c",
        "generalized": True,
        "source_hashes": {
            "41ccb8c30d393fdc42a44d3b208b179f948ebc44e1c316c4e78b76f627f3bb3c",
            "09588a228454cd17abb67313111597bf62edf69ac9286a225bed91913b7ffb35",
            "aeb8bc10311d29a49ceb316a824021c2ef6f17847d459bea89ace81f5f96c1df",
            "ccc871738c362676351da341dfbf003900ea0578380395818594fb2ed6852579",
            "66b945d96e416473a7bf667158784b6b6175b8afbcc922bc073d17a22387fa24",
        },
    },
    ".github/workflows/android-dependency-update.yml": {
        "name": "Android Dependency Update",
        "canonical_hash": "05e2b3435ae6c44dfac330372257beb8ccd0b4046cd7fb66bff57fabefb799e3",
        "generalized": True,
        "source_hashes": {
            "05e2b3435ae6c44dfac330372257beb8ccd0b4046cd7fb66bff57fabefb799e3",
            "ba191c6a57ff4008bd50e08df3f5b931095de753fddb7a669f3d66445c2032a0",
            "8e5f1bac9cf34a4b89d0d49d1a137c46a18212420d820f3103e5020b6628a0ff",
            "320489791ba36be59acabf9ac3b0267bfaab93e7e68e4b40700a5016a90bc1ef",
            "218d0b95a059b7c0e559590cf074b99f3fa1cbc6896cdab316133bc39d110704",
            "389bc8192c50e3f60e771d6f8f254f25ddc639bb41cd33e86109cda171b3ef25",
        },
    },
    ".github/workflows/codeql-scan.yml": {
        "name": "CodeQL Scan",
        "canonical_hash": "b1daefb6a9ccf116f965927078d197b7fd77c4e35093258e05c5a0c5c0660417",
        "generalized": True,
        "source_hashes": {
            "a524ceeb0890b7c6ec820412ee6568fde448310a8fdea8cf80179553e7d281f9",
            "b1daefb6a9ccf116f965927078d197b7fd77c4e35093258e05c5a0c5c0660417",
            "e16a42da22d3d1d1fcc2027f8904587003b09a058f1ace5135d131a4eac2b288",
            "7e105503a4469dc6efca0ac829f5bb9a6ab2ea6a9e18d674b842fc83340510b6",
            "1c85cedbe13e2334c6ec9d887ee06ee6fc81827311b8ed50278de225b90f17ba",
            "9e3b56da6fe8e52662f6e9fff25d1bfb9d4285673008a6b13cc4af7ccbed2e59",
            "888afc38304e373a2efcb201edf4be0eb263cb606ec4498f377e7972ba976fac",
        },
    },
    ".github/workflows/website-sftp-deploy.yml": {
        "name": "Website SFTP Deploy",
        "canonical_hash": "b0ef23a564e122b032f710d57a50a0d08fa49b142386df869c99f960f4e5be8b",
        "source_hashes": {
            "b0ef23a564e122b032f710d57a50a0d08fa49b142386df869c99f960f4e5be8b",
        },
    },
    ".github/workflows/jules-auto-assign.yml": {
        "name": "Jules Auto-Assign",
        "canonical_hash": "fda0a6aea5ac252f58143d670f738385e7a3579048921db468cca6b4c673ea2f",
        "source_hashes": {
            "fda0a6aea5ac252f58143d670f738385e7a3579048921db468cca6b4c673ea2f",
        },
    },
    ".github/workflows/android-debug-ci.yml": {
        "name": "Android Debug CI",
        "canonical_hash": "6f25a5f112d324c4bb19236302c860917f1e65e984e919e778afdd634a97336d",
        "source_hashes": {
            "6f25a5f112d324c4bb19236302c860917f1e65e984e919e778afdd634a97336d",
        },
    },
}

PURPOSE_PROFILES: Final[dict[str, dict[str, object]]] = {
    "09588a228454cd17abb67313111597bf62edf69ac9286a225bed91913b7ffb35": {"signing": "pem-chain", "chain_secret": "CHAIN", "java_version": "17", "inject_signing_args": True, "test_command": "./gradlew testDebugUnitTest", "app_name": "MadeMeDance"},
    "aeb8bc10311d29a49ceb316a824021c2ef6f17847d459bea89ace81f5f96c1df": {"signing": "pem-chain", "chain_secret": "KEYSTORE_CHAIN", "java_version": "17", "inject_signing_args": True, "arcore_local_properties": True},
    "66b945d96e416473a7bf667158784b6b6175b8afbcc922bc073d17a22387fa24": {"signing": "raw-jks", "java_version": "21", "arcore_local_properties": True, "app_name": "GraffitiXR"},
    "ba191c6a57ff4008bd50e08df3f5b931095de753fddb7a669f3d66445c2032a0": {"lib_dir": "app/libs", "opencv": True, "opencv_layout": "sdk-root", "glm_layout": "archive-root"},
    "8e5f1bac9cf34a4b89d0d49d1a137c46a18212420d820f3103e5020b6628a0ff": {"lib_dir": "libs", "opencv": True, "opencv_layout": "sdk-contents", "glm_layout": "headers"},
    "320489791ba36be59acabf9ac3b0267bfaab93e7e68e4b40700a5016a90bc1ef": {"lib_dir": "libs", "opencv": True, "opencv_layout": "sdk-contents", "glm_layout": "headers"},
    "e16a42da22d3d1d1fcc2027f8904587003b09a058f1ace5135d131a4eac2b288": {"languages": ["actions", "javascript-typescript"]},
    "7e105503a4469dc6efca0ac829f5bb9a6ab2ea6a9e18d674b842fc83340510b6": {"java_version": "19", "build_command": "./gradlew clean assembleDebug --no-build-cache"},
    "1c85cedbe13e2334c6ec9d887ee06ee6fc81827311b8ed50278de225b90f17ba": {"java_version": "19", "build_command": "./gradlew clean assembleGithubDebug --no-build-cache"},
    "888afc38304e373a2efcb201edf4be0eb263cb606ec4498f377e7972ba976fac": {"languages": ["java-kotlin"], "build_mode": "autobuild"},
}

GENERAL_CURATED_NAMES: Final[dict[str, str]] = {
    ".github/workflows/jules-dispatch.yml": "Jules Dispatch",
    ".github/workflows/jules-glee.yml": "Glee Audit",
    ".github/workflows/context-backup.yml": "Context Backup",
    ".github/workflows/clear-cache.yml": "Clear Gradle Cache",
}

# A reviewed source can use an existing curated implementation instead of a
# repository-specific executor.
CURATED_SOURCE_OVERRIDES: Final[dict[str, str]] = {
    "511f95a3edaf45d4d2f50b83a2e345eda49ef43d4ad4e9194f60af7cf7591d9a": ".github/workflows/clear-cache.yml",
}

# These were inspected individually. They are not alternate implementations of
# useful automation; they are disabled, malformed, placeholders, or one-shot
# temporary scaffolding. Registry sources remain as history after removal.
OBSOLETE_WORKFLOWS: Final[dict[tuple[str, str], str]] = {
    ("hereliesaz/ideaz", ".github/workflows/antigravity-branch-manager.yml"): "disabled no-op: the job is hard-disabled pending a valid Gemini key",
    ("hereliesaz/ideaz", ".github/workflows/antigravity-issue-handler.yml"): "disabled no-op: the job is hard-disabled pending a valid Gemini key",
    ("hereliesaz/hereliesaz.github.io", ".github/workflows/dependency-submission-disable.yml"): "dummy workflow whose only trigger is a branch literally named disabled",
    ("hereliesaz/cleanunderwear", ".github/workflows/dependabot.yml"): "malformed Dependabot configuration placed in Actions instead of .github/dependabot.yml",
    ("hereliesaz/illumera", ".github/workflows/temp-dispatch-release.yml"): "temporary one-shot release dispatcher",
    ("hereliesaz/illumera", ".github/workflows/temp-recent-review-fixes.yml"): "temporary one-shot review cleanup that removes itself after use",
    ("hereliesaz/spybomb", ".github/workflows/blank.yml"): "unchanged GitHub hello-world starter workflow",
    ("hereliesaz/cleanunderwear", ".github/workflows/jules-agent.yml"): "placeholder that only echoes that Jules is not configured",
    ("hereliesaz/cleanunderwear", ".github/workflows/jules-auto-merge.yml"): "placeholder that only echoes that Jules is not configured",
    ("hereliesaz/guillotine", ".github/workflows/jules-agent.yml"): "placeholder that only echoes that Jules is not configured",
    ("hereliesaz/guillotine", ".github/workflows/jules-auto-merge.yml"): "placeholder that only echoes that Jules is not configured",
    ("hereliesaz/click", ".github/workflows/release.yml"): "starter release template that publishes a debug APK and says it should be a release build",
    ("hereliesaz/fluttertest", ".github/workflows/release.yml"): "starter release template that publishes a debug APK and says it should be a release build",
}

TEMPORARY_CONTROLLER_WORKFLOWS: Final[set[str]] = {
    ".github/workflows/repair-guillotine-release.yml",
    ".github/workflows/repair-release-centralization.yml",
    ".github/workflows/emergency-concurrency-fix.yml",
    ".github/workflows/migrate-repository-workflows.yml",
    ".github/workflows/migrate-semantic-library.yml",
    ".github/workflows/migrate-semantic-purpose.yml",
}


def semantic_override_for_source(source_sha256: str) -> str | None:
    for path, rule in SEMANTIC_WORKFLOWS.items():
        if source_sha256 in rule["source_hashes"]:
            return path
    return None


def curated_override_for_source(source_sha256: str) -> str | None:
    return CURATED_SOURCE_OVERRIDES.get(source_sha256)


def reviewed_override_for_source(source_sha256: str) -> str | None:
    return curated_override_for_source(source_sha256) or semantic_override_for_source(source_sha256)


def workflow_display_name(path: str) -> str:
    rule = SEMANTIC_WORKFLOWS.get(path)
    if rule:
        return str(rule["name"])
    return GENERAL_CURATED_NAMES[path]


def canonical_hash(path: str) -> str:
    return str(SEMANTIC_WORKFLOWS[path]["canonical_hash"])


def uses_target_repository_name(path: str) -> bool:
    return path in SEMANTIC_WORKFLOWS or path in GENERAL_CURATED_NAMES


def purpose_profile_for_source(source_sha256: str) -> dict[str, object] | None:
    profile = PURPOSE_PROFILES.get(source_sha256)
    return dict(profile) if profile else None


def uses_purpose_profile(path: str) -> bool:
    rule = SEMANTIC_WORKFLOWS.get(path)
    return bool(rule and rule.get("generalized"))
