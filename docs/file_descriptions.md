# Project File Descriptions

This document provides a brief but thorough description of all key non-ignored files in the project.

-   `./.gitignore`: Specifies intentionally untracked files to ignore, such as build artifacts and local configuration files.
-   `./AGENTS.md`: Provides guidance for AI agents and human developers working on the Click application, including mandatory pre-commit requirements.
-   `./build.gradle.kts`: The root Gradle build script for the project, configuring project-wide settings and dependencies.
-   `./gradlew` & `./gradlew.bat`: Gradle wrapper scripts for Unix-based systems and Windows, respectively, ensuring a consistent Gradle version is used.
-   `./app/build.gradle.kts`: The Gradle build script for the `app` module, defining dependencies and build settings specific to the Android application.
-   `./app/src/main/AndroidManifest.xml`: The Android application manifest file, declaring the app's components, permissions, and other essential information.

## Core Source Files (`app/src/main/kotlin/com/hereliesaz/click/`)

-   `MainActivity.kt`: The main entry point of the application. It provides the UI for enabling/disabling triggers, adjusting settings, and guiding the user through permission grants.
-   `ClickAccessibilityService.kt`: The core background service that detects when a camera app is active. It manages sensor listeners and delegates trigger logic to the `CameraTriggerHandler`.
-   `CameraTriggerHandler.kt`: A framework-agnostic class containing all the business logic for the camera triggers (proximity, vibration, back-tap, etc.). It is designed to be highly testable.
-   `Clock.kt`: An interface and implementation for abstracting the system clock, allowing for deterministic testing of time-dependent logic.
-   `TapCalibrationActivity.kt`: An activity that allows users to calibrate the sensitivity of the back-tap trigger by recording their tap strength.
-   `GestureCaptureActivity.kt`: An activity that allows users to record the on-screen location of their camera's shutter button for precise tap simulation.
-   `./utils/CrashReporter.kt`: A utility for reporting crashes to a remote server.
-   `./utils/Secrets.kt`: A placeholder file for storing secrets like API keys, which is ignored by version control.

## Resource Files (`app/src/main/res/`)

-   `./layout/activity_main.xml`: The layout file for the main settings screen (`MainActivity`).
-   `./layout/activity_tap_calibration.xml`: The layout file for the back-tap calibration screen.
-   `./layout/activity_gesture_capture.xml`: The layout file for the shutter button capture screen.
-   `./values/strings.xml`: Contains all the string resources used in the application.
-   `./xml/accessibility_service_config.xml`: The configuration file for the `ClickAccessibilityService`, declaring its capabilities and required permissions.

## Test Files (`app/src/test/`)

-   `./kotlin/com/hereliesaz/click/CameraTriggerHandlerTest.kt`: Unit tests for the `CameraTriggerHandler`, ensuring the core business logic works as expected.
