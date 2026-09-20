# Data Layer

This document provides information about the data layer in the Click application, including data sources and models.

## 1. Data Sources

The Click application has two main data sources:

*   **`SharedPreferences`**: Used to store the user's preferences, such as which triggers are enabled and the sensitivity of the "Tap" trigger.
*   **`SensorManager`**: Provides access to the device's sensors, such as the accelerometer and proximity sensor.

## 2. Data Models

The Click application does not have any complex data models. The data is stored as simple key-value pairs in `SharedPreferences`.

## 3. Data Flow

The data flows from the `MainActivity` to the `CameraTriggerHandler`. The `MainActivity` is responsible for reading the user's preferences from `SharedPreferences` and passing them to the `CameraTriggerHandler`. The `CameraTriggerHandler` then uses this information to determine which triggers to enable and how to respond to sensor events.
