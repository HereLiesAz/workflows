package com.hereliesaz.click

import android.content.SharedPreferences
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith
import org.mockito.Mock
import org.mockito.Mockito.*
import org.mockito.junit.MockitoJUnitRunner
import org.junit.Assert.*

@RunWith(MockitoJUnitRunner::class)
class CameraTriggerHandlerTest {

    @Mock
    private lateinit var mockPrefs: SharedPreferences

    private lateinit var triggerHandler: CameraTriggerHandler
    private lateinit var testClock: TestClock

    /**
     * A controllable clock for testing time-dependent logic.
     */
    class TestClock(private var currentTime: Long = 0) : Clock {
        override fun uptimeMillis(): Long {
            return currentTime
        }

        fun advanceTime(millis: Long) {
            currentTime += millis
        }
    }

    @Before
    fun setUp() {
        testClock = TestClock()
        // The handler is initialized with a lambda that provides the mocked SharedPreferences
        // and our controllable TestClock.
        triggerHandler = CameraTriggerHandler(
            prefsProvider = { mockPrefs },
            clock = testClock
        )
    }

    @Test
    fun `proximity event returns true on valid tap`() {
        `when`(mockPrefs.getBoolean(MainActivity.KEY_LENS_TAP_PROXIMITY_ENABLED, false)).thenReturn(true)

        // Simulate sensor covered
        assertFalse(triggerHandler.handleProximityEvent(distance = 0f, maxRange = 5f))

        // Advance time and simulate sensor uncovered
        testClock.advanceTime(100)
        assertTrue(triggerHandler.handleProximityEvent(distance = 5f, maxRange = 5f))
    }

    @Test
    fun `proximity event returns false when disabled`() {
        `when`(mockPrefs.getBoolean(MainActivity.KEY_LENS_TAP_PROXIMITY_ENABLED, false)).thenReturn(false)
        assertFalse(triggerHandler.handleProximityEvent(distance = 0f, maxRange = 5f))
        assertFalse(triggerHandler.handleProximityEvent(distance = 5f, maxRange = 5f))
    }

    @Test
    fun `fingerprint event returns true and has cooldown`() {
        `when`(mockPrefs.getBoolean(MainActivity.KEY_FINGERPRINT_ENABLED, false)).thenReturn(true)

        // First event should be true
        assertTrue(triggerHandler.handleFingerprintEvent())

        // Advance time slightly, should still be in cooldown
        testClock.advanceTime(100)
        assertFalse(triggerHandler.handleFingerprintEvent())

        // Advance time past the cooldown
        testClock.advanceTime(500)
        assertTrue(triggerHandler.handleFingerprintEvent())
    }

    @Test
    fun `accelerometer event returns true on significant shake`() {
        `when`(mockPrefs.getBoolean(MainActivity.KEY_LENS_TAP_VIBRATION_ENABLED, false)).thenReturn(true)
        `when`(mockPrefs.getInt(MainActivity.KEY_VIBRATION_SENSITIVITY, 50)).thenReturn(50) // Default sensitivity

        // A large change in acceleration should trigger it
        assertTrue(triggerHandler.handleAccelerometerEvent(x = 50f, y = 50f, z = 50f, lastX = 0f, lastY = 0f, lastZ = 0f))
    }

    @Test
    fun `accelerometer event returns false on insignificant shake`() {
        `when`(mockPrefs.getBoolean(MainActivity.KEY_LENS_TAP_VIBRATION_ENABLED, false)).thenReturn(true)
        `when`(mockPrefs.getInt(MainActivity.KEY_VIBRATION_SENSITIVITY, 50)).thenReturn(50)

        // A small change should not trigger it
        assertFalse(triggerHandler.handleAccelerometerEvent(x = 1f, y = 1f, z = 1f, lastX = 0f, lastY = 0f, lastZ = 0f))
    }

    @Test
    fun `volume key event returns true and has cooldown`() {
        `when`(mockPrefs.getBoolean(MainActivity.KEY_VOLUME_KEY_ENABLED, false)).thenReturn(true)

        // First event should be true
        assertTrue(triggerHandler.handleVolumeKeyEvent())

        // Advance time slightly, should still be in cooldown
        testClock.advanceTime(100)
        assertFalse(triggerHandler.handleVolumeKeyEvent())

        // Advance time past the cooldown
        testClock.advanceTime(500)
        assertTrue(triggerHandler.handleVolumeKeyEvent())
    }
}
