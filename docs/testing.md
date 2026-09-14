# Testing

This document describes the testing strategy and guidelines for the Click application.

## 1. Unit Tests

The most important tests are the unit tests for the `CameraTriggerHandler`, as this class contains the core logic.

*   **To run all unit tests:**
    ```bash
    ./gradlew testDebugUnitTest
    ```
    The test report will be generated at `app/build/reports/tests/testDebugUnitTest/index.html`.

**Testing Strategy:** The `CameraTriggerHandlerTest.kt` file demonstrates the correct way to test the logic. It mocks the `SharedPreferences` dependency and injects a controllable `TestClock` to verify the behavior of the handler in isolation, without needing the Android framework.

## 2. Manual Testing

Manual testing is also important to ensure that the app works as expected on a variety of devices.

### Test Cases

*   Verify that the app can detect when a camera app is in the foreground.
*   Verify that the "Wave" trigger works as expected.
*   Verify that the "Tap" trigger works as expected.
*   Verify that the "Fingerprint Scroll" trigger works as expected.
*   Verify that the app stops listening for sensor events when the camera app is no longer in the foreground.

## 3. Guidelines

*   **Write unit tests for all new business logic:** All new or modified logic in `CameraTriggerHandler` must be accompanied by unit tests.
*   **Test on a variety of devices:** The app should be tested on a variety of devices with different screen sizes, resolutions, and Android versions.
*   **Test in a variety of environments:** The app should be tested in a variety of environments, such as a quiet room, a noisy street, and a moving car.
