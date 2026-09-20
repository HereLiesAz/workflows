package com.hereliesaz.click

import android.content.Context
import android.content.SharedPreferences
import android.os.Bundle
import android.view.MotionEvent
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity

/**
 * An activity that provides a full-screen, transparent interface for the user to
 * record the on-screen location of their camera app's shutter button.
 *
 * When the user touches the screen, this activity captures the absolute X and Y
 * coordinates of the touch event and saves them to [SharedPreferences]. The activity
 * then immediately finishes, returning the user to the previous screen.
 *
 * The saved coordinates will be used by the [ClickAccessibilityService] to dispatch
 * tap gestures to the correct location.
 */
class GestureCaptureActivity : AppCompatActivity() {

    /** The [SharedPreferences] instance used to store the captured coordinates. */
    private lateinit var prefs: SharedPreferences

    /**
     * Constants for the keys used to store the shutter button coordinates in SharedPreferences.
     */
    companion object {
        /** The key for the X-coordinate of the shutter button. */
        const val KEY_SHUTTER_X = "shutter_x"
        /** The key for the Y-coordinate of the shutter button. */
        const val KEY_SHUTTER_Y = "shutter_y"
    }

    /**
     * Called when the activity is first created. Sets up the content view and initializes
     * the [SharedPreferences] instance.
     * @param savedInstanceState If the activity is being re-initialized after previously
     *                           being shut down, this Bundle contains the data it most
     *                           recently supplied in [onSaveInstanceState]. Otherwise, it is null.
     */
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_gesture_capture)
        prefs = getSharedPreferences(MainActivity.PREFS_NAME, Context.MODE_PRIVATE)
    }

    /**
     * Called when a touch screen event occurs.
     *
     * This method listens for the `ACTION_DOWN` event, which indicates the start of a touch.
     * When detected, it gets the raw screen coordinates of the touch, saves them to
     * [SharedPreferences], displays a confirmation [Toast], and then closes the activity.
     *
     * @param event The [MotionEvent] object containing full information about the event.
     * @return `true` if the event was handled, `false` otherwise.
     */
    override fun onTouchEvent(event: MotionEvent): Boolean {
        if (event.action == MotionEvent.ACTION_DOWN) {
            val x = event.rawX
            val y = event.rawY

            // Save the coordinates to SharedPreferences
            prefs.edit()
                .putFloat(KEY_SHUTTER_X, x)
                .putFloat(KEY_SHUTTER_Y, y)
                .apply()

            // Provide feedback to the user and close the activity
            Toast.makeText(this, "Shutter location saved!", Toast.LENGTH_SHORT).show()
            finish()
            return true
        }
        return super.onTouchEvent(event)
    }
}
