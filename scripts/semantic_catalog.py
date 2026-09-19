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
            "edf31723ec2cdb361831175f5005831d3812924e21ed639288c057d87172528d",
            "40b44c43d74996ee59074631cdb2746a7910024a716db4f4619ba1e748977c80",
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
    ".github/workflows/android-debug-ci.yml": {
        "name": "Android Debug CI",
        "canonical_hash": "6f25a5f112d324c4bb19236302c860917f1e65e984e919e778afdd634a97336d",
        "source_hashes": {
            "6f25a5f112d324c4bb19236302c860917f1e65e984e919e778afdd634a97336d",
        },
    },
}

PURPOSE_PROFILES: Final[dict[str, dict[str, object]]] = {
    "968458e29535134b77927dbc8ec6c653ad070e0b6e9cd30f7ac9063544eb14e9": {"tool": "maven", "java_version": "17", "publish_command": "mvn --batch-mode deploy"},
    "03e2f1e420d12d9cc0a7cdbd64594ac76c6f5025b064f43083b57b0714cf087a": {"tool": "gradle", "java_version": "21", "jitpack": True, "build_command": "./gradlew assemble", "publish_command": "./gradlew publish"},
    "57f245d8d8504ca1ef5146ccc3533aecc5d08c45ab5aa9416b3b619ba3c385a9": {
        "kind": "node",
        "node_version": "22",
        "java_version": "17",
        "version_frozen": "1",
        "command": "corepack enable\npnpm install --frozen-lockfile\npnpm build\npnpm test\npnpm fixtures\ngit add -N conformance/fixtures\ngit diff --exit-code -- conformance/fixtures\nnode .github/scripts/write-google-services.mjs\n( cd apps/storefront-cmp && chmod +x gradlew && ./gradlew wasmJsBrowserDistribution --no-daemon --stacktrace && ./gradlew assembleDebug --no-daemon --stacktrace && ./gradlew desktopTest --no-daemon --stacktrace && ./gradlew :azp:test --no-daemon --stacktrace )",
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
    "202a3be9eb627b6679ca3723e6f47d154b9c5b0703c517cf79ec7f6f5ff6c89a": {"mode": "changesets", "node_version": "22", "registry_url": "https://registry.npmjs.org", "scope": "", "token": "npm", "working_directory": ".", "prepare_command": "corepack enable && npm install -g npm@10 && pnpm install --frozen-lockfile", "version_command": "pnpm run version", "publish_command": "pnpm run release", "version_branch": "changeset-release/main", "version_pr_title": "chore: version packages"},
    "edf31723ec2cdb361831175f5005831d3812924e21ed639288c057d87172528d": {"mode": "single-retry", "node_version": "22", "registry_url": "https://registry.npmjs.org", "scope": "", "token": "npm", "working_directory": ".", "prepare_command": "corepack enable && npm install -g npm@10 && pnpm install --frozen-lockfile", "default_package": "@azphalt/azdk", "build_command": "pnpm --filter \"$PACKAGE...\" build", "publish_script": "scripts/publish-one-retry.sh"},
    "40b44c43d74996ee59074631cdb2746a7910024a716db4f4619ba1e748977c80": {"mode": "staged", "node_version": "22", "registry_url": "https://registry.npmjs.org", "scope": "", "token": "npm", "working_directory": ".", "prepare_command": "corepack enable && npm install -g npm@10 && pnpm install --frozen-lockfile", "build_command": "pnpm build", "publish_script": "scripts/publish-staged.sh", "promote_script": "scripts/promote-latest.sh", "stage_size": "5", "stage_cooldown": "120", "call_cooldown": "30", "staging_tag": "staging"},
    "ecaa174d3910d20491133343eb12f16cb2979108025efeced85d28a9b6e7c9b1": {"java_version":"21","use_gradle_setup":False,"version_mode":"fixed","fixed_version":"1.0.0","cancel_in_progress":True,"release_mode":"none","matrix":{"include":[{"os":"ubuntu-latest","artifact":"hashkitty-linux-installer","path":"installer_output/*.deb","prepare":"sudo apt-get update && sudo apt-get install -y fakeroot","build":"cd hashkitty-java && chmod +x gradlew && ./gradlew clean installDist; cd ..; printf 'main-class=hashkitty.java.server.ServerApp\\n' > server.properties; \"$JAVA_HOME/bin/jpackage\" --name hashkitty --input hashkitty-java/app/build/install/app/lib --main-jar app.jar --main-class hashkitty.java.App --app-version \"$DESKTOP_VERSION\" --dest installer_output --type deb --add-launcher server=server.properties --java-options '-Djava.library.path=$APPDIR' --verbose"},{"os":"windows-latest","artifact":"hashkitty-windows-installer","path":"installer_output/*.exe","prepare":"","build":"cd hashkitty-java && ./gradlew clean installDist; cd ..; printf 'main-class=hashkitty.java.server.ServerApp\\n' > server.properties; \"$JAVA_HOME/bin/jpackage\" --name hashkitty --input hashkitty-java/app/build/install/app/lib --main-jar app.jar --main-class hashkitty.java.App --app-version \"$DESKTOP_VERSION\" --dest installer_output --type exe --win-dir-chooser --win-menu --win-shortcut --add-launcher server=server.properties --verbose"}]}},
    "acc1dc959c04a0f3c4c42f8768b3aa469dfd5a449d0a02584cb2a98641f8d14b": {"java_version":"21","use_gradle_setup":True,"version_mode":"none","cancel_in_progress":True,"release_mode":"none","matrix":{"include":[{"os":"ubuntu-latest","artifact":"desktop-linux-deb","path":"desktop/build/compose/binaries/main/deb/*.deb","prepare":"","build":"chmod +x gradlew && ./gradlew :desktop:packageDeb --build-cache --stacktrace"},{"os":"macos-latest","artifact":"desktop-macos-dmg","path":"desktop/build/compose/binaries/main/dmg/*.dmg","prepare":"","build":"chmod +x gradlew && ./gradlew :desktop:packageDmg --build-cache --stacktrace"},{"os":"windows-latest","artifact":"desktop-windows-msi","path":"desktop/build/compose/binaries/main/msi/*.msi","prepare":"","build":"./gradlew :desktop:packageMsi --build-cache --stacktrace"}]}},
    "c6251f2b6b5fe71bea894085048df9338151bc914505f23dbd5f8f37c4721190": {"java_version":"21","use_gradle_setup":True,"version_mode":"none","cancel_in_progress":False,"release_mode":"guillotine","release_title":"","release_body":"Guillotine desktop installers. Unsigned builds: on macOS use Open from the context menu; on Windows use More info → Run anyway if SmartScreen blocks the installer; on Linux install the downloaded .deb with apt.","matrix":{"include":[{"os":"ubuntu-latest","artifact":"guillotine-desktop-linux-deb","path":"desktop/build/compose/binaries/main/deb/*.deb","prepare":"","build":"chmod +x gradlew && ./gradlew :desktop:packageDeb --build-cache --stacktrace"},{"os":"macos-latest","artifact":"guillotine-desktop-macos-dmg","path":"desktop/build/compose/binaries/main/dmg/*.dmg","prepare":"","build":"chmod +x gradlew && ./gradlew :desktop:packageDmg --build-cache --stacktrace"},{"os":"windows-latest","artifact":"guillotine-desktop-windows-msi","path":"desktop/build/compose/binaries/main/msi/*.msi","prepare":"","build":"./gradlew :desktop:packageMsi --build-cache --stacktrace"}]}},
    "f085283d13372c3d20dfeb8e47b3fe2541f7c912f15c30547257aa22c11be7c2": {"java_version":"21","use_gradle_setup":True,"version_mode":"mcpserved","cancel_in_progress":True,"release_mode":"mcpserved","release_title":"","release_body":"Native desktop installers for Windows, macOS, and Linux.","matrix":{"include":[{"os":"ubuntu-latest","artifact":"mcpserved-desktop-linux","path":"dist/*","prepare":"sudo apt-get update && sudo apt-get install -y fakeroot binutils rpm","build":"chmod +x ./gradlew || true; ./gradlew :desktop:packageDistributionForCurrentOS -PdesktopPackageVersion=\"$DESKTOP_VERSION\" --stacktrace; mkdir -p dist; find desktop/build/compose/binaries/main -type f \\( -name '*.dmg' -o -name '*.msi' -o -name '*.exe' -o -name '*.deb' -o -name '*.rpm' \\) -exec cp {} dist/ \\;; ls -la dist"},{"os":"macos-latest","artifact":"mcpserved-desktop-macos","path":"dist/*","prepare":"","build":"chmod +x ./gradlew || true; ./gradlew :desktop:packageDistributionForCurrentOS -PdesktopPackageVersion=\"$DESKTOP_VERSION\" --stacktrace; mkdir -p dist; find desktop/build/compose/binaries/main -type f \\( -name '*.dmg' -o -name '*.msi' -o -name '*.exe' -o -name '*.deb' -o -name '*.rpm' \\) -exec cp {} dist/ \\;; ls -la dist"},{"os":"windows-latest","artifact":"mcpserved-desktop-windows","path":"dist/*","prepare":"","build":"chmod +x ./gradlew || true; ./gradlew :desktop:packageDistributionForCurrentOS -PdesktopPackageVersion=\"$DESKTOP_VERSION\" --stacktrace; mkdir -p dist; find desktop/build/compose/binaries/main -type f \\( -name '*.dmg' -o -name '*.msi' -o -name '*.exe' -o -name '*.deb' -o -name '*.rpm' \\) -exec cp {} dist/ \\;; ls -la dist"}]}},
    "e6dc8ef902c25e4c1b5dfcc338526e617afb9e104fb1cadbaac740ab7b259d3e": {"signing": "project", "java_version": "17", "google_services": "none", "build_command": "./gradlew assembleDebug", "artifact_glob": "app/build/outputs/apk/debug/*.apk", "persist_version": False, "version_mode": "major-minor-run-count", "asset_name_mode": "preserve", "move_tag": False, "prerelease": True, "release_title_style": "app-tag", "release_notes_mode": "changelog", "app_name": "ReUp"},
    "0734d0c56fd8fc16abd5aee34a30f1170e6b42abafae354aff05eee485e54704": {"signing": "pem-chain", "java_version": "21", "google_services": "none", "build_command": "./gradlew clean assembleFossRelease -PversionCode=$RUN_NUMBER -PversionName=1.3.0.$RUN_NUMBER", "artifact_glob": "app/build/outputs/apk/foss/release/*.apk", "persist_version": False, "version_mode": "run-number-base", "base_version": "1.3.0", "fixed_tag": "v1.3-debug", "asset_name_mode": "app-v-version", "move_tag": True, "prerelease": True, "release_title": "1.3 Debug Builds", "wrapper_validation": True, "keystore_output": "app/release.keystore", "gradle_properties": ["org.gradle.jvmargs=-Xmx3072m", "android.useAndroidX=true"], "app_name": "Cue-Detat"},
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
        "extra_checkout_repository": "Stremio/media",
        "extra_checkout_ref": "95781597c8e3c30d6232e77bdadecc38ad35aa17",
        "extra_checkout_path": "vendor/stremio-media",
        "command": "chmod +x ci/build-stremio-media.sh\n./ci/build-stremio-media.sh vendor/stremio-media stremio-aars\nfor aar in lib-exoplayer-release.aar lib-decoder-av1-release.aar lib-decoder-ffmpeg-release.aar lib-decoder-iamf-release.aar lib-decoder-mpegh-release.aar; do test -s \"stremio-aars/$aar\" || { echo \"Missing Stremio playback artifact: $aar\" >&2; exit 1; }; cp \"stremio-aars/$aar\" \"playbackcore/libs/$aar\"; done\nchmod +x gradlew\n./gradlew :app:testDebugUnitTest :app:lintDebug :app:assembleDebug --no-daemon --stacktrace",
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
