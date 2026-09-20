# Task Flow

This document describes the user task flow in the Click application.

## 1. First-Time User

1.  The user launches the app for the first time.
2.  The user is greeted with a welcome screen that explains what the app does.
3.  The user is guided through the process of granting the necessary permissions.
4.  The user is taken to the main screen, where they can enable the different trigger features.

## 2. Returning User

1.  The user launches the app.
2.  The user is taken to the main screen.
3.  The user can enable/disable the different trigger features and adjust the sensitivity of the "Tap" trigger.

## 3. Taking a Picture

1.  The user opens a camera app.
2.  The `ClickAccessibilityService` detects that a camera app is in the foreground and starts listening for sensor events.
3.  The user performs one of the enabled trigger actions (e.g., waves their hand over the proximity sensor).
4.  The `CameraTriggerHandler` detects the trigger action and simulates a tap on the screen to take a picture.
5.  The user closes the camera app.
6.  The `ClickAccessibilityService` detects that the camera app is no longer in the foreground and stops listening for sensor events.
