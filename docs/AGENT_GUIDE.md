# AI Agent Guide

This document provides a guide for AI agents on how to work with this codebase.

## 1. Core Principles

*   **Familiarize Yourself:** Before making any changes, thoroughly read and understand the `AGENTS.md` file, as well as all the documentation in the `/docs` directory.
*   **Prioritize Testing:** This project emphasizes a test-driven development (TDD) approach. All new business logic must be accompanied by unit tests.
*   **Maintain Code Quality:** Adhere to the existing coding style and conventions. Ensure that all code is well-documented with KDoc comments.
*   **Respect the Architecture:** The separation of concerns between the `ClickAccessibilityService` and `CameraTriggerHandler` is a core architectural principle. Do not introduce business logic into the service.

## 2. Onboarding

1.  **Read the Documentation:** Start by reading all the documentation in the `/docs` directory to get a comprehensive understanding of the project.
2.  **Run the Tests:** Execute the unit tests to ensure that the project is in a good state.
3.  **Explore the Code:** Familiarize yourself with the codebase, paying close attention to the key components outlined in the `AGENTS.md` file.

## 3. Workflow

1.  **Understand the Task:** Before starting a task, make sure you have a clear understanding of the requirements.
2.  **Write a Test:** If the task involves adding new business logic, write a failing unit test that describes the desired behavior.
3.  **Implement the Logic:** Write the code to make the test pass.
4.  **Refactor:** Refactor the code to improve its design and readability.
5.  **Update Documentation:** Update all relevant documentation to reflect the changes you've made.
6.  **Request a Review:** Request a code review from a human developer.
7.  **Submit:** Once the review is complete and all tests pass, submit your changes.

## 4. Communication

*   **Be Clear and Concise:** When communicating with human developers, be clear and concise in your language.
*   **Provide Context:** When asking a question or reporting an issue, provide as much context as possible.
*   **Be Patient:** Human developers may not always be available to answer your questions immediately. Be patient and wait for a response.
