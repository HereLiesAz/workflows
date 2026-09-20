package com.hereliesaz.click

import android.accessibilityservice.AccessibilityService
import android.accessibilityservice.GestureDescription
import android.content.Context
import android.graphics.Path
import android.graphics.PixelFormat
import android.hardware.Sensor
import android.hardware.SensorEvent
import android.hardware.SensorEventListener
import android.hardware.SensorManager
import android.provider.Settings
import android.view.Gravity
import android.view.KeyEvent
import android.view.LayoutInflater
import android.view.MotionEvent
import android.view.WindowManager
import android.view.accessibility.AccessibilityEvent
import android.widget.ScrollView

/**
 * An Accessibility Service that detects when a camera app is in the foreground and
 * provides alternative methods to trigger the camera shutter using device sensors.
 *
 * This service is the primary bridge between the Android Framework and the app's business logic.
 *
 * Its responsibilities include:
 * - Interacting with Android system services like [WindowManager] and [SensorManager].
 * - Listening for `TYPE_WINDOW_STATE_CHANGED` accessibility events to determine if a known
 *   camera app is active.
 * - Managing the lifecycle of sensor listeners to conserve battery, only running them when
 *   a camera app is in the foreground.
 * - Handling the creation and visibility of a transparent overlay for the fingerprint scroll trigger.
 * - Receiving key events for the volume key trigger.
 * - Delegating the actual trigger decision logic to a [CameraTriggerHandler].
 * - Dispatching the final "tap" gesture to the screen to take a picture.
 */
class ClickAccessibilityService : AccessibilityService(), SensorEventListener {

    /** Manages the transparent overlay view for the fingerprint trigger. */
    private lateinit var windowManager: WindowManager
    /** The transparent, scrollable view used to capture fingerprint scroll gestures. */
    private var overlayView: ScrollView? = null
    /** Manages the device's sensors (proximity and accelerometer). */
    private var sensorManager: SensorManager? = null
    /** The device's proximity sensor, used for the "wave" trigger. */
    private var proximitySensor: Sensor? = null
    /** The device's accelerometer, used for "vibration" and "back tap" triggers. */
    private var accelerometer: Sensor? = null
    /** The business logic handler that determines if an event should trigger a picture. */
    private lateinit var triggerHandler: CameraTriggerHandler

    /** Tracks whether a known camera application is currently in the foreground. */
    private var isCameraAppActive = false
    /** Stores the last known x-axis acceleration value. */
    private var lastX = 0f
    /** Stores the last known y-axis acceleration value. */
    private var lastY = 0f
    /** Stores the last known z-axis acceleration value. */
    private var lastZ = 0f

    companion object {
        /**
         * A set of package names for common camera applications. This service will only activate
         * its features when an app with one of these package names is in the foreground.
         */
        private val CAMERA_PACKAGES = setOf(
            "com.google.android.GoogleCamera", "com.android.camera", "com.android.camera2",
            "com.samsung.android.camera", "com.oneplus.camera", "com.motorola.cameraone",
            "com.sonyericsson.android.camera", "org.codeaurora.snapcam"
        )
    }

    /**
     * Called by the system when the service is first connected. This is where system services
     * are initialized, the [CameraTriggerHandler] is instantiated, and the overlay view is prepared.
     */
    override fun onServiceConnected() {
        super.onServiceConnected()
        triggerHandler = CameraTriggerHandler(
            prefsProvider = { getSharedPreferences(MainActivity.PREFS_NAME, Context.MODE_PRIVATE) },
            clock = SystemClockImpl()
        )
        windowManager = getSystemService(Context.WINDOW_SERVICE) as WindowManager
        sensorManager = getSystemService(Context.SENSOR_SERVICE) as SensorManager
        proximitySensor = sensorManager?.getDefaultSensor(Sensor.TYPE_PROXIMITY)
        accelerometer = sensorManager?.getDefaultSensor(Sensor.TYPE_ACCELEROMETER)
        createOverlayView()
    }

    /**
     * Registers the sensor listeners to start detecting proximity and accelerometer events.
     * This is called only when a camera app becomes active to conserve system resources.
     */
    private fun registerSensors() {
        proximitySensor?.let { sensorManager?.registerListener(this, it, SensorManager.SENSOR_DELAY_NORMAL) }
        accelerometer?.let { sensorManager?.registerListener(this, it, SensorManager.SENSOR_DELAY_UI) }
    }

    /**
     * Unregisters the sensor listeners to stop detecting events and save battery.
     * This is called when a camera app is no longer active.
     */
    private fun unregisterSensors() {
        sensorManager?.unregisterListener(this)
    }

    /**
     * Inflates and configures the transparent overlay view from `R.layout.overlay_layout`.
     * The view is set up to listen for touch events, which are then passed to the
     * [CameraTriggerHandler] to check for a fingerprint scroll gesture.
     */
    private fun createOverlayView() {
        val inflater = getSystemService(Context.LAYOUT_INFLATER_SERVICE) as LayoutInflater
        overlayView = inflater.inflate(R.layout.overlay_layout, null) as ScrollView
        overlayView?.setOnTouchListener { _, event ->
            if (event.action == MotionEvent.ACTION_MOVE && triggerHandler.handleFingerprintEvent()) {
                takePicture()
            }
            false // Return false to ensure the event is not consumed
        }
    }

