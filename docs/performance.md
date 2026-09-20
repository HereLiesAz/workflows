# Performance

This document provides performance considerations and guidelines for the Click application.

## 1. Battery

To conserve battery, the app's sensors are only active when a known camera app is running in the foreground. When you switch to another app or turn off the screen, sensor listening is automatically paused.

## 2. CPU

The app's CPU usage is minimal. The sensor listeners run on a background thread, and the business logic in the `CameraTriggerHandler` is very lightweight.

## 3. Memory

The app's memory usage is also minimal. The `ClickAccessibilityService` and `CameraTriggerHandler` are the only long-lived objects.

## 4. Guidelines

*   **Avoid long-running operations on the main thread:** All long-running operations should be performed on a background thread.
*   **Use `SharedPreferences` for small amounts of data:** `SharedPreferences` is not designed to store large amounts of data. If you need to store a large amount of data, consider using a database.
*   **Release resources when they are no longer needed:** Make sure to release any resources, such as sensor listeners, when they are no longer needed.
