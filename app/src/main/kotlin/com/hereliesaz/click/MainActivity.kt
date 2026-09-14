package com.hereliesaz.click

import android.content.Context
import android.content.Intent
import android.content.SharedPreferences
import android.net.Uri
import android.os.Bundle
import android.provider.Settings
import android.text.TextUtils
import android.widget.Button
import android.widget.SeekBar
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import androidx.appcompat.app.AppCompatDelegate
import com.google.android.material.switchmaterial.SwitchMaterial

/**
 * The main entry point and settings screen of the application.
 *
 * This activity provides the user interface for:
 * 1.  Displaying the current status of the required Accessibility Service and Overlay permissions.
 * 2.  Providing buttons that guide the user to the correct system settings screens to
 *     enable these permissions.
 * 3.  Allowing the user to toggle the different camera trigger methods (e.g., fingerprint,
 *     proximity wave, vibration).
 * 4.  Adjusting the sensitivity for the vibration trigger.
 * 5.  Toggling between light and dark themes.
 * 6.  Providing access to the shutter button location and back-tap calibration activities.
 */
class MainActivity : AppCompatActivity() {

    // UI elements for displaying permission status
    private lateinit var serviceStatusText: TextView
    private lateinit var overlayStatusText: TextView

    // UI controls for enabling/disabling triggers and settings
    private lateinit var fingerprintSwitch: SwitchMaterial
    private lateinit var lensTapProximitySwitch: SwitchMaterial
    private lateinit var lensTapVibrationSwitch: SwitchMaterial
    private lateinit var backTapSwitch: SwitchMaterial
    private lateinit var volumeKeySwitch: SwitchMaterial
    private lateinit var vibrationSensitivitySeekbar: SeekBar
    private lateinit var themeSwitch: SwitchMaterial

    /** The [SharedPreferences] instance for storing all user settings. */
    private lateinit var prefs: SharedPreferences

    /**
     * Companion object holding constants and utility methods for the MainActivity.
     */
    companion object {
        /** The filename for the app's SharedPreferences. */
        const val PREFS_NAME = "ClickPrefs"
        /** SharedPreferences key for storing the theme (true for dark mode, false for light). */
        const val KEY_DARK_MODE = "darkMode"
        /** SharedPreferences key for enabling the fingerprint scroll trigger. */
        const val KEY_FINGERPRINT_ENABLED = "fingerprintEnabled"
        /** SharedPreferences key for enabling the proximity sensor "wave" trigger. */
        const val KEY_LENS_TAP_PROXIMITY_ENABLED = "lensTapProximityEnabled"
        /** SharedPreferences key for enabling the accelerometer "vibration" trigger. */
        const val KEY_LENS_TAP_VIBRATION_ENABLED = "lensTapVibrationEnabled"
        /** SharedPreferences key for enabling the "back tap" trigger. */
        const val KEY_BACK_TAP_ENABLED = "backTapEnabled"
        /** SharedPreferences key for storing the vibration sensitivity level (0-100). */
        const val KEY_VIBRATION_SENSITIVITY = "vibrationSensitivity"
        /** SharedPreferences key for the custom shutter button X-coordinate. */
        const val KEY_SHUTTER_X = "shutter_x"
        /** SharedPreferences key for the custom shutter button Y-coordinate. */
        const val KEY_SHUTTER_Y = "shutter_y"
        /** SharedPreferences key for the calibrated back-tap sensitivity threshold. */
        const val KEY_BACK_TAP_SENSITIVITY = "back_tap_sensitivity"
        /** SharedPreferences key for enabling the volume key trigger. */
        const val KEY_VOLUME_KEY_ENABLED = "volumeKeyEnabled"

        /**
         * Checks if the specified Accessibility Service is currently enabled in the system settings.
         * This is done by querying the secure settings for the list of enabled services and checking
         * if our service's component name is present.
         *
         * @param context The application context.
         * @param accessibilityService The class of the service to check (e.g., `ClickAccessibilityService::class.java`).
         * @return `true` if the service is enabled, `false` otherwise.
         */
        fun isAccessibilityServiceEnabled(context: Context, accessibilityService: Class<*>): Boolean {
            val colonSplitter = TextUtils.SimpleStringSplitter(':')
            val settingValue = Settings.Secure.getString(context.contentResolver, Settings.Secure.ENABLED_ACCESSIBILITY_SERVICES)

            settingValue?.let {
                colonSplitter.setString(it)
                while (colonSplitter.hasNext()) {
                    val componentName = colonSplitter.next()
                    if (componentName.equals(context.packageName + "/" + accessibilityService.name, ignoreCase = true)) {
                        return true
                    }
                }
            }
            return false
        }
    }