    /**
     * Handles `TYPE_WINDOW_STATE_CHANGED` events to detect when a camera app becomes active or inactive.
     * This is the main control logic for activating and deactivating the service's features.
     * @param event The accessibility event triggered by the system.
     */
    override fun onAccessibilityEvent(event: AccessibilityEvent) {
        if (event.eventType == AccessibilityEvent.TYPE_WINDOW_STATE_CHANGED) {
            val packageName = event.packageName?.toString() ?: return
            val isNowCamera = CAMERA_PACKAGES.contains(packageName)

            if (isNowCamera && !isCameraAppActive) {
                // A camera app has just become active
                isCameraAppActive = true
                showOverlay()
                registerSensors()
            } else if (!isNowCamera && isCameraAppActive) {
                // The active app is no longer a camera app
                isCameraAppActive = false
                hideOverlay()
                unregisterSensors()
            }
        }
    }

    /**
     * Adds the overlay view to the window manager, making it visible on the screen.
     * This is only done if the view is not already shown and if the app has the necessary
     * "draw over other apps" permission.
     */
    private fun showOverlay() {
        if (overlayView?.windowToken == null && Settings.canDrawOverlays(this)) {
            val params = WindowManager.LayoutParams(
                WindowManager.LayoutParams.WRAP_CONTENT, WindowManager.LayoutParams.MATCH_PARENT,
                WindowManager.LayoutParams.TYPE_ACCESSIBILITY_OVERLAY,
                WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL,
                PixelFormat.TRANSLUCENT
            ).apply { gravity = Gravity.END or Gravity.TOP }
            windowManager.addView(overlayView, params)
        }
    }

    /**
     * Removes the overlay view from the window manager, hiding it from the screen.
     */
    private fun hideOverlay() {
        if (overlayView?.windowToken != null) {
            windowManager.removeView(overlayView)
        }
    }

    /**
     * Called by the [SensorManager] when new sensor data is available. This method routes
     * the raw sensor event data to the [CameraTriggerHandler] to process the specific logic
     * for each trigger type.
     * @param event The [SensorEvent] containing the new data.
     */
    override fun onSensorChanged(event: SensorEvent) {
        if (!isCameraAppActive) return

        when (event.sensor.type) {
            Sensor.TYPE_PROXIMITY -> {
                val distance = event.values[0]
                val maxRange = proximitySensor?.maximumRange ?: distance
                if (triggerHandler.handleProximityEvent(distance, maxRange)) {
                    takePicture()
                }
            }
            Sensor.TYPE_ACCELEROMETER -> {
                val x = event.values[0]
                val y = event.values[1]
                val z = event.values[2]
                // Prioritize back tap event as it is more specific than a general shake
                if (triggerHandler.handleBackTapEvent(z, lastZ)) {
                    takePicture()
                } else if (triggerHandler.handleAccelerometerEvent(x, y, z, lastX, lastY, lastZ)) {
                    takePicture()
                }
                lastX = x
                lastY = y
                lastZ = z
            }
        }
    }

    /**
     * Captures hardware key events, specifically for volume up and down presses.
     * The event is passed to the [CameraTriggerHandler]. If the handler confirms a trigger,
     * this method returns `true` to consume the event, preventing the system from performing
     * the default action (e.g., changing the volume).
     *
     * @param event The [KeyEvent] that occurred.
     * @return `true` if the event was handled, `false` otherwise.
     */
    override fun onKeyEvent(event: KeyEvent): Boolean {
        if (event.action == KeyEvent.ACTION_DOWN) {
            when (event.keyCode) {
                KeyEvent.KEYCODE_VOLUME_UP, KeyEvent.KEYCODE_VOLUME_DOWN -> {
                    if (triggerHandler.handleVolumeKeyEvent()) {
                        takePicture()
                        return true // Consume the event
                    }
                }
            }
        }
        return super.onKeyEvent(event)
    }

    /**
     * Required by the [SensorEventListener] interface. This app does not need to react
     * to changes in sensor accuracy, so this method is empty.
     */
    override fun onAccuracyChanged(sensor: Sensor?, accuracy: Int) {}

    /**
     * Dispatches a simulated tap gesture to the screen to take a picture.
     * If the user has saved custom shutter button coordinates, it taps that location.
     * Otherwise, it defaults to tapping the center of the screen, which works for most
     * camera apps.
     */
    private fun takePicture() {
        val prefs = getSharedPreferences(MainActivity.PREFS_NAME, Context.MODE_PRIVATE)
        val x = prefs.getFloat(MainActivity.KEY_SHUTTER_X, -1f)
        val y = prefs.getFloat(MainActivity.KEY_SHUTTER_Y, -1f)

        val tapPath = Path()

        if (x != -1f && y != -1f) {
            // Use the saved coordinates if they exist
            tapPath.moveTo(x, y)
        } else {
            // Fallback to the center of the screen as a default
            val displayMetrics = resources.displayMetrics
            val centerX = displayMetrics.widthPixels / 2f
            val centerY = displayMetrics.heightPixels / 2f
            tapPath.moveTo(centerX, centerY)
        }

        val gestureBuilder = GestureDescription.Builder()
        gestureBuilder.addStroke(GestureDescription.StrokeDescription(tapPath, 0, 1))
        dispatchGesture(gestureBuilder.build(), null, null)
    }

    /**
     * Called by the system when the service is interrupted (e.g., the user turns it off in settings).
     * This ensures all resources are cleaned up to prevent leaks.
     */
    override fun onInterrupt() {
        isCameraAppActive = false
        hideOverlay()
        unregisterSensors()
    }

    /**
     * Called by the system when the service is being destroyed. Ensures final cleanup of all resources.
     */
    override fun onDestroy() {
        super.onDestroy()
        hideOverlay()
        unregisterSensors()
    }
}
