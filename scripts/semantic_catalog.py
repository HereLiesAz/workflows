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
            "825e6e5a5cbc7d80f2854e239557599c354131b24dee94d3c14b806f640ce98b",
            "a95687c1a4f8af0ad53e5d420d557fc7237dd2f97d70d63201ac4cdff6edb6c6",
            "b97bd64bdcefbb35d0e33cd76c966052f13342e26a4e5fcdf1650a95cb994b0e",
            "60ac0b25cf88bcff28f3b5c31d1d9545e5a6ba10d9b80d1b7d35e540329b350e",
            # HereLiesAz/hereliesaz.github.io:.github/workflows/android-release-aab.yml
            # is intentionally NOT generalized. That repository has a legitimate
            # bespoke release/deployment pipeline and keeps its dedicated executor.
            # HereLiesAz/QaRd:.github/workflows/play-release.yml — see PURPOSE_PROFILES
            # for the pem-chain signing / bundlePlayRelease / tracks-from-inputs profile.
            "dee6f7b8f329c64093b03787ecab565a92a6eab18a8a14c5d5d49d6815e045d0",
            # HereLiesAz/CueDetat:.github/workflows/play_publish.yml — see
            # PURPOSE_PROFILES for its pem-chain / git-commit-count-versioned profile.
            "c99c3eed02d6deb557eaba891c904d3fcdabde1c27a518dee8c7e8e422b92b98",
        },
    },
    ".github/workflows/android-github-release.yml": {
        "name": "Android GitHub Release",
        "canonical_hash": "41ccb8c30d393fdc42a44d3b208b179f948ebc44e1c316c4e78b76f627f3bb3c",
        "generalized": True,
        "source_hashes": {
            "41ccb8c30d393fdc42a44d3b208b179f948ebc44e1c316c4e78b76f627f3bb3c",
            "4574d6f09eca2407de0f4303494e984c4bba5b3edcc035a5903824ce0ef58315",
            "09588a228454cd17abb67313111597bf62edf69ac9286a225bed91913b7ffb35",
            "aeb8bc10311d29a49ceb316a824021c2ef6f17847d459bea89ace81f5f96c1df",
            "ccc871738c362676351da341dfbf003900ea0578380395818594fb2ed6852579",
            "66b945d96e416473a7bf667158784b6b6175b8afbcc922bc073d17a22387fa24",
            "f74f4d32dcd258fd1e13fccce422b3900ce7eb50cfbd20e31a5dc9848f179348",
            "67ce04785215b3aacb24ff9d7703d6e87bfed3aacdf4ab3bd780540c47bb18cb",
            "0734d0c56fd8fc16abd5aee34a30f1170e6b42abafae354aff05eee485e54704",
            "e6dc8ef902c25e4c1b5dfcc338526e617afb9e104fb1cadbaac740ab7b259d3e",
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
        "generalized": True,
        "source_hashes": {
            "b0ef23a564e122b032f710d57a50a0d08fa49b142386df869c99f960f4e5be8b",
            "961e61bc138f682e09cad9b4318e0b44ca82719e751bda9b3594acc1b7937c27",
            "31afe4d12a10ef30e8475e959100df371e0384d5af5dab8b41feb42fa1758291",
            "aab5ef3d85c2ac59d48c828207dbb273c22eacfc9d84e3f28faa96e44eb78a05",
            "8b42bbc29b2f1b8ab416a72cd6b2ed04c37811d4ec358ea24c5a4640773474fc",
        },
    },
    ".github/workflows/jules-scheduled-triage.yml": {
        "name": "Jules Scheduled Issue Triage",
        "canonical_hash": "c5795302751261681062afb2384c0a30807517ee87a9246fcc46f874d0b0f7f1",
        "source_hashes": {
            "c5795302751261681062afb2384c0a30807517ee87a9246fcc46f874d0b0f7f1",
            "417422c330b5c2c0b37ef35eb18ec3c5424671bffa96288d868e69202fef8327",
            "fa0ee2978160f94d866bd050b5767781c50ea823bba21275e02e08d066ef650c",
        },
    },
    ".github/workflows/jules-auto-assign.yml": {
        "name": "Jules Auto-Assign",
        "canonical_hash": "fda0a6aea5ac252f58143d670f738385e7a3579048921db468cca6b4c673ea2f",
        "source_hashes": {
            "fda0a6aea5ac252f58143d670f738385e7a3579048921db468cca6b4c673ea2f",
        },
    },
    ".github/workflows/ci-validation.yml": {
        "name": "CI Validation",
        "canonical_hash": "5fe909668facbf1604c5b7b3b84ba42ecff633f5ed2a52a4ba54180d8a0053d0",
        "generalized": True,
        "source_hashes": {
            "5fe909668facbf1604c5b7b3b84ba42ecff633f5ed2a52a4ba54180d8a0053d0",
            "52ca995d48319a2c683fa64cd248e8cdab22514d19dd7df731d47adc7db6e3cd",
            "1e1a288d8b11d79b01237145826c5d0dd03a1398dc40685fefbe5ab1e9ec66e7",
            "76ed7e227ffb3569d5c7ff6dc196e029a9be297c6e18413c0dce509f48d0a1ac",
            "10548e68e51337b353f1bb359e619b9e4e541e09028b3d67bec2ab33f3f65065",
            "b39fb843f7d476e46f871a0d9893e572be0c10158021ef707640b7d3f2baa721",
            "0b7b065e8862e6c031ece662ec8e4a6b3f38ce4e1eb665d2abb38dc0bd3453ff",
            "41fe12a37af090d9bbb2d801dc044c858f4620f9215678277c71d9a83a5fd22d",
            "e0453104ae87efbcbaff88ffbf48bb4f13960d6793b9b0961e26930e9738b5c3",
            "efd2a9e25587d0b98bfac920bbece460f9391789dddc7b2f49d20a318b2a1826",
            "802e95696b2de19f1ee773ff2bbd52f361bcddf92eb5320c2279abda51c0de46",
            "9f8a0b11a0bcc7c92f361efebd7d443dfdcb9e92516378b9d689eee0a10222bd",
            "ecd3d0b9d749eee197622cfcd6eec22c54bf46270553ec35253297ed9d4d8674",
            "ca84d43ee0762c0d02fb98325047a1b5aee2be2c832c16972af7775c265e465a",
            "9f8da3bca25bfd3dc0b79ccbf911454b10d940e597e3bfeed73995cdc8bd8551",
            "3b152efa3c299bbb83309c04d844b1292a3346a844ba1d3193a6beaa7a5c0699",
            "f8094e4c2c08c047dc17b2ccb7766dab14eeb775d66238b2c1f93c06fe995cce",
            "8d0bee7aa3ab78d04396737b8f3fdde27eb3f4164f501979a811cac647b569b7",
            "6ab641050248a526163bd43e627e6bf32c80a618fa1b0bfb4dbf3d24e1e8c697",
            "57f245d8d8504ca1ef5146ccc3533aecc5d08c45ab5aa9416b3b619ba3c385a9",
            "60c8cb4ab8364f08369e2fae3b9a8322825d0a596405966da26a7889e98501a8",
            "b662b29aa007235e906bac5ae76e05b1f0573f4599f76125dfbeda4acfd89864",
        },
    },
    ".github/workflows/multi-platform-app-release.yml": {
        "name": "Multi-Platform App Release",
        "canonical_hash": "2150463fc5eba564d0d1a6069b40aef1f36333d8a30d0f2cd0ec8938000a802b",
        "generalized": True,
        "source_hashes": {
            "2150463fc5eba564d0d1a6069b40aef1f36333d8a30d0f2cd0ec8938000a802b",
            "91d73e21d7385b0155e9193b8d718f1e9d3ecb5fce92401f0fc06d9bd41aadb8",
            "d8c9826d6991f1fd657934457f0a73d3e018ccbc802e0186c4b40a501d621337",
        },
    },
    ".github/workflows/artifact-github-release.yml": {
        "name": "Artifact GitHub Release",
        "canonical_hash": "57c23f2489e4e00b40c10a98d12610d6f95b36b66ee7a242236be21f3058a114",
        "generalized": True,
        "source_hashes": {
            "57c23f2489e4e00b40c10a98d12610d6f95b36b66ee7a242236be21f3058a114",
            "3ee242e7f4214889ba314e70ef51aec8553ec25bfe5965b9bfb7a89ea08e4a9d",
        },
    },
    ".github/workflows/maven-package-publish.yml": {
        "name": "Maven Package Publish",
        "canonical_hash": "968458e29535134b77927dbc8ec6c653ad070e0b6e9cd30f7ac9063544eb14e9",
        "generalized": True,
        "source_hashes": {
            "968458e29535134b77927dbc8ec6c653ad070e0b6e9cd30f7ac9063544eb14e9",
            "03e2f1e420d12d9cc0a7cdbd64594ac76c6f5025b064f43083b57b0714cf087a",
        },
    },
    ".github/workflows/node-package-publish.yml": {
        "name": "Node Package Publish",
        "canonical_hash": "70516095978d4884e183505d261e2485f1b35c7b8835e69d13a726da077ca285",
        "generalized": True,
        "source_hashes": {
            "70516095978d4884e183505d261e2485f1b35c7b8835e69d13a726da077ca285",
            "202a3be9eb627b6679ca3723e6f47d154b9c5b0703c517cf79ec7f6f5ff6c89a",
        },
    },
    ".github/workflows/desktop-package.yml": {
        "name": "Desktop Package",
        "canonical_hash": "ecaa174d3910d20491133343eb12f16cb2979108025efeced85d28a9b6e7c9b1",
        "generalized": True,
        "source_hashes": {
            "ecaa174d3910d20491133343eb12f16cb2979108025efeced85d28a9b6e7c9b1",
            "acc1dc959c04a0f3c4c42f8768b3aa469dfd5a449d0a02584cb2a98641f8d14b",
            "c6251f2b6b5fe71bea894085048df9338151bc914505f23dbd5f8f37c4721190",
            "f085283d13372c3d20dfeb8e47b3fe2541f7c912f15c30547257aa22c11be7c2",
        },
    },
    # Content-package sibling of azp-model-release. The repository builds many
    # .azp packages from sources it already owns, so there is no upstream model
    # to fetch and no single release asset; the only per-repository value is the
    # glob of built packages, which lives in PURPOSE_PROFILES as packages_glob.
    ".github/workflows/azp-package-release.yml": {
        "name": "AZP Package Release",
        "canonical_hash": "daa7c2c9b42632686d27a6ac2571e5ca36223fceb5a2a8e23d58f3fc2cb76a57",
        "generalized": True,
        "source_hashes": {
            # HereLiesAz/aive:.github/workflows/azp-package-release.yml — packs the
            # Azphalt Store workflow/role packages under docs/azphalt-packages/
            # into build/azp/*.azp and publishes them all to the release tag.
            "daa7c2c9b42632686d27a6ac2571e5ca36223fceb5a2a8e23d58f3fc2cb76a57",
        },
    },
}

