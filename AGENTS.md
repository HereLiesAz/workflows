# Agent Developer Notes for Click

## **MANDATORY PRE-COMMIT REQUIREMENTS**

**WITHOUT EXCEPTION, all of the following conditions MUST be met before committing any changes:**

1.  **Complete Code Review:** The AI MUST request and receive a complete code review from a human developer.
2.  **Passing Build and Tests:** The AI MUST run a full build and execute all unit tests. The build MUST succeed, and all tests MUST pass.
3.  **Up-to-Date Documentation:** The AI MUST keep all documents and documentation (`/docs` directory) updated with any changes made to the codebase.

---

This document provides guidance for AI agents and human developers working on the Click application.

## 1. Documentation Index

The `/docs` directory contains a comprehensive set of documents that are an extension of this `AGENTS.md` file and are every bit as important. All agents and developers are required to be familiar with the contents of these documents.

-   `AGENT_GUIDE.md`: A guide for AI agents on how to work with this codebase.
-   `TODO.md`: A list of tasks to be completed.
-   `UI_UX.md`: An overview of the UI/UX design and principles.
-   `auth.md`: Details on authentication and authorization (if any).
-   `conduct.md`: The code of conduct for this project.
-   `data_layer.md`: Information about the data layer, including data sources and models.
-   `fauxpas.md`: A list of common mistakes to avoid.
-   `file_descriptions.md`: Descriptions of all files in the project.
-   `misc.md`: Miscellaneous notes and information.
-   `performance.md`: Performance considerations and guidelines.
-   `screens.md`: A breakdown of all screens in the application.
-   `task_flow.md`: A description of the user task flow.
-   `testing.md`: The testing strategy and guidelines.
-   `workflow.md`: The development workflow.

---

## 2. Project Overview

Click is an Android application that provides alternative methods for triggering the camera shutter using the phone's hardware sensors. It is designed to be a lightweight utility that runs in the background when a camera app is active.

## 3. Architecture

The application's architecture is designed to separate Android framework dependencies from the core business logic. This makes the application more modular, maintainable, and, most importantly, **testable**.

### Key Components

*   **`ClickAccessibilityService`**: This is the main entry point for the background service and the primary point of interaction with the Android framework.
    *   **Responsibilities:**
        *   Detecting when a known camera app is in the foreground using `AccessibilityEvent`s.
        *   Managing the lifecycle of sensor listeners (`SensorManager`).
        *   Displaying and managing the invisible overlay for the fingerprint trigger (`WindowManager`).
        *   Dispatching the final "tap" gesture to the screen (`dispatchGesture`).
    *   **It should NOT contain any complex business logic.** It acts as a bridge, sensing events and delegating the decision-making to the `CameraTriggerHandler`.

*   **`CameraTriggerHandler`**: This is a plain Kotlin class that contains all the business logic for the camera triggers.
    *   **Responsibilities:**
        *   Implementing the logic for the proximity, vibration, and fingerprint triggers.
        *   Managing the state for each trigger (e.g., cooldowns, sensor coverage).
        *   Determining if a given event should result in a picture being taken.
    *   **This class is framework-agnostic.** It should not have any `import android...` statements except for interfaces that are part of the dependency contract (like `SharedPreferences`).

*   **`Clock` interface (`Clock.kt`)**: This interface abstracts away the system clock.
    *   **`SystemClockImpl`**: The production implementation that uses the real `android.os.SystemClock`.
    *   **`TestClock`**: The test implementation that allows for manual time control, making time-dependent tests (like for cooldowns) deterministic and fast.

*   **`MainActivity`**: The main UI of the app. Its primary purpose is to guide the user through enabling the necessary permissions and to allow them to toggle the different trigger features.

## 4. How to Build the Project

This project uses the Gradle wrapper. All commands should be run from the root of the repository.

*   **To build a debug APK:**
    ```bash
    ./gradlew assembleDebug
    ```
    The output APK will be located in `app/build/outputs/apk/debug/`.

*   **To clean the project:**
    ```bash
    ./gradlew clean
    ```

## 5. How to Test the Project

The most important tests are the unit tests for the `CameraTriggerHandler`, as this class contains the core logic.

*   **To run all unit tests:**
    ```bash
    ./gradlew testDebugUnitTest
    ```
    The test report will be generated at `app/build/reports/tests/testDebugUnitTest/index.html`.

**Testing Strategy:** The `CameraTriggerHandlerTest.kt` file demonstrates the correct way to test the logic. It mocks the `SharedPreferences` dependency and injects a controllable `TestClock` to verify the behavior of the handler in isolation, without needing the Android framework.

## 6. Contribution Guidelines

*   **Maintain Separation of Concerns:** Any new trigger logic or complex decision-making should be added to `CameraTriggerHandler`, not the service. The service should only handle interactions with the Android OS.
*   **Write Unit Tests:** All new or modified logic in `CameraTriggerHandler` must be accompanied by unit tests.
*   **Preserve Documentation:** Ensure KDocs are updated for any changes to public or internal methods to keep the codebase clear and maintainable.
