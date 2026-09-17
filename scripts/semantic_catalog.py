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
        "source_hashes": {
            "41ccb8c30d393fdc42a44d3b208b179f948ebc44e1c316c4e78b76f627f3bb3c",
        },
    },
    ".github/workflows/android-dependency-update.yml": {
        "name": "Android Dependency Update",
        "canonical_hash": "05e2b3435ae6c44dfac330372257beb8ccd0b4046cd7fb66bff57fabefb799e3",
        "source_hashes": {
            "05e2b3435ae6c44dfac330372257beb8ccd0b4046cd7fb66bff57fabefb799e3",
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
