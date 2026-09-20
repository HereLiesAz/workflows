# Workflow

This document describes the development workflow for the Click application.

## 1. Branching

*   All new features and bug fixes should be developed on a separate feature branch.
*   The branch name should be descriptive of the feature or bug fix.
*   Once the feature or bug fix is complete, a pull request should be created to merge the branch into the `main` branch.

## 2. Code Reviews

*   All pull requests must be reviewed by at least one other developer before they can be merged.
*   The reviewer should check for code quality, correctness, and adherence to the project's coding style and conventions.

## 3. Continuous Integration

*   The project uses a continuous integration (CI) server to automatically build and test all pull requests.
*   The CI server runs the unit tests and generates a test report.
*   A pull request cannot be merged unless the CI build succeeds and all tests pass.

## 4. Releasing

*   The project uses semantic versioning.
*   When a new version of the app is ready to be released, a new release branch should be created from the `main` branch.
*   The version number should be updated in the `build.gradle.kts` file.
*   The release branch should be tested thoroughly before it is merged into the `main` branch.
*   Once the release branch is merged, a new tag should be created for the release.

## 5. Automated Issue Management

*   This repository uses the `google-labs-code/jules-invoke` action to automatically assign and attempt to resolve new issues using an AI agent (Jules).
*   When a new issue is opened (or a security advisory published), the workflow triggers Jules to:
    *   Assign the issue to itself.
    *   Attempt to resolve the issue by modifying code, running tests, and updating documentation.
    *   Close the issue upon successful verification.
