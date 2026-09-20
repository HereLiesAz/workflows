package com.hereliesaz.click

import android.content.SharedPreferences
import kotlin.math.abs

/**
 * A framework-agnostic class that contains the core business logic for detecting
 * various camera trigger events (proximity, vibration, fingerprint, back tap, volume key). This class is
 * designed to be easily unit-testable, with no direct dependencies on the Android framework.
 *
 * State management for each trigger (like cooldowns and last event times) is handled internally.
 *
 * @param prefsProvider A function that provides the current [SharedPreferences] instance
 *                      to access user settings. This is a provider function to ensure the
 *                      latest preferences are always used.
 * @param clock A [Clock] implementation to allow for time-dependent logic (like cooldowns)
 *              to be controlled and tested deterministically.
 */
class CameraTriggerHandler(
    private val prefsProvider: () -> SharedPreferences,
    private val clock: Clock
) {

    /** The time when the proximity sensor was last covered. Used to calculate the duration of a "wave". */
    private var proximityCoverTime = 0L
    /** Tracks the current state of the proximity sensor (covered or not). */
    private var isProximityCovered = false
    /** The time of the last detected "shake" or "vibration" event to enforce a cooldown. */
    private var lastShakeTime = -1L
    /** The time of the last fingerprint scroll event to enforce a cooldown. */
    private var lastFingerprintTime = -1L
    /** The time of the last detected tap in a potential double-tap sequence. */
    private var lastTapTime = 0L
    /** The number of taps detected within the double-tap time window. */
    private var tapCount = 0
    /** The time of the last volume key press to enforce a cooldown. */
    private var lastVolumePressTime = -1L

    /**
     * Constants that define the behavior of the camera triggers, such as cooldowns and thresholds.
     */
    companion object {
        /** The maximum duration (in milliseconds) for a proximity "wave" to be considered a tap. */
        private const val PROXIMITY_TAP_THRESHOLD_MS = 500L
        /** The base acceleration threshold for the vibration trigger when sensitivity is at maximum. */
        private const val VIBRATION_BASE_THRESHOLD = 10.0
        /** The maximum acceleration threshold for the vibration trigger when sensitivity is at minimum. */
        private const val VIBRATION_MAX_THRESHOLD = 60.0
        /** The cooldown period (in milliseconds) after a vibration trigger to prevent multiple triggers. */
        private const val VIBRATION_COOLDOWN_MS = 500L
        /** The cooldown period (in milliseconds) after a fingerprint trigger. */
        private const val FINGERPRINT_COOLDOWN_MS = 500L
        /** The base acceleration threshold for the back-tap trigger. */
        private const val BACK_TAP_THRESHOLD = 25.0
        /** The time window (in milliseconds) in which two taps must occur to be considered a double-tap. */
        private const val BACK_TAP_WINDOW_MS = 500L
        /** The cooldown period (in milliseconds) after a successful double-tap trigger. */
        private const val BACK_TAP_COOLDOWN_MS = 1000L
        /** The cooldown period (in milliseconds) after a volume key trigger. */
        private const val VOLUME_KEY_COOLDOWN_MS = 500L
    }

    /**
     * Processes a proximity sensor event to determine if a "wave" gesture occurred.
     * A wave is defined as a brief period where the sensor is covered and then uncovered,
     * lasting less than [PROXIMITY_TAP_THRESHOLD_MS].
     *
     * @param distance The distance value from the proximity sensor event.
     * @param maxRange The maximum range of the proximity sensor.
     * @return `true` if a wave gesture should trigger a picture, `false` otherwise. Returns `false`
     *         if the feature is disabled in preferences.
     */
    fun handleProximityEvent(distance: Float, maxRange: Float): Boolean {
        val lensTapProximityEnabled = prefsProvider().getBoolean(MainActivity.KEY_LENS_TAP_PROXIMITY_ENABLED, false)
        if (!lensTapProximityEnabled) return false

        if (distance < maxRange) {
            // Sensor is covered
            if (!isProximityCovered) {
                isProximityCovered = true
                proximityCoverTime = clock.uptimeMillis()
            }
        } else {
            // Sensor is uncovered
            if (isProximityCovered) {
                val duration = clock.uptimeMillis() - proximityCoverTime
                isProximityCovered = false
                if (duration < PROXIMITY_TAP_THRESHOLD_MS) {
                    return true // A valid "wave" was detected
                }
            }
        }
        return false
    }

    /**
     * Processes an accelerometer event to determine if a "vibration" or "shake" gesture occurred.
     * This is detected by checking for a sudden, significant change in acceleration across any
     * axis. The sensitivity of the detection is dynamically calculated based on user preferences.
     *
     * @param x The current acceleration force along the x-axis.
     * @param y The current acceleration force along the y-axis.
     * @param z The current acceleration force along the z-axis.
     * @param lastX The previous acceleration force along the x-axis.
     * @param lastY The previous acceleration force along the y-axis.
     * @param lastZ The previous acceleration force along the z-axis.
     * @return `true` if a vibration gesture should trigger a picture, `false` otherwise. Returns `false`
     *         if the feature is disabled or if it is on cooldown.
     */
    fun handleAccelerometerEvent(x: Float, y: Float, z: Float, lastX: Float, lastY: Float, lastZ: Float): Boolean {
        val lensTapVibrationEnabled = prefsProvider().getBoolean(MainActivity.KEY_LENS_TAP_VIBRATION_ENABLED, false)
        if (!lensTapVibrationEnabled) return false

        val currentTime = clock.uptimeMillis()
        if (lastShakeTime != -1L && (currentTime - lastShakeTime) < VIBRATION_COOLDOWN_MS) {
            return false // In cooldown
        }

        // Calculate a dynamic threshold based on user-set sensitivity.
        // Higher sensitivity value means a lower threshold (easier to trigger).
        val sensitivity = prefsProvider().getInt(MainActivity.KEY_VIBRATION_SENSITIVITY, 50)
        val progress = sensitivity / 100.0
        val dynamicThreshold = VIBRATION_MAX_THRESHOLD - (progress * (VIBRATION_MAX_THRESHOLD - VIBRATION_BASE_THRESHOLD))

        val deltaX = abs(x - lastX)
        val deltaY = abs(y - lastY)
        val deltaZ = abs(z - lastZ)

        if (deltaX > dynamicThreshold || deltaY > dynamicThreshold || deltaZ > dynamicThreshold) {
            lastShakeTime = currentTime
            return true
        }
        return false
    }

    /**
     * Processes a z-axis accelerometer event to detect a "double-tap" on the back of the device.
     * A double-tap is registered when two spikes in the z-axis acceleration occur within the
     * [BACK_TAP_WINDOW_MS]. The sensitivity of the tap detection is based on a calibrated
     * threshold from user preferences.
     *
     * @param z The current acceleration force along the z-axis.
     * @param lastZ The previous acceleration force along the z-axis.
     * @return `true` if a double-tap gesture should trigger a picture, `false` otherwise. Returns
     *         `false` if the feature is disabled or if the conditions for a double-tap are not met.
     */
    fun handleBackTapEvent(z: Float, lastZ: Float): Boolean {
        val prefs = prefsProvider()
        val backTapEnabled = prefs.getBoolean(MainActivity.KEY_BACK_TAP_ENABLED, false)
        if (!backTapEnabled) return false

        val calibratedThreshold = prefs.getFloat(MainActivity.KEY_BACK_TAP_SENSITIVITY, BACK_TAP_THRESHOLD.toFloat())
        val currentTime = clock.uptimeMillis()
        val deltaZ = abs(z - lastZ)

        if (deltaZ > calibratedThreshold) {
            // A potential tap was detected
            if (currentTime - lastTapTime > BACK_TAP_WINDOW_MS) {
                // This tap is outside the window, so it's the first tap of a new sequence.
                tapCount = 1
            } else {
                // This tap is within the window, increment the count.
                tapCount++
            }
            lastTapTime = currentTime

            if (tapCount == 2) {
                // Double-tap successful
                tapCount = 0 // Reset for the next one
                lastTapTime = currentTime + BACK_TAP_COOLDOWN_MS // Enforce cooldown to prevent immediate re-trigger
                return true
            }
        }

        // Reset tap count if the time between taps is too long.
        if (currentTime - lastTapTime > BACK_TAP_WINDOW_MS) {
            tapCount = 0
        }

        return false
    }

    /**
     * Processes a fingerprint swipe event. This method uses a simple cooldown
     * ([FINGERPRINT_COOLDOWN_MS]) to prevent a single swipe from triggering multiple pictures.
     *
     * @return `true` if a fingerprint gesture should trigger a picture, `false` otherwise. Returns
     *         `false` if the feature is disabled or on cooldown.
     */
    fun handleFingerprintEvent(): Boolean {
        val fingerprintEnabled = prefsProvider().getBoolean(MainActivity.KEY_FINGERPRINT_ENABLED, false)
        if (!fingerprintEnabled) return false

        val currentTime = clock.uptimeMillis()
        if (lastFingerprintTime == -1L || currentTime - lastFingerprintTime > FINGERPRINT_COOLDOWN_MS) {
            lastFingerprintTime = currentTime
            return true
        }
        return false
    }

    /**
     * Processes a volume key event. This method uses a simple cooldown ([VOLUME_KEY_COOLDOWN_MS])
     * to prevent a single long press or multiple rapid presses from triggering multiple pictures.
     *
     * @return `true` if a volume key press should trigger a picture, `false` otherwise. Returns
     *         `false` if the feature is disabled or on cooldown.
     */
    fun handleVolumeKeyEvent(): Boolean {
        val volumeKeyEnabled = prefsProvider().getBoolean(MainActivity.KEY_VOLUME_KEY_ENABLED, false)
        if (!volumeKeyEnabled) return false

        val currentTime = clock.uptimeMillis()
        if (lastVolumePressTime == -1L || currentTime - lastVolumePressTime > VOLUME_KEY_COOLDOWN_MS) {
            lastVolumePressTime = currentTime
            return true
        }
        return false
    }
}
