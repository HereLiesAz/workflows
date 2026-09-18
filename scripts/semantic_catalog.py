from __future__ import annotations

from typing import Final

# These are semantic decisions, not implementation identities. Hashes are only
# safety guards: a source must still be one of the reviewed implementations
# before the synchronizer binds it to the shared purpose-level workflow.
SEMANTIC_WORKFLOWS: Final[dict[str, dict[str, object]]] = {
    ".github/workflows/azp-model-release.yml": {
        "name": "AZP Model Release",
        "canonical_hash": "d97ccb161c6ef03fda005a7053d4de85c1cd9cf97785ccf7a8e777ca5ef31ee5",
        "generalized": True,
        "source_hashes": {
            "d97ccb161c6ef03fda005a7053d4de85c1cd9cf97785ccf7a8e777ca5ef31ee5",
            "c43f374050664d850b17bfd5ceb78a1911b3cdf1e306448609944c02949e32aa",
            "d8c762275c29a2b6fd557eca12c44756ec7235d4c7fb03a9a447eecc5838eaa0",
            "568a9897992715e3f68494df838280782f3802894d1443e8116515f59e7d9335",
            "2035037f33e3e03869b40dee3f370dc5ddc7624d7739a14387e75279d789464a",
            "68ae6a768bec59f03798cbe48aabe8f40fa6a766ac1b7f4de4d3fe263e6b239c",
            "a9972b81ec5bacc17dd1c0e940d33db72f01ffed2731912009de3c1162ef8225",
            "6a8a4056fd16575bc5467fe85cd817c210246759bb14c77410a6d24843cd056f",
            "dcb6b7518a06d3dc61e567155044371fd6bd8b31027e0b70fed1aff8c18afd4e",
            "3410ad7b1417abab4d9a83d2722e498b82804b1ac21e87bb2329ec645b0760b2",
            "ef7cbad07655eecfac60a227b0b2aaafc5176d188cd3f196e298aaa644d4022f",
            "6c427bb8947e75e2b24dffba12970f6b06109612995bfc29765745efe5e678b6",
            "df219e18f056f70c71d3f68c3a73a8ce5d8b3834525f018f7e663f1f7073ab8f",
            "14fb07a3c131ebc9bc352b5fe31e82b9d451fac8625b7c355261e7f066e481a2",
            "c53b3701ed073a143ff089ff92b0b3ecf4e6316ea04631734b18898fb0613255",
        },
    },
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
        "generalized": True,
        "source_hashes": {
            "c7e435bc33db1508560b4f5e700570d3f9544ce3d2efa16b4b7df2a60ee3c1f4",
            "9f62916fd29cb8ceed1a342fe12a5e7d3edeea9b81603064406163ed81453127",
            "09adb91f6846d345ebb261ae428ad9412bfbfac6fe1d1192a726b84546b46928",
            "f0b5d5091bb2d2372b65116ee9d154f0fe03ed641d3693436525ff618f47f22a",
            "e27bd12865d67d2b1c70163a463a38a043c90869fd8d319a4097d7b2412852ed",
            "bc33a453efa94395260c9b521a0fc01da92a27a8da0181d2c598770148ee6007",
            "f637fcde293eeaaa50671b2f6313751cd044a6419c37ebba3678dd702940d94a",
            "48cc88893221e4dbfa9bdede0cec35d7fcd6932f3d4d472cf496284e59d19c18",
            "441264e5b5c2542d4213fa4b25dc3c4eaf061a4ea8b2cd64ebe4dba0aed61d84",
            "d469abed7144cbed30feaf51455bdc0bc039b6bb9978968ff5a534d361e31828",
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
    "441264e5b5c2542d4213fa4b25dc3c4eaf061a4ea8b2cd64ebe4dba0aed61d84": {"signing": "pem-chain", "pem_legacy": True, "google_services": "raw", "build_command": "./gradlew bundleRelease --build-cache", "aab_glob": "app/build/outputs/bundle/release/*.aab", "version_mode": "git-count", "version_arg": "versionBuild", "inject_signing_args": True, "publish_on_push": False, "tracks_from_inputs": True, "publish_default": True, "persist_version": False, "ad_id_check": True, "mapping_file": "app/build/outputs/mapping/release/mapping.txt", "github_release_after_play": "manual", "release_version_scheme": "legacy-blame", "release_app_name": "LogKitty"},
    "d469abed7144cbed30feaf51455bdc0bc039b6bb9978968ff5a534d361e31828": {"signing": "pem-chain", "pem_legacy": True, "google_services": "none", "build_command": "./gradlew bundleRelease --build-cache", "aab_glob": "app/build/outputs/bundle/release/*.aab", "version_mode": "git-count", "version_arg": "versionBuild", "inject_signing_args": True, "publish_on_push": True, "tracks_from_csv_input": True, "publish_default": False, "persist_version": False, "test_command": "./gradlew testDebugUnitTest --build-cache", "mapping_file": "app/build/outputs/mapping/release/mapping.txt", "push_tracks": [{"track": "internal", "status": "completed"}, {"track": "alpha", "status": "completed"}], "github_release_after_play": "manual", "release_version_scheme": "legacy-blame"},
    "9f62916fd29cb8ceed1a342fe12a5e7d3edeea9b81603064406163ed81453127": {"signing": "pem-chain", "build_command": "./gradlew bundlePlay", "aab_glob": "app/build/outputs/bundle/play/*.aab", "version_mode": "git-count", "version_arg": "versionBuild", "inject_signing_args": True, "tracks_from_inputs": True, "publish_default": False, "persist_version": False},
    "09adb91f6846d345ebb261ae428ad9412bfbfac6fe1d1192a726b84546b46928": {"signing": "pem-chain", "google_services": "raw", "build_command": "./gradlew bundlePlayRelease", "aab_glob": "app/build/outputs/bundle/playRelease/*.aab", "inject_signing_args": True, "persist_version": False},
    "f0b5d5091bb2d2372b65116ee9d154f0fe03ed641d3693436525ff618f47f22a": {"signing": "pem-chain", "google_services": "raw", "build_command": "./gradlew bundleRelease", "aab_glob": "app/build/outputs/bundle/release/*.aab", "version_mode": "play-highest", "version_arg": "versionCodeOverride", "inject_signing_args": True, "persist_version": False, "tracks": [{"track": "internal", "status": "completed"}, {"track": "alpha", "status": "draft"}]},
    "e27bd12865d67d2b1c70163a463a38a043c90869fd8d319a4097d7b2412852ed": {"signing": "raw-jks", "build_command": "./gradlew bundlePlaystoreRelease", "aab_glob": "app/build/outputs/bundle/playstoreRelease/*.aab", "arcore_local_properties": True, "persist_version": True},
    "bc33a453efa94395260c9b521a0fc01da92a27a8da0181d2c598770148ee6007": {"signing": "raw-jks", "build_command": "./gradlew bundleRelease", "aab_glob": "app/build/outputs/bundle/release/*.aab", "persist_version": True},
    "f637fcde293eeaaa50671b2f6313751cd044a6419c37ebba3678dd702940d94a": {"signing": "raw-jks", "build_command": "./gradlew bundleRelease", "aab_glob": "app/build/outputs/bundle/release/*.aab", "arcore_local_properties": True, "persist_version": True},
    "48cc88893221e4dbfa9bdede0cec35d7fcd6932f3d4d472cf496284e59d19c18": {"signing": "pem-chain", "build_command": "./gradlew bundlePlayRelease", "aab_glob": "app/build/outputs/bundle/playRelease/*.aab", "version_mode": "git-count", "version_arg": "versionBuild", "inject_signing_args": True, "persist_version": False, "tracks": [{"track": "internal", "status": "completed"}, {"track": "alpha", "status": "completed"}, {"track": "beta", "status": "draft"}, {"track": "production", "status": "draft"}]},
    "d97ccb161c6ef03fda005a7053d4de85c1cd9cf97785ccf7a8e777ca5ef31ee5": {"asset": "style.onnx", "model_url": "https://huggingface.co/onnx-community/fast-neural-style-mosaic/resolve/main/mosaic.onnx"},
    "c43f374050664d850b17bfd5ceb78a1911b3cdf1e306448609944c02949e32aa": {"asset": "gtcrn_simple.onnx", "model_url": "https://huggingface.co/onnx-community/gtcrn/resolve/main/gtcrn_simple.onnx"},
    "d8c762275c29a2b6fd557eca12c44756ec7235d4c7fb03a9a447eecc5838eaa0": {"asset": "lama.onnx", "model_url": "https://huggingface.co/Carve/LaMa-ONNX/resolve/main/lama_fp32.onnx"},
    "568a9897992715e3f68494df838280782f3802894d1443e8116515f59e7d9335": {"asset": "midas.onnx", "model_url": "https://huggingface.co/julienkay/sentis-MiDaS/resolve/main/midas_v21_small_256.onnx"},
    "2035037f33e3e03869b40dee3f370dc5ddc7624d7739a14387e75279d789464a": {"asset": "mirnet.onnx", "model_url": "https://huggingface.co/onnx-community/mirnet/resolve/main/mirnet.onnx"},
    "68ae6a768bec59f03798cbe48aabe8f40fa6a766ac1b7f4de4d3fe263e6b239c": {"asset": "face-embed.onnx", "model_url": "https://huggingface.co/onnx-community/mobilefacenet/resolve/main/mobilefacenet.onnx"},
    "a9972b81ec5bacc17dd1c0e940d33db72f01ffed2731912009de3c1162ef8225": {"asset": "mobilenetv3.onnx", "model_url": "https://huggingface.co/onnx-community/mobilenetv3_small_100/resolve/main/onnx/model.onnx"},
    "6a8a4056fd16575bc5467fe85cd817c210246759bb14c77410a6d24843cd056f": {"asset": "moondream2.onnx", "model_url": "https://huggingface.co/onnx-community/moondream2/resolve/main/onnx/model.onnx"},
    "dcb6b7518a06d3dc61e567155044371fd6bd8b31027e0b70fed1aff8c18afd4e": {"asset": "tts.onnx", "model_url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx"},
    "3410ad7b1417abab4d9a83d2722e498b82804b1ac21e87bb2329ec645b0760b2": {"asset": "segmentation.onnx", "model_url": "https://huggingface.co/onnx-community/pyannote-segmentation-3.0/resolve/main/segmentation.onnx"},
    "ef7cbad07655eecfac60a227b0b2aaafc5176d188cd3f196e298aaa644d4022f": {"asset": "realesrgan.onnx", "model_url": "https://huggingface.co/Xenova/real-esrgan-x4/resolve/main/onnx/model.onnx"},
    "6c427bb8947e75e2b24dffba12970f6b06109612995bfc29765745efe5e678b6": {"asset": "version-RFB-320.onnx", "model_url": "https://huggingface.co/onnx-community/ultraface-version-RFB-320/resolve/main/version-RFB-320.onnx"},
    "df219e18f056f70c71d3f68c3a73a8ce5d8b3834525f018f7e663f1f7073ab8f": {"asset": "embedding.onnx", "model_url": "https://huggingface.co/onnx-community/wespeaker-voxceleb-resnet34-LM/resolve/main/embedding.onnx"},
    "14fb07a3c131ebc9bc352b5fe31e82b9d451fac8625b7c355261e7f066e481a2": {"asset": "whisper-base.onnx", "model_url": "https://huggingface.co/onnx-community/whisper-base/resolve/main/onnx/model.onnx"},
    "c53b3701ed073a143ff089ff92b0b3ecf4e6316ea04631734b18898fb0613255": {"asset": "yamnet.onnx", "model_url": "https://huggingface.co/onnx-community/yamnet/resolve/main/yamnet.onnx"},
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
    ("hereliesaz/guillotine", ".github/workflows/extensions.yml"): "stale workflow: the extensions/ tree was removed from Guillotine, so every run fails before npm can start",
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
