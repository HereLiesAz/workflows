# Faux Pas (Common Mistakes)

This document lists common mistakes to avoid when working on the Click application.

*   **Adding business logic to `ClickAccessibilityService`:** The `ClickAccessibilityService` should only be responsible for interacting with the Android framework. All business logic should be in the `CameraTriggerHandler`.
*   **Not writing unit tests:** All new business logic must be accompanied by unit tests.
*   **Ignoring the existing architecture:** The project has a well-defined architecture. Do not introduce new architectural patterns without first discussing it with the team.
*   **Forgetting to update documentation:** All documentation must be kept up-to-date with any changes made to the codebase.
*   **Introducing Android framework dependencies into `CameraTriggerHandler`:** The `CameraTriggerHandler` should be framework-agnostic. Do not add any `import android...` statements to this class.
