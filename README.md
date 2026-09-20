# Click.

An app for taking pictures when the shutter button is inconvenient or out of reach. It uses your phone's sensors to trigger the shutter in your favorite camera app.

## The Triggers

You can enable any combination of the following methods from the app's main screen. All triggers work by simulating a **tap in the center of the screen**, which should work with most camera apps.

### 1. Proximity "Wave"
*   **What it does:** Lets you take a picture by waving your hand or finger over the top of your phone (near the earpiece).
*   **How it works:** It uses the proximity sensor to detect a brief shadow, which it interprets as a "wave." This is great for group photos or when the phone is mounted on a tripod.

### 2. Vibration "Tap"
*   **What it does:** Lets you take a picture by tapping the back or side of your phone.
*   **How it works:** It uses the accelerometer to feel for the specific jolt of a physical tap.
*   **Sensitivity:** To prevent accidental triggers from ambient movement (like a bumpy car ride), you can adjust the sensitivity of this trigger in the app. A higher sensitivity requires a harder tap.

### 3. Fingerprint Scroll
*   **What it does:** Lets you take a picture by swiping down on your phone's fingerprint scanner (if it supports gestures).
*   **How it works:** It places an invisible overlay on the screen to intercept the scroll gesture. If your phone uses fingerprint swipes for notification access, this swipe is registered and translated into a shutter command.
*   **Permission Required:** This is the only trigger that requires the "Draw Over Other Apps" permission.

## The Setup

To make this work, you have to grant two permissions. The app will guide you to the correct settings screen for each.

1.  **Accessibility Service:** This is the core of the app. It's required so `Click` can know when a camera app is active and can simulate the screen tap. **It does not read any screen content, passwords, or other personal information.**
2.  **Draw Over Other Apps:** This is **only** needed for the *Fingerprint Scroll* trigger. It allows the app to place its invisible overlay.

## A Note on Battery

To conserve battery, the app's sensors are only active when a known camera app is running in the foreground. When you switch to another app or turn off the screen, sensor listening is automatically paused.