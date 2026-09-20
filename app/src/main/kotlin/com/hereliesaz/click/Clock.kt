package com.hereliesaz.click

import android.os.SystemClock

/**
 * An interface to abstract away the system clock.
 *
 * This abstraction is a critical part of the application's testability strategy. By depending
 * on this interface instead of calling `SystemClock.uptimeMillis()` directly, the business
 * logic in [CameraTriggerHandler] can be tested with a controllable, deterministic clock
 * (like a `TestClock` in the unit tests). This allows for reliable testing of time-dependent
 * features like cooldowns and double-tap windows without introducing unpredictable waits.
 */
interface Clock {
    /**
     * Returns the number of milliseconds since the device booted. This value is guaranteed to be
     * monotonic and is suitable for measuring time intervals.
     * @return The current uptime in milliseconds.
     */
    fun uptimeMillis(): Long
}

/**
 * The production implementation of the [Clock] interface.
 * This class simply delegates the call to the Android `SystemClock`, providing real-world
 * time data to the application when it is running normally.
 */
class SystemClockImpl : Clock {
    /**
     * Fetches the current uptime from `android.os.SystemClock`.
     * @return The time since boot in milliseconds.
     */
    override fun uptimeMillis(): Long {
        return SystemClock.uptimeMillis()
    }
}
