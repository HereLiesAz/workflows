package com.hereliesaz.click

import android.content.Context
import android.hardware.Sensor
import android.hardware.SensorEvent
import android.hardware.SensorEventListener
import android.hardware.SensorManager
import android.os.Bundle
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import kotlin.math.abs

/**
 * An activity dedicated to calibrating the sensitivity of the "back tap" trigger.
 *
 * This activity instructs the user to tap the back of their device a few times. It
 * listens for spikes in the accelerometer's Z-axis to detect these taps. After a
 * required number of taps are recorded, it calculates an average tap force and saves
 * a sensitivity threshold to [SharedPreferences]. This allows the back-tap feature
 * to be tailored to the user's specific device and tap strength.
 */
class TapCalibrationActivity : AppCompatActivity(), SensorEventListener {

    /** Manages the device's sensors, specifically the accelerometer. */
    private lateinit var sensorManager: SensorManager
    /** The device's accelerometer sensor. */
    private var accelerometer: Sensor? = null
    /** The TextView used to display the current status of the calibration process. */
    private lateinit var calibrationStatusText: TextView

    /** Stores the last known z-axis acceleration value to calculate the delta. */
    private var lastZ = 0f
    /** The number of valid taps recorded so far. */
    private var tapsRecorded = 0
    /** A list to store the measured force (deltaZ) of each recorded tap. */
    private val recordedForces = mutableListOf<Float>()
    /** The timestamp of the last recorded tap, used for cooldown/debouncing. */
    private var lastTapTimestamp = 0L

    /**
     * Companion object holding constants for the calibration process.
     */
    companion object {
        /** The key for storing the calibrated back-tap sensitivity threshold in SharedPreferences. */
        const val KEY_BACK_TAP_SENSITIVITY = "back_tap_sensitivity"
        /** The number of taps the user needs to perform to complete the calibration. */
        private const val REQUIRED_TAPS = 3
        /** A cooldown period (in milliseconds) to prevent a single physical shake from being counted as multiple taps. */
        private const val TAP_COOLDOWN_MS = 300L
    }

    /**
     * Initializes the activity, its views, and the [SensorManager].
     * @param savedInstanceState If the activity is being re-initialized, this Bundle contains
     *                           the most recent data, otherwise it is null.
     */
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_tap_calibration)

        calibrationStatusText = findViewById(R.id.calibration_status)
        sensorManager = getSystemService(Context.SENSOR_SERVICE) as SensorManager
        accelerometer = sensorManager.getDefaultSensor(Sensor.TYPE_ACCELEROMETER)
    }

    /**
     * Called when the activity is resumed. Registers the accelerometer sensor listener to
     * start listening for tap events.
     */
    override fun onResume() {
        super.onResume()
        sensorManager.registerListener(this, accelerometer, SensorManager.SENSOR_DELAY_UI)
    }

    /**
     * Called when the activity is paused. Unregisters the sensor listener to conserve
     * battery and system resources.
     */
    override fun onPause() {
        super.onPause()
        sensorManager.unregisterListener(this)
    }

    /**
     * Required by [SensorEventListener], but not used in this activity.
     */
    override fun onAccuracyChanged(sensor: Sensor?, accuracy: Int) {
        // Not needed
    }

    /**
     * Called when new sensor data is available. This is the core of the calibration logic.
     * It monitors the accelerometer's Z-axis for sharp changes, which indicate a tap.
     * @param event The [SensorEvent] containing the new data.
     */
    override fun onSensorChanged(event: SensorEvent) {
        if (event.sensor.type == Sensor.TYPE_ACCELEROMETER) {
            val z = event.values[2]
            val deltaZ = abs(z - lastZ)
            lastZ = z

            val currentTime = System.currentTimeMillis()
            // A tap is detected if the change in Z-axis acceleration is above a high initial threshold
            // and enough time has passed since the last tap.
            if (deltaZ > 15 && (currentTime - lastTapTimestamp > TAP_COOLDOWN_MS)) {
                lastTapTimestamp = currentTime
                tapsRecorded++
                recordedForces.add(deltaZ)
                calibrationStatusText.text = "Taps Recorded: $tapsRecorded of $REQUIRED_TAPS"

                if (tapsRecorded >= REQUIRED_TAPS) {
                    finishCalibration()
                }
            }
        }
    }

    /**
     * Finalizes the calibration process. It calculates the sensitivity threshold, saves it
     * to [SharedPreferences], provides feedback to the user, and closes the activity.
     */
    private fun finishCalibration() {
        if (recordedForces.isEmpty()) {
            Toast.makeText(this, "Calibration failed. Please try again.", Toast.LENGTH_SHORT).show()
        } else {
            // Calculate the sensitivity threshold. We use 75% of the average recorded force
            // to create a threshold that is sensitive but not prone to accidental triggers.
            val averageForce = recordedForces.average()
            val sensitivity = (averageForce * 0.75).toFloat()

            val prefs = getSharedPreferences(MainActivity.PREFS_NAME, Context.MODE_PRIVATE)
            prefs.edit().putFloat(KEY_BACK_TAP_SENSITIVITY, sensitivity).apply()

            Toast.makeText(this, "Calibration complete! Sensitivity set to ${"%.2f".format(sensitivity)}", Toast.LENGTH_LONG).show()
        }
        finish() // Close the calibration activity
    }
}