    /**
     * Initializes the activity, its views, and listeners.
     * This method is responsible for setting up the UI, applying the user's saved theme,
     * and configuring listeners for all interactive elements like buttons and switches.
     * @param savedInstanceState If the activity is being re-initialized, this Bundle contains
     *                           the most recent data, otherwise it is null.
     */
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        com.hereliesaz.click.utils.CrashReporter.init(this)
        prefs = getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        applyTheme() // Apply the theme before setting the content view
        setContentView(R.layout.activity_main)

        // Initialize UI components by finding them in the layout
        serviceStatusText = findViewById(R.id.service_status_text)
        overlayStatusText = findViewById(R.id.overlay_permission_status_text)
        fingerprintSwitch = findViewById(R.id.fingerprint_scroll_switch)
        lensTapProximitySwitch = findViewById(R.id.lens_tap_proximity_switch)
        lensTapVibrationSwitch = findViewById(R.id.lens_tap_vibration_switch)
        backTapSwitch = findViewById(R.id.back_tap_switch)
        volumeKeySwitch = findViewById(R.id.volume_key_switch)
        vibrationSensitivitySeekbar = findViewById(R.id.vibration_sensitivity_seekbar)
        themeSwitch = findViewById(R.id.theme_switch)

        // Initialize buttons and set their click listeners
        val enableServiceButton: Button = findViewById(R.id.enable_service_button)
        val enableOverlayButton: Button = findViewById(R.id.enable_overlay_permission_button)
        val recordShutterButton: Button = findViewById(R.id.record_shutter_button)
        val calibrateButton: Button = findViewById(R.id.calibrate_back_tap_button)

        calibrateButton.setOnClickListener {
            startActivity(Intent(this, TapCalibrationActivity::class.java))
        }

        recordShutterButton.setOnClickListener {
            startActivity(Intent(this, GestureCaptureActivity::class.java))
        }