PURPOSE_PROFILES: Final[dict[str, dict[str, object]]] = {
    "2150463fc5eba564d0d1a6069b40aef1f36333d8a30d0f2cd0ec8938000a802b": {"serialize":True,"prepare_node_version":"22","prepare_command":"gh auth setup-git\ngit config user.name \"github-actions[bot]\"\ngit config user.email \"41898282+github-actions[bot]@users.noreply.github.com\"\nversion=\"$(node tools/version.mjs bump)\"\ntest -n \"$version\" || { echo \"::error::version bump produced no version\" >&2; exit 1; }\ngit add version.properties\ngit diff --cached --quiet && { echo \"::error::version.properties did not change\" >&2; exit 1; }\ngit commit -m \"chore(version): $version [skip ci]\"\npushed=\"\"\nfor attempt in 1 2 3 4 5; do if git push origin \"HEAD:$TARGET_REF_NAME\"; then pushed=yes; break; fi; git pull --rebase origin \"$TARGET_REF_NAME\"; sleep $((attempt * 3)); done\ntest -n \"$pushed\" || { echo \"::error::could not push version commit\" >&2; exit 1; }\ngit tag \"v$version\"\ngit push origin \"v$version\"\necho \"version=$version\" >> \"$GITHUB_OUTPUT\"\necho \"tag=v$version\" >> \"$GITHUB_OUTPUT\"","matrix":{"include":[{"os":"ubuntu-latest","java_version":"17","java_distribution":"corretto","node_version":"22","gradle":True,"artifact_name":"android-apk","prepare":"node .github/scripts/write-google-services.mjs","build":"cd apps/storefront-cmp && AZPHALT_VERSION_FROZEN=1 ./gradlew assembleDebug --no-daemon --stacktrace && cd ../.. && node .github/scripts/name-debug-apk.mjs \"$RELEASE_VERSION\" \"azphalt-store-$RELEASE_VERSION-debug.apk\"","artifact_path":"azphalt-store-*.apk"},{"os":"ubuntu-latest","java_version":"17","java_distribution":"corretto","gradle":True,"artifact_name":"desktop-linux","build":"cd apps/storefront-cmp && AZPHALT_VERSION_FROZEN=1 ./gradlew packageReleaseDistributionForCurrentOS","artifact_path":"apps/storefront-cmp/build/compose/binaries/main-release/"},{"os":"macos-latest","java_version":"17","java_distribution":"corretto","gradle":True,"artifact_name":"desktop-macos","build":"cd apps/storefront-cmp && AZPHALT_VERSION_FROZEN=1 ./gradlew packageReleaseDistributionForCurrentOS","artifact_path":"apps/storefront-cmp/build/compose/binaries/main-release/"},{"os":"windows-latest","java_version":"17","java_distribution":"corretto","gradle":True,"shell":"pwsh","artifact_name":"desktop-windows","build":"$env:AZPHALT_VERSION_FROZEN='1'; Set-Location apps/storefront-cmp; ./gradlew packageReleaseDistributionForCurrentOS","artifact_path":"apps/storefront-cmp/build/compose/binaries/main-release/"}]},"allow_partial":True,"release_when":"always","tag_mode":"prepare-output","force_tag":False,"prerelease":True,"title_template":"Azphalt $VERSION","body_template":"Every artifact built from commit $BUILD_SHA at version $VERSION. Android is the debug-signed storefront APK; desktop assets are the native Windows, macOS, and Linux installers.","rolling_tag":"latest","rolling_title":"Azphalt (Latest)"},
    "91d73e21d7385b0155e9193b8d718f1e9d3ecb5fce92401f0fc06d9bd41aadb8": {"serialize":True,"prepare_java_version":"21","prepare_gradle":True,"prepare_command":"if [ -n \"${GOOGLE_SERVICES:-}\" ]; then printf \"%s\" \"$GOOGLE_SERVICES\" > app/google-services.json; fi\ntest -n \"${KEYSTORE_RAW:-}\" || { echo \"::error::KEYSTORE_RAW is required\" >&2; exit 1; }\nprintf \"%s\" \"$KEYSTORE_RAW\" | base64 --decode > app/keystore.jks\ntest -s app/keystore.jks || { echo \"::error::decoded keystore is empty\" >&2; exit 1; }\nchmod +x gradlew\nKEYSTORE_FILE=\"$PWD/app/keystore.jks\" KEYSTORE_PASSWORD=\"$KEYSTORE_PASSWORD\" KEY_ALIAS=\"$KEY_ALIAS\" KEY_PASSWORD=\"$KEY_PASSWORD\" ./gradlew assembleRelease\nMAJOR=$(grep \"^versionMajor=\" version.properties | cut -d= -f2 | tr -d \"\\r \")\nMINOR=$(grep \"^versionMinor=\" version.properties | cut -d= -f2 | tr -d \"\\r \")\nPATCH=$(grep \"^versionPatch=\" version.properties | cut -d= -f2 | tr -d \"\\r \")\nBUILD_NUMBER=$(grep \"^versionBuild=\" version.properties | cut -d= -f2 | tr -d \"\\r \")\nversion=\"${MAJOR}.${MINOR}.${PATCH}.${BUILD_NUMBER}\"\ntag=\"latest-release-v${MAJOR}.${MINOR}\"\napk=$(find app/build/outputs/apk/release -name \"*.apk\" | head -1)\ntest -n \"$apk\" && test -s \"$apk\" || { echo \"::error::release APK missing\" >&2; exit 1; }\nmkdir -p release-artifacts\ncp \"$apk\" \"release-artifacts/Graffux-${version}-release.apk\"\necho \"version=$version\" >> \"$GITHUB_OUTPUT\"\necho \"tag=$tag\" >> \"$GITHUB_OUTPUT\"","prepare_artifact_name":"android-apk","prepare_artifact_path":"release-artifacts/*.apk","matrix":{"include":[{"os":"ubuntu-latest","java_version":"21","gradle":True,"artifact_name":"desktop-linux","prepare":"sudo apt-get update && sudo apt-get install -y fakeroot rpm","build":"chmod +x gradlew && ./gradlew :desktop:packageDeb :desktop:packageRpm","artifact_path":"desktop/build/compose/binaries/main/deb/*.deb\ndesktop/build/compose/binaries/main/rpm/*.rpm"},{"os":"windows-latest","java_version":"21","gradle":True,"shell":"pwsh","artifact_name":"desktop-windows","prepare":"if (-not (Get-Command candle.exe -ErrorAction SilentlyContinue)) { choco install wixtoolset --version=3.14.1 -y --no-progress; $wixBin = Get-ChildItem \"C:\\Program Files (x86)\\WiX Toolset*\\bin\" -Directory -ErrorAction SilentlyContinue | Select-Object -First 1; if (-not $wixBin) { throw \"WiX install failed\" }; Add-Content -Path $env:GITHUB_PATH -Value $wixBin.FullName }","build":"./gradlew.bat :desktop:packageMsi","artifact_path":"desktop/build/compose/binaries/main/msi/*.msi"}]},"allow_partial":False,"release_when":"always","tag_mode":"prepare-output","force_tag":True,"prerelease":False,"title_template":"Graffux $VERSION","body_template":"Release build from commit $BUILD_SHA — Android APK plus Linux (.deb/.rpm) and Windows (.msi) desktop builds."},
    "d8c9826d6991f1fd657934457f0a73d3e018ccbc802e0186c4b40a501d621337": {"serialize":False,"matrix":{"include":[{"os":"ubuntu-latest","java_version":"17","gradle":True,"artifact_name":"app-debug","build":"chmod +x gradlew && ./gradlew assembleDebug","artifact_path":"app/build/outputs/apk/debug/app-debug.apk"},{"os":"ubuntu-latest","python_version":"3.9","artifact_name":"pwnagotchi-raspi","prepare":"pip install pyinstaller websockets","build":"cd pwnagotchi_raspi && pyinstaller --onefile --name pwnagotchi_raspi main.py","artifact_path":"pwnagotchi_raspi/dist/pwnagotchi_raspi"}]},"allow_partial":False,"release_when":"tag","tag_mode":"target-ref","force_tag":False,"prerelease":True,"generate_notes":True,"title_template":"pwnagotchiOnAndroid $TAG","body_template":"Android debug APK and Raspberry Pi executable built from commit $BUILD_SHA."},
    "a95687c1a4f8af0ad53e5d420d557fc7237dd2f97d70d63201ac4cdff6edb6c6": {"signing":"raw-jks","signing_env_style":"release-store","java_version":"21","setup_android":True,"android_packages":"platform-tools","shared_cache_path":"stremio-aars","shared_cache_key":"stremio-media-Linux-95781597c8e3c30d6232e77bdadecc38ad35aa17-v2","shared_cache_trusted_save":True,"extra_checkout_repository":"Stremio/media","extra_checkout_ref":"95781597c8e3c30d6232e77bdadecc38ad35aa17","extra_checkout_path":"vendor/stremio-media","google_services":"none","package_name":"com.hereliesaz.illumera","pre_build_command":"missing=0\nfor aar in lib-exoplayer-release.aar lib-decoder-av1-release.aar lib-decoder-ffmpeg-release.aar lib-decoder-iamf-release.aar lib-decoder-mpegh-release.aar; do test -s \"stremio-aars/$aar\" || missing=1; done\nif [ \"$missing\" -ne 0 ]; then chmod +x ci/build-stremio-media.sh; ./ci/build-stremio-media.sh vendor/stremio-media stremio-aars; fi\nfor aar in lib-exoplayer-release.aar lib-decoder-av1-release.aar lib-decoder-ffmpeg-release.aar lib-decoder-iamf-release.aar lib-decoder-mpegh-release.aar; do test -s \"stremio-aars/$aar\" || { echo \"Missing Stremio playback artifact: $aar\" >&2; exit 1; }; cp \"stremio-aars/$aar\" \"playbackcore/libs/$aar\"; done\nBASE=$(grep -oP 'versionName\\s*=.*?:\\s*\"\\K[^\"]+' app/build.gradle.kts | head -1)\ntest -n \"$BASE\" || { echo \"Could not resolve base versionName\" >&2; exit 1; }\nMAJOR_MINOR=$(printf '%s\\n' \"$BASE\" | grep -oP '^\\d+\\.\\d+')\ntest -n \"$MAJOR_MINOR\" || { echo \"Invalid base versionName: $BASE\" >&2; exit 1; }\nRELEASE_VERSION_NAME=\"${MAJOR_MINOR}.${TARGET_RUN_NUMBER}\"\nRELEASE_VERSION_CODE=\"$((TARGET_RUN_NUMBER * 100 + VERSION_BUILD))\"\necho \"RELEASE_VERSION_NAME=$RELEASE_VERSION_NAME\" >> \"$GITHUB_ENV\"\necho \"RELEASE_VERSION_CODE=$RELEASE_VERSION_CODE\" >> \"$GITHUB_ENV\"","build_command":"./gradlew :app:testDebugUnitTest :app:lintRelease :app:assembleRelease :app:bundlePlay --no-daemon --stacktrace -PversionNameOverride=\"$RELEASE_VERSION_NAME\" -PversionCodeOverride=\"$RELEASE_VERSION_CODE\"","aab_glob":"app/build/outputs/bundle/play/*.aab","apk_glob":"app/build/outputs/apk/release/*.apk","publish_on_push":True,"publish_default":True,"persist_version":False,"tracks":[{"track":"internal","status":"completed"},{"track":"alpha","status":"draft","preserve_existing":True,"name":"illumera $RELEASE_VERSION_NAME"}],"github_built_release_always":True,"github_built_release_tag_env":"RELEASE_VERSION_NAME","github_built_release_include_aab":False,"github_built_release_checksum":True,"github_built_release_changes":True,"release_app_name":"illumera"},
    "b97bd64bdcefbb35d0e33cd76c966052f13342e26a4e5fcdf1650a95cb994b0e": {"signing":"raw-jks","signing_env_style":"release-store","java_version":"21","setup_android":True,"android_packages":"platform-tools","google_services":"none","package_name":"com.hereliesaz.illumera","build_command":"./gradlew :app:testDebugUnitTest :app:lintRelease :app:assembleRelease :app:bundlePlay --no-daemon --stacktrace -PversionNameOverride=\"$VERSION\" -PversionCodeOverride=\"$ANDROID_VERSION_CODE\"","aab_glob":"app/build/outputs/bundle/play/*.aab","apk_glob":"app/build/outputs/apk/release/*.apk","publish_on_push":True,"publish_default":True,"persist_version":False,"tracks":[{"track":"internal","status":"completed"},{"track":"alpha","status":"draft","preserve_existing":True,"name":"illumera $VERSION"}],"github_built_release_always":True,"github_built_release_tag_env":"VERSION","github_built_release_include_aab":False,"github_built_release_checksum":True,"github_built_release_changes":True,"release_app_name":"illumera"},
    "60ac0b25cf88bcff28f3b5c31d1d9545e5a6ba10d9b80d1b7d35e540329b350e": {"signing":"raw-jks","signing_env_style":"release-store","java_version":"21","setup_android":True,"android_packages":"platform-tools","google_services":"none","package_name":"com.hereliesaz.illumera","build_command":"./gradlew :app:testDebugUnitTest :app:lintRelease :app:assembleRelease :app:bundlePlay --no-daemon --stacktrace -PversionNameOverride=\"$VERSION\" -PversionCodeOverride=\"$ANDROID_VERSION_CODE\"","aab_glob":"app/build/outputs/bundle/play/*.aab","apk_glob":"app/build/outputs/apk/release/*.apk","publish_on_push":True,"publish_default":True,"persist_version":False,"tracks":[{"track":"internal","status":"completed"},{"track":"alpha","status":"draft","preserve_existing":True,"name":"illumera $VERSION"}],"github_built_release_always":True,"github_built_release_tag_env":"VERSION","github_built_release_include_aab":False,"github_built_release_checksum":True,"github_built_release_changes":True,"release_app_name":"illumera"},
    "57c23f2489e4e00b40c10a98d12610d6f95b36b66ee7a242236be21f3058a114": {"tool": "maven", "java_version": "17", "tag_mode": "target-ref", "build_command": "mvn package", "files": ["jbox2d-library/target/jbox2d-library-*.jar", "jbox2d-testbed/target/jbox2d-testbed-*-jar-with-dependencies.jar"], "generate_notes": False},
    "3ee242e7f4214889ba314e70ef51aec8553ec25bfe5965b9bfb7a89ea08e4a9d": {"tool": "python", "python_version": "3.11", "tag_mode": "computed", "version_command": "python3 tools/next_version.py", "tag_prefix": "v", "version_env": "AZRIENOCH_VERSION", "install_command": "pip install -r requirements.txt", "build_command": "python3 -m tools.designspace_build", "files": ["fonts/variable/Azrienoch-VF.ttf", "fonts/variable/Azrienoch-VF.woff2"], "release_name_prefix": "Azrienoch", "title_include_sha": True, "generate_notes": True},
    "825e6e5a5cbc7d80f2854e239557599c354131b24dee94d3c14b806f640ce98b": {"signing": "pem-chain", "java_version": "21", "google_services": "none", "build_command": "./gradlew :androidApp:assembleRelease :androidApp:bundleRelease --no-daemon", "aab_glob": "androidApp/build/outputs/bundle/release/*.aab", "apk_glob": "androidApp/build/outputs/apk/release/*.apk", "package_name": "com.hereliesaz.morphont", "signing_env_prefix": "MORPHONT", "publish_on_push": False, "publish_default": False, "tracks_from_inputs": True, "persist_version": False, "github_built_release_on_tag": True, "release_app_name": "Morphont"},
    "6f25a5f112d324c4bb19236302c860917f1e65e984e919e778afdd634a97336d": {"kind": "gradle", "java_version": "17", "command": "./gradlew assembleDebug", "report_path": "app/build/outputs/apk/debug/app-debug.apk", "report_when": "always", "retention_days": 7},
    "1606a824a8bd29eb3c6dbd9ca74f88692ee0abd248e910d9a1ee69acb279766c": {"kind": "flutter", "java_version": "17", "flutter_version": "3.16.0", "command": "flutter pub get\nflutter build apk --debug\nVERSION=$(grep '^version:' pubspec.yaml | head -n 1 | sed 's/^version:[[:space:]]*//' | tr -d '\\r ')\nif [ -z \"$VERSION\" ]; then VERSION=1.0.0; fi\nmv build/app/outputs/flutter-apk/app-debug.apk \"build/app/outputs/flutter-apk/IDEaz-$VERSION-debug.apk\"", "report_path": "build/app/outputs/flutter-apk/IDEaz-*-debug.apk", "report_when": "always", "retention_days": 7},
    "968458e29535134b77927dbc8ec6c653ad070e0b6e9cd30f7ac9063544eb14e9": {"tool": "maven", "java_version": "17", "publish_command": "mvn --batch-mode deploy"},
    "03e2f1e420d12d9cc0a7cdbd64594ac76c6f5025b064f43083b57b0714cf087a": {"tool": "gradle", "java_version": "21", "jitpack": True, "build_command": "./gradlew assemble", "publish_command": "./gradlew publish"},
    "57f245d8d8504ca1ef5146ccc3533aecc5d08c45ab5aa9416b3b619ba3c385a9": {
        "kind": "node",
        "node_version": "22",
        "java_version": "17",
        "version_frozen": "1",
        "command": "corepack enable\npnpm install --frozen-lockfile\npnpm build\npnpm test\npnpm fixtures\ngit add -N conformance/fixtures\ngit diff --exit-code -- conformance/fixtures\nnode .github/scripts/write-google-services.mjs\n( cd apps/storefront-cmp && chmod +x gradlew && ./gradlew wasmJsBrowserDistribution --no-daemon --stacktrace && ./gradlew assembleDebug --no-daemon --stacktrace && ./gradlew desktopTest --no-daemon --stacktrace && ./gradlew :azp:test --no-daemon --stacktrace )",
    },
    "b662b29aa007235e906bac5ae76e05b1f0573f4599f76125dfbeda4acfd89864": {
        "kind": "gradle",
        "java_version": "21",
        "timeout_minutes": 45,
        "command": "./gradlew desktopTest --stacktrace\n./gradlew compileKotlinJs compileKotlinWasmJs assembleAndroidMain --stacktrace",
        "report_path": "build/reports/tests/",
        "report_when": "always",
        "retention_days": 7,
    },
    "60c8cb4ab8364f08369e2fae3b9a8322825d0a596405966da26a7889e98501a8": {
        "kind": "gradle",
        "java_version": "21",
        "setup_android": True,
        "android_packages": "platforms;android-37.0 platforms;android-37.1 build-tools;37.0.0",
        "command": "./gradlew detekt",
        "snyk": True,
    },
    "70516095978d4884e183505d261e2485f1b35c7b8835e69d13a726da077ca285": {"mode": "simple", "node_version": "22", "registry_url": "https://npm.pkg.github.com", "scope": "@HereLiesAz", "token": "github", "working_directory": "aznavrail-react", "prepare_command": "corepack enable && yarn install", "build_command": "yarn build", "publish_command": "npm publish"},
    "202a3be9eb627b6679ca3723e6f47d154b9c5b0703c517cf79ec7f6f5ff6c89a": {"mode": "changesets", "node_version": "22", "registry_url": "https://registry.npmjs.org", "scope": "", "token": "npm", "working_directory": ".", "prepare_command": "corepack enable && npm install -g npm@10 && pnpm install --frozen-lockfile", "version_command": "pnpm run version", "publish_command": "pnpm run release", "version_branch": "changeset-release/main", "version_pr_title": "chore: version packages", "fallback_publish_script": "scripts/publish-staged.sh", "fallback_promote_script": "scripts/promote-latest.sh", "fallback_promote": True, "fallback_stage_size": "5", "fallback_stage_cooldown": "120", "fallback_call_cooldown": "30", "fallback_staging_tag": "staging"},
    "ecaa174d3910d20491133343eb12f16cb2979108025efeced85d28a9b6e7c9b1": {"java_version":"21","use_gradle_setup":False,"version_mode":"fixed","fixed_version":"1.0.0","cancel_in_progress":True,"release_mode":"none","matrix":{"include":[{"os":"ubuntu-latest","artifact":"hashkitty-linux-installer","path":"installer_output/*.deb","prepare":"sudo apt-get update && sudo apt-get install -y fakeroot","build":"cd hashkitty-java && chmod +x gradlew && ./gradlew clean installDist; cd ..; printf 'main-class=hashkitty.java.server.ServerApp\\n' > server.properties; \"$JAVA_HOME/bin/jpackage\" --name hashkitty --input hashkitty-java/app/build/install/app/lib --main-jar app.jar --main-class hashkitty.java.App --app-version \"$DESKTOP_VERSION\" --dest installer_output --type deb --add-launcher server=server.properties --java-options '-Djava.library.path=$APPDIR' --verbose"},{"os":"windows-latest","artifact":"hashkitty-windows-installer","path":"installer_output/*.exe","prepare":"","build":"cd hashkitty-java && ./gradlew clean installDist; cd ..; printf 'main-class=hashkitty.java.server.ServerApp\\n' > server.properties; \"$JAVA_HOME/bin/jpackage\" --name hashkitty --input hashkitty-java/app/build/install/app/lib --main-jar app.jar --main-class hashkitty.java.App --app-version \"$DESKTOP_VERSION\" --dest installer_output --type exe --win-dir-chooser --win-menu --win-shortcut --add-launcher server=server.properties --verbose"}]}},
    "acc1dc959c04a0f3c4c42f8768b3aa469dfd5a449d0a02584cb2a98641f8d14b": {"java_version":"21","use_gradle_setup":True,"version_mode":"none","cancel_in_progress":True,"release_mode":"none","matrix":{"include":[{"os":"ubuntu-latest","artifact":"desktop-linux-deb","path":"desktop/build/compose/binaries/main/deb/*.deb","prepare":"","build":"chmod +x gradlew && ./gradlew :desktop:packageDeb --build-cache --stacktrace"},{"os":"macos-latest","artifact":"desktop-macos-dmg","path":"desktop/build/compose/binaries/main/dmg/*.dmg","prepare":"","build":"chmod +x gradlew && ./gradlew :desktop:packageDmg --build-cache --stacktrace"},{"os":"windows-latest","artifact":"desktop-windows-msi","path":"desktop/build/compose/binaries/main/msi/*.msi","prepare":"","build":"./gradlew :desktop:packageMsi --build-cache --stacktrace"}]}},
    "c6251f2b6b5fe71bea894085048df9338151bc914505f23dbd5f8f37c4721190": {"java_version":"21","use_gradle_setup":True,"version_mode":"none","cancel_in_progress":False,"release_mode":"guillotine","release_title":"","release_body":"Guillotine desktop installers. Unsigned builds: on macOS use Open from the context menu; on Windows use More info → Run anyway if SmartScreen blocks the installer; on Linux install the downloaded .deb with apt.","matrix":{"include":[{"os":"ubuntu-latest","artifact":"guillotine-desktop-linux-deb","path":"desktop/build/compose/binaries/main/deb/*.deb","prepare":"","build":"chmod +x gradlew && ./gradlew :desktop:packageDeb --build-cache --stacktrace"},{"os":"macos-latest","artifact":"guillotine-desktop-macos-dmg","path":"desktop/build/compose/binaries/main/dmg/*.dmg","prepare":"","build":"chmod +x gradlew && ./gradlew :desktop:packageDmg --build-cache --stacktrace"},{"os":"windows-latest","artifact":"guillotine-desktop-windows-msi","path":"desktop/build/compose/binaries/main/msi/*.msi","prepare":"","build":"./gradlew :desktop:packageMsi --build-cache --stacktrace"}]}},
    "f085283d13372c3d20dfeb8e47b3fe2541f7c912f15c30547257aa22c11be7c2": {"java_version":"21","use_gradle_setup":True,"version_mode":"mcpserved","cancel_in_progress":True,"release_mode":"mcpserved","release_title":"","release_body":"Native desktop installers for Windows, macOS, and Linux.","matrix":{"include":[{"os":"ubuntu-latest","artifact":"mcpserved-desktop-linux","path":"dist/*","prepare":"sudo apt-get update && sudo apt-get install -y fakeroot binutils rpm","build":"chmod +x ./gradlew || true; ./gradlew :desktop:packageDistributionForCurrentOS -PdesktopPackageVersion=\"$DESKTOP_VERSION\" --stacktrace; mkdir -p dist; find desktop/build/compose/binaries/main -type f \\( -name '*.dmg' -o -name '*.msi' -o -name '*.exe' -o -name '*.deb' -o -name '*.rpm' \\) -exec cp {} dist/ \\;; ls -la dist"},{"os":"macos-latest","artifact":"mcpserved-desktop-macos","path":"dist/*","prepare":"","build":"chmod +x ./gradlew || true; ./gradlew :desktop:packageDistributionForCurrentOS -PdesktopPackageVersion=\"$DESKTOP_VERSION\" --stacktrace; mkdir -p dist; find desktop/build/compose/binaries/main -type f \\( -name '*.dmg' -o -name '*.msi' -o -name '*.exe' -o -name '*.deb' -o -name '*.rpm' \\) -exec cp {} dist/ \\;; ls -la dist"},{"os":"windows-latest","artifact":"mcpserved-desktop-windows","path":"dist/*","prepare":"","build":"chmod +x ./gradlew || true; ./gradlew :desktop:packageDistributionForCurrentOS -PdesktopPackageVersion=\"$DESKTOP_VERSION\" --stacktrace; mkdir -p dist; find desktop/build/compose/binaries/main -type f \\( -name '*.dmg' -o -name '*.msi' -o -name '*.exe' -o -name '*.deb' -o -name '*.rpm' \\) -exec cp {} dist/ \\;; ls -la dist"}]}},
    "e6dc8ef902c25e4c1b5dfcc338526e617afb9e104fb1cadbaac740ab7b259d3e": {"signing": "project", "java_version": "17", "google_services": "none", "build_command": "./gradlew assembleDebug", "artifact_glob": "app/build/outputs/apk/debug/*.apk", "persist_version": False, "version_mode": "major-minor-run-count", "asset_name_mode": "preserve", "move_tag": False, "prerelease": True, "release_title_style": "app-tag", "release_notes_mode": "changelog", "app_name": "ReUp"},
    "e9283d745ed6350a22feee09c1d3c1e59f63c1a284fb889d28e735671eb865b5": {"signing": "pem-chain", "java_version": "21", "google_services": "none", "build_command": "./gradlew clean assembleRelease -PversionBuild=$RUN_NUMBER -PversionName=1.3.0.$RUN_NUMBER", "artifact_glob": "app/build/outputs/apk/release/*.apk", "persist_version": False, "version_mode": "run-number-base", "base_version": "1.3.0", "fixed_tag": "v1.3-debug", "asset_name_mode": "app-v-version", "move_tag": True, "prerelease": True, "release_title": "1.3 Debug Builds", "wrapper_validation": True, "keystore_output": "app/release.keystore", "gradle_properties": ["org.gradle.jvmargs=-Xmx3072m", "android.useAndroidX=true"], "app_name": "Cue-Detat"},
    "67ce04785215b3aacb24ff9d7703d6e87bfed3aacdf4ab3bd780540c47bb18cb": {"signing": "project", "java_version": "21", "google_services": "none", "build_command": "./gradlew assembleRelease", "artifact_glob": "app/build/outputs/apk/release/*.apk", "persist_version": False, "version_mode": "source-tag", "asset_name_mode": "preserve", "move_tag": False, "prerelease": False, "release_title_style": "tag"},
    "f74f4d32dcd258fd1e13fccce422b3900ce7eb50cfbd20e31a5dc9848f179348": {"signing": "pem-chain", "chain_secret": "KEYSTORE_CHAIN", "java_version": "17", "inject_signing_args": True, "google_services": "raw", "build_command": "./gradlew assembleGithubRelease", "artifact_glob": "app/build/outputs/apk/github/release/*.apk", "mapping_file": "app/build/outputs/mapping/githubRelease/mapping.txt", "persist_version": True, "release_title_style": "major-minor-version", "app_name": "Guillotine"},
    "b0ef23a564e122b032f710d57a50a0d08fa49b142386df869c99f960f4e5be8b": {"build_mode": "jekyll", "local_dir": "./_site/", "remote_dir": "/app", "ssl_verify_off": True},
    "961e61bc138f682e09cad9b4318e0b44ca82719e751bda9b3594acc1b7937c27": {"build_mode": "node", "local_dir": "./webpage/dist/", "remote_dir": "/qard", "ssl_verify_off": True},
    "31afe4d12a10ef30e8475e959100df371e0384d5af5dab8b41feb42fa1758291": {"build_mode": "none", "local_dir": "./docs/", "remote_dir": "/guillotine", "ssl_verify_off": True},
    "aab5ef3d85c2ac59d48c828207dbb273c22eacfc9d84e3f28faa96e44eb78a05": {"build_mode": "none", "local_dir": "./docs/", "remote_dir": "/app", "ssl_verify_off": False},
    "8b42bbc29b2f1b8ab416a72cd6b2ed04c37811d4ec358ea24c5a4640773474fc": {"build_mode": "jekyll", "local_dir": "./_site/", "remote_dir": "/graffitixr", "ssl_verify_off": True},
    "441264e5b5c2542d4213fa4b25dc3c4eaf061a4ea8b2cd64ebe4dba0aed61d84": {"signing": "pem-chain", "pem_legacy": True, "google_services": "raw", "build_command": "./gradlew bundleRelease --build-cache", "aab_glob": "app/build/outputs/bundle/release/*.aab", "version_mode": "git-count", "version_arg": "versionBuild", "inject_signing_args": True, "publish_on_push": False, "tracks_from_inputs": True, "publish_default": True, "persist_version": False, "ad_id_check": True, "mapping_file": "app/build/outputs/mapping/release/mapping.txt", "github_release_after_play": "manual", "release_version_scheme": "legacy-blame", "release_app_name": "LogKitty"},
    "d469abed7144cbed30feaf51455bdc0bc039b6bb9978968ff5a534d361e31828": {"signing": "pem-chain", "pem_legacy": True, "google_services": "none", "build_command": "./gradlew bundleRelease --build-cache", "aab_glob": "app/build/outputs/bundle/release/*.aab", "version_mode": "git-count", "version_arg": "versionBuild", "inject_signing_args": True, "publish_on_push": True, "tracks_from_csv_input": True, "publish_default": False, "persist_version": False, "test_command": "./gradlew testDebugUnitTest --build-cache", "mapping_file": "app/build/outputs/mapping/release/mapping.txt", "push_tracks": [{"track": "internal", "status": "completed"}, {"track": "alpha", "status": "completed"}], "github_release_after_play": "manual", "release_version_scheme": "legacy-blame"},
    "9f62916fd29cb8ceed1a342fe12a5e7d3edeea9b81603064406163ed81453127": {"signing": "pem-chain", "build_command": "./gradlew bundlePlay", "aab_glob": "app/build/outputs/bundle/play/*.aab", "version_mode": "git-count", "version_arg": "versionBuild", "inject_signing_args": True, "tracks_from_inputs": True, "publish_default": False, "persist_version": False},
    "09adb91f6846d345ebb261ae428ad9412bfbfac6fe1d1192a726b84546b46928": {"signing": "pem-chain", "google_services": "raw", "build_command": "./gradlew bundlePlayRelease", "aab_glob": "app/build/outputs/bundle/playRelease/*.aab", "inject_signing_args": True, "persist_version": False, "live_rollout_draft_fallback": True, "package_name": "com.hereliesaz.guillotine", "play_version_floor": True, "pre_build_command": "test -n \"${PLAY_HIGHEST_VERSION_CODE:-}\" && sed -i -E \"s/^versionBuild=.*/versionBuild=${PLAY_HIGHEST_VERSION_CODE}/\" version.properties && grep -qx \"versionBuild=${PLAY_HIGHEST_VERSION_CODE}\" version.properties"},
    "f0b5d5091bb2d2372b65116ee9d154f0fe03ed641d3693436525ff618f47f22a": {"signing": "pem-chain", "google_services": "raw", "build_command": "./gradlew bundleRelease", "aab_glob": "app/build/outputs/bundle/release/*.aab", "version_mode": "play-highest", "version_arg": "versionCodeOverride", "inject_signing_args": True, "persist_version": False, "tracks": [{"track": "internal", "status": "completed"}, {"track": "alpha", "status": "draft"}]},
    "e27bd12865d67d2b1c70163a463a38a043c90869fd8d319a4097d7b2412852ed": {"signing": "raw-jks", "build_command": "./gradlew bundlePlaystoreRelease", "aab_glob": "app/build/outputs/bundle/playstoreRelease/*.aab", "arcore_local_properties": True, "persist_version": True},
    "bc33a453efa94395260c9b521a0fc01da92a27a8da0181d2c598770148ee6007": {"signing": "raw-jks", "build_command": "./gradlew bundleRelease", "aab_glob": "app/build/outputs/bundle/release/*.aab", "persist_version": True},
    "f637fcde293eeaaa50671b2f6313751cd044a6419c37ebba3678dd702940d94a": {"signing": "raw-jks", "build_command": "./gradlew bundleRelease", "aab_glob": "app/build/outputs/bundle/release/*.aab", "arcore_local_properties": True, "persist_version": True},
    "c99c3eed02d6deb557eaba891c904d3fcdabde1c27a518dee8c7e8e422b92b98": {"signing": "pem-chain", "build_command": "./gradlew bundleRelease", "aab_glob": "app/build/outputs/bundle/release/*.aab", "version_mode": "git-count", "version_arg": "versionBuild", "inject_signing_args": True, "persist_version": False, "tracks": [{"track": "internal", "status": "completed"}, {"track": "alpha", "status": "completed"}, {"track": "beta", "status": "draft"}, {"track": "production", "status": "draft"}]},
    "dee6f7b8f329c64093b03787ecab565a92a6eab18a8a14c5d5d49d6815e045d0": {"signing": "pem-chain", "java_version": "17", "build_command": "./gradlew bundlePlayRelease --build-cache", "aab_glob": "app/build/outputs/bundle/playRelease/*.aab", "inject_signing_args": True, "google_services": "raw", "tracks_from_inputs": True, "publish_default": False},
    # AZP Package Release — HereLiesAz/aive. No model asset or upstream URL:
    # `npm run build` writes every package to build/azp/ and all of them ship.
    "daa7c2c9b42632686d27a6ac2571e5ca36223fceb5a2a8e23d58f3fc2cb76a57": {"packages_glob": "build/azp/*.azp"},
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
    "4574d6f09eca2407de0f4303494e984c4bba5b3edcc035a5903824ce0ef58315": {"signing": "raw-jks", "java_version": "17", "inject_signing_args": True, "google_services": "none", "test_command": "./gradlew testDebugUnitTest --build-cache --no-daemon --stacktrace", "build_command": "./gradlew assembleRelease -PreleaseVersionName=1.0.0.$RUN_NUMBER -PreleaseVersionCode=$RUN_NUMBER --build-cache --no-daemon --stacktrace", "artifact_glob": "app/build/outputs/apk/release/*.apk", "persist_version": False, "version_mode": "run-number-base", "base_version": "1.0.0", "asset_name_mode": "app-v-version", "move_tag": False, "prerelease": False, "release_title_style": "app-tag", "wrapper_validation": False, "keystore_output": "app/keystore.jks", "app_name": "HereLiesAz-Admin"},
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
    "5fe909668facbf1604c5b7b3b84ba42ecff633f5ed2a52a4ba54180d8a0053d0": {
        "kind": "python",
        "os": ["ubuntu-latest"],
        "python_versions": ["3.10", "3.11", "3.12"],
        "install_command": "python -m pip install --upgrade pip\npip install -r requirements.txt\npip install -e \".[dev]\"",
        "command": "pytest -q",
    },
    "1e1a288d8b11d79b01237145826c5d0dd03a1398dc40685fefbe5ab1e9ec66e7": {
        "kind": "python",
        "os": ["ubuntu-latest"],
        "python_versions": ["3.9", "3.10", "3.11"],
        "install_command": "python -m pip install --upgrade pip\npython -m pip install flake8 pytest\nif [ -f requirements.txt ]; then pip install -r requirements.txt; fi\nif [ -f linux_app/requirements.txt ]; then pip install -r linux_app/requirements.txt; fi\nif [ -f pwnagotchi_raspi/requirements.txt ]; then pip install -r pwnagotchi_raspi/requirements.txt; fi",
        "command": "flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics\nflake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics\npytest",
    },
    "76ed7e227ffb3569d5c7ff6dc196e029a9be297c6e18413c0dce509f48d0a1ac": {
        "kind": "python",
        "os": ["ubuntu-latest", "macos-latest"],
        "python_versions": ["3.10.0", "3.11.0"],
        "install_command": "pip install --upgrade pip\npip install wheel\npip install -r requirements/dev.txt",
        "command": "flake8 . --count --show-source --statistics\nflake8 . --count --exit-zero --max-line-length=127 --statistics\npytest\nmypy --pretty theHarvester/*/*.py\nmypy --pretty theHarvester/*/*/*.py\npython theHarvester.py -d apple.com -b anubis\npython theHarvester.py -d yale.edu -b baidu\npython theHarvester.py -d yale.edu -b bing\npython theHarvester.py -d yale.edu -b certspotter\npython theHarvester.py -d hcl.com -b crtsh\npython theHarvester.py -d yale.edu -b dnsdumpster\npython theHarvester.py -d yale.edu -b duckduckgo\npython theHarvester.py -d yale.edu -b hackertarget\npython theHarvester.py -d yale.edu -b intelx\npython theHarvester.py -d yale.edu -b otx\npython theHarvester.py -d yale.edu -b qwant\npython theHarvester.py -d yale.edu -b rapiddns\npython theHarvester.py -d yale.edu -b sublist3r\npython theHarvester.py -d yale.edu -b threatcrowd\npython theHarvester.py -d yale.edu -b threatminer\npython theHarvester.py -d yale.edu -b urlscan\npython theHarvester.py -d yale.edu -b yahoo\npython theHarvester.py -d yale.edu -c",
    },
    "10548e68e51337b353f1bb359e619b9e4e541e09028b3d67bec2ab33f3f65065": {
        "kind": "node",
        "package_manager": "npm",
        "node_version": "22",
        "command": "npm ci\nnpm run typecheck\nnpm test\nnpm run build",
    },
    "b39fb843f7d476e46f871a0d9893e572be0c10158021ef707640b7d3f2baa721": {
        "kind": "node",
        "package_manager": "pnpm",
        "package_manager_version": "10.33.0",
        "node_version": "22",
        "database_url": "postgresql://pricepilot:pricepilot@localhost:5432/pricepilot?schema=public",
        "command": "pnpm install --frozen-lockfile\npnpm --filter @sail/db db:deploy\npnpm lint\npnpm typecheck\npnpm test\npnpm build\npnpm --filter @sail/web exec playwright install --with-deps chromium\npnpm --filter @sail/web e2e",
        "report_path": "apps/web/playwright-report/",
        "report_when": "failure",
        "retention_days": 7,
    },
    "0b7b065e8862e6c031ece662ec8e4a6b3f38ce4e1eb665d2abb38dc0bd3453ff": {
        "kind": "node",
        "package_manager": "npm",
        "node_version": "22",
        "java_version": "17",
        "command": "npm install -g firebase-tools@13\nnpm ci\nfirebase setup:emulators:firestore\nfirebase emulators:start --only firestore,storage --project barbacker-rules-test > emulator.log 2>&1 &\nemulator_pid=$!\ncleanup() { kill \"$emulator_pid\" 2>/dev/null || true; echo '--- emulator.log tail ---'; tail -200 emulator.log || true; }\ntrap cleanup EXIT\nready=false\nfor i in $(seq 1 60); do\n  if (echo > /dev/tcp/127.0.0.1/8080) 2>/dev/null && (echo > /dev/tcp/127.0.0.1/9199) 2>/dev/null; then ready=true; break; fi\n  sleep 1\ndone\nif [ \"$ready\" != true ]; then echo 'emulators did not come up'; tail -200 emulator.log; exit 1; fi\nnpx vitest --run --config vitest.rules.config.ts\n( cd functions && npm ci && npm run build && npm test )",
    },
    "52ca995d48319a2c683fa64cd248e8cdab22514d19dd7df731d47adc7db6e3cd": {"kind": "gradle", "java_version": "17", "validate_wrapper": False, "command": "./gradlew testDebugUnitTest --build-cache --no-daemon --stacktrace\n./gradlew assembleDebug --build-cache --no-daemon --stacktrace", "report_path": "app/build/reports/tests/\napp/build/outputs/apk/debug/*.apk", "report_when": "always", "retention_days": 7},
    "41fe12a37af090d9bbb2d801dc044c858f4620f9215678277c71d9a83a5fd22d": {
        "kind": "gradle",
        "java_version": "21",
        "validate_wrapper": True,
        "command": "./gradlew build",
    },
    "e0453104ae87efbcbaff88ffbf48bb4f13960d6793b9b0961e26930e9738b5c3": {
        "kind": "gradle",
        "java_version": "21",
        "command": "./gradlew :composeApp:detekt :shared:detektMetadataMain :shared:detektAndroidMain -PskipAutoIncrementVersion",
    },
    "efd2a9e25587d0b98bfac920bbece460f9391789dddc7b2f49d20a318b2a1826": {
        "kind": "gradle",
        "java_version": "21",
        "validate_wrapper": True,
        "command": "./gradlew -Pcuedetat.coreOnly=true allTests --stacktrace",
        "report_path": "core/*/build/reports/tests/\ncore/*/build/test-results/",
        "report_when": "always",
        "retention_days": 14,
    },
    "802e95696b2de19f1ee773ff2bbd52f361bcddf92eb5320c2279abda51c0de46": {
        "kind": "gradle",
        "java_version": "21",
        "validate_wrapper": True,
        "setup_android": True,
        "android_packages": "platforms;android-37.0 platforms;android-37.1 build-tools;37.0.0",
        "command": "./gradlew build --stacktrace",
        "report_path": "**/build/reports/tests/",
        "report_when": "failure",
        "retention_days": 7,
    },
    "9f8a0b11a0bcc7c92f361efebd7d443dfdcb9e92516378b9d689eee0a10222bd": {
        "kind": "gradle",
        "java_version": "21",
        "extra_checkout_repository": "HereLiesAz/Conveyance",
        "extra_checkout_ref": "b3e13674df9dfbcc0b35f800b57d78a305d07b03",
        "extra_checkout_path": "vendor/Conveyance",
        "command": "./gradlew desktopTest compileKotlinDesktop compileKotlinJs compileKotlinWasmJs compileAndroidMain",
    },
    "ecd3d0b9d749eee197622cfcd6eec22c54bf46270553ec35253297ed9d4d8674": {
        "kind": "gradle",
        "java_version": "17",
        "working_directory": "cmp",
        "command": "./gradlew :shared:desktopTest --stacktrace\n./gradlew :composeApp:assembleDebug --stacktrace\n./gradlew :composeApp:desktopJar --stacktrace",
        "report_path": "cmp/shared/build/reports/tests/",
        "report_when": "failure",
        "retention_days": 7,
    },
    "ca84d43ee0762c0d02fb98325047a1b5aee2be2c832c16972af7775c265e465a": {
        "kind": "gradle",
        "java_version": "21",
        "setup_android": True,
        "android_packages": "platform-tools",
        "command": "./gradlew testDebugUnitTest\n./gradlew :shared:desktopTest :desktopApp:test",
        "report_path": "app/build/reports/tests/testDebugUnitTest\nshared/build/reports/tests/desktopTest\ndesktopApp/build/reports/tests/test",
        "report_when": "always",
        "retention_days": 14,
    },
    "9f8da3bca25bfd3dc0b79ccbf911454b10d940e597e3bfeed73995cdc8bd8551": {
        "kind": "gradle",
        "java_version": "21",
        "pre_command": "sed -e 's/{{PROJECT_NUMBER}}/000000000000/' -e 's/{{PROJECT_ID}}/lexorcist-ci/' -e 's/{{APP_ID}}/1:000000000000:android:0000000000000000000000/' -e 's/{{CLIENT_ID}}/000000000000-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.apps.googleusercontent.com/' -e 's/{{GOOGLE_SERVICES_API_KEY}}/AIzaSyAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA/' app/google-services.template.json > app/google-services.json",
        "command": "./gradlew projects --no-daemon\n./gradlew :shared:assemble :app:compileDebugKotlin --no-daemon\n./gradlew :shared:allTests :app:testDebugUnitTest --no-daemon\n./gradlew :app:assembleDebug --no-daemon\n./gradlew :app:minifyReleaseWithR8 --no-daemon",
        "report_path": "app/build/reports/tests/\napp/build/test-results/\nshared/build/reports/tests/\nshared/build/test-results/",
        "report_when": "always",
        "retention_days": 7,
    },
    "3b152efa3c299bbb83309c04d844b1292a3346a844ba1d3193a6beaa7a5c0699": {
        "kind": "gradle",
        "java_version": "21",
        "command": "./gradlew wasmJsBrowserDistribution --no-daemon",
    },
    "f8094e4c2c08c047dc17b2ccb7766dab14eeb775d66238b2c1f93c06fe995cce": {
        "kind": "docker",
        "command": "docker build . --file Dockerfile --tag theharvester:ci",
    },
    "8d0bee7aa3ab78d04396737b8f3fdde27eb3f4164f501979a811cac647b569b7": {
        "kind": "gradle",
        "java_version": "21",
        "inject_google_services": True,
        "command": "node webruntime/src/test/js/jsx-source-chain.test.mjs\nnode webruntime/src/test/js/loader-import-cycle.test.mjs\nnode webruntime/src/test/js/jsx-array-children.test.mjs\nnode webruntime/src/test/js/bridge-source-priority.test.mjs\nset +e\n( timeout --kill-after=1m 25m bash -eo pipefail -c './gradlew assembleDebug bundlePlay testDebugUnitTest desktopMainClasses lintDebug --continue' 2>&1 | tee build.log; echo \"${PIPESTATUS[0]}\" > /tmp/build_exit_code ) &\nBUILD_PID=$!\n( sleep 600; if kill -0 \"$BUILD_PID\" 2>/dev/null; then JCMD=\"${JAVA_HOME:+$JAVA_HOME/bin/jcmd}\"; JCMD=\"${JCMD:-jcmd}\"; for pid in $(\"$JCMD\" -l 2>/dev/null | awk '{print $1}'); do \"$JCMD\" \"$pid\" Thread.print 2>&1 || true; done; fi ) &\nWATCHDOG_PID=$!\nwait \"$BUILD_PID\"\npkill -P \"$WATCHDOG_PID\" 2>/dev/null || true\nkill \"$WATCHDOG_PID\" 2>/dev/null || true\nwait \"$WATCHDOG_PID\" 2>/dev/null || true\nEXIT_CODE=$(cat /tmp/build_exit_code 2>/dev/null || echo 1)\nexit \"$EXIT_CODE\"",
    },
    "6ab641050248a526163bd43e627e6bf32c80a618fa1b0bfb4dbf3d24e1e8c697": {
        "kind": "gradle",
        "java_version": "21",
        "setup_android": True,
        "android_packages": "platform-tools",
        "timeout_minutes": 45,
        "cache_path": "stremio-aars",
        "cache_key": "stremio-media-Linux-95781597c8e3c30d6232e77bdadecc38ad35aa17-v2",
        "extra_checkout_repository": "Stremio/media",
        "extra_checkout_ref": "95781597c8e3c30d6232e77bdadecc38ad35aa17",
        "extra_checkout_path": "vendor/stremio-media",
        "command": "set -euo pipefail\nmissing=0\nfor aar in lib-exoplayer-release.aar lib-decoder-av1-release.aar lib-decoder-ffmpeg-release.aar lib-decoder-iamf-release.aar lib-decoder-mpegh-release.aar; do test -s \"stremio-aars/$aar\" || missing=1; done\nif [ \"$missing\" -ne 0 ]; then chmod +x ci/build-stremio-media.sh; ./ci/build-stremio-media.sh vendor/stremio-media stremio-aars; fi\nfor aar in lib-exoplayer-release.aar lib-decoder-av1-release.aar lib-decoder-ffmpeg-release.aar lib-decoder-iamf-release.aar lib-decoder-mpegh-release.aar; do test -s \"stremio-aars/$aar\" || { echo \"Missing Stremio playback artifact: $aar\" >&2; exit 1; }; cp \"stremio-aars/$aar\" \"playbackcore/libs/$aar\"; done\nchmod +x gradlew\n./gradlew :app:testDebugUnitTest :app:lintDebug :app:assembleDebug --no-daemon --stacktrace",
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
    "cb2a978450da9b6dc82f8527a4ff2dbcde9af37e4e88d99e4409f217826572f0": ".github/workflows/jules-dispatch.yml",
}

# These were inspected individually. They are not alternate implementations of
# useful automation; they are disabled, malformed, placeholders, or one-shot
# temporary scaffolding. Registry sources remain as history after removal.
OBSOLETE_WORKFLOWS: Final[dict[tuple[str, str], str]] = {
    ("hereliesaz/azphalt", ".github/workflows/publish-package.yml"): "superseded by release.yml; the canonical release now falls back to staged/backoff publication after a partial or rate-limited publish",
    ("hereliesaz/azphalt", ".github/workflows/publish-staged.yml"): "superseded by release.yml; staged publication is now the automatic resilient fallback inside the canonical release action",
    ("hereliesaz/fluttertest", ".github/workflows/android_ci_jules.yml"): "superseded by the Flutter-native CI workflow, which builds the same debug APK through the correct Flutter toolchain",
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
    ("hereliesaz/cuedetat", ".github/workflows/android-release-apk.yml"): "superseded by release.yml, which handles both push and manual signed Foss releases for this repository",
    ("hereliesaz/azphalt", ".github/workflows/android-release-apk.yml"): "superseded by app-release.yml, the repository's unified one-version/every-artifact release pipeline",
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