        enableServiceButton.setOnClickListener {
            startActivity(Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS))
        }

        enableOverlayButton.setOnClickListener {
            if (!Settings.canDrawOverlays(this)) {
                val intent = Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION, Uri.parse("package:$packageName"))
                startActivity(intent)
            }
        }

        // Set up listeners for switches to save their state to SharedPreferences
        fingerprintSwitch.setOnCheckedChangeListener { _, isChecked ->
            prefs.edit().putBoolean(KEY_FINGERPRINT_ENABLED, isChecked).apply()
        }

        lensTapProximitySwitch.setOnCheckedChangeListener { _, isChecked ->
            prefs.edit().putBoolean(KEY_LENS_TAP_PROXIMITY_ENABLED, isChecked).apply()
        }

        lensTapVibrationSwitch.setOnCheckedChangeListener { _, isChecked ->
            vibrationSensitivitySeekbar.isEnabled = isChecked
            prefs.edit().putBoolean(KEY_LENS_TAP_VIBRATION_ENABLED, isChecked).apply()
        }

        vibrationSensitivitySeekbar.setOnSeekBarChangeListener(object : SeekBar.OnSeekBarChangeListener {
            override fun onProgressChanged(seekBar: SeekBar?, progress: Int, fromUser: Boolean) {}
            override fun onStartTrackingTouch(seekBar: SeekBar?) {}
            override fun onStopTrackingTouch(seekBar: SeekBar?) {
                prefs.edit().putInt(KEY_VIBRATION_SENSITIVITY, seekBar?.progress ?: 50).apply()
            }
        })

        themeSwitch.setOnCheckedChangeListener { _, isChecked ->
            prefs.edit().putBoolean(KEY_DARK_MODE, isChecked).apply()
            val mode = if (isChecked) AppCompatDelegate.MODE_NIGHT_YES else AppCompatDelegate.MODE_NIGHT_NO
            AppCompatDelegate.setDefaultNightMode(mode)
            recreate() // Recreate the activity to apply the new theme
        }

        backTapSwitch.setOnCheckedChangeListener { _, isChecked ->
            prefs.edit().putBoolean(KEY_BACK_TAP_ENABLED, isChecked).apply()
        }

        volumeKeySwitch.setOnCheckedChangeListener { _, isChecked ->
            prefs.edit().putBoolean(KEY_VOLUME_KEY_ENABLED, isChecked).apply()
        }
    }

    /**
     * Called when the activity is resumed or becomes visible to the user.
     * This is the ideal place to update the UI to reflect the current state of system
     * permissions and user settings, as the user may have changed them in another screen.
     */
    override fun onResume() {
        super.onResume()
        // Post UI updates to the view's message queue to ensure they run after the layout is complete.
        serviceStatusText.post {
            updateServiceStatus()
            updateOverlayPermissionStatus()
        }
        loadPreferences()
    }

    /**
     * Applies the selected theme (light or dark) to the activity.
     * It reads the preference from SharedPreferences and sets the default night mode for the app.
     * This method is called in `onCreate` before the content view is set.
     */
    private fun applyTheme() {
        val isDarkMode = prefs.getBoolean(KEY_DARK_MODE, true) // Default to dark mode
        val mode = if (isDarkMode) AppCompatDelegate.MODE_NIGHT_YES else AppCompatDelegate.MODE_NIGHT_NO
        AppCompatDelegate.setDefaultNightMode(mode)
    }

    /**
     * Loads all saved preferences from SharedPreferences and updates the UI controls
     * (switches, seekbar) to reflect the stored values.
     */
    private fun loadPreferences() {
        themeSwitch.isChecked = prefs.getBoolean(KEY_DARK_MODE, true)
        fingerprintSwitch.isChecked = prefs.getBoolean(KEY_FINGERPRINT_ENABLED, false)
        lensTapProximitySwitch.isChecked = prefs.getBoolean(KEY_LENS_TAP_PROXIMITY_ENABLED, false)
        lensTapVibrationSwitch.isChecked = prefs.getBoolean(KEY_LENS_TAP_VIBRATION_ENABLED, false)
        backTapSwitch.isChecked = prefs.getBoolean(KEY_BACK_TAP_ENABLED, false)
        volumeKeySwitch.isChecked = prefs.getBoolean(KEY_VOLUME_KEY_ENABLED, false)
        vibrationSensitivitySeekbar.progress = prefs.getInt(KEY_VIBRATION_SENSITIVITY, 50)
        vibrationSensitivitySeekbar.isEnabled = lensTapVibrationSwitch.isChecked
    }

    /**
     * Updates the service status TextView with appropriate text and background color
     * based on whether the Accessibility Service is currently enabled.
     */
    private fun updateServiceStatus() {
        if (isAccessibilityServiceEnabled(this, ClickAccessibilityService::class.java)) {
            serviceStatusText.text = "Service Status: Enabled"
            serviceStatusText.setBackgroundColor(0xFFC8E6C9.toInt()) // Green
        } else {
            serviceStatusText.text = "Service Status: Disabled"
            serviceStatusText.setBackgroundColor(0xFFFFCDD2.toInt()) // Red
        }
    }

    /**
     * Updates the overlay permission status TextView with appropriate text and background color
     * based on whether the "draw over other apps" permission has been granted.
     */
    private fun updateOverlayPermissionStatus() {
        if (Settings.canDrawOverlays(this)) {
            overlayStatusText.text = "Overlay Permission: Granted"
            overlayStatusText.setBackgroundColor(0xFFC8E6C9.toInt())
        } else {
            overlayStatusText.text = "Overlay Permission: Denied"
            overlayStatusText.setBackgroundColor(0xFFFFCDD2.toInt())
        }
    }
}
