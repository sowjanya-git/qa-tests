---
Feature: Login
Test Case ID: LOGIN-010
Test Scenario: 	Session Handling & Navigation Control Post Login
Test Description: Validate how the application behaves after login when navigating across tabs, using browser back button, and during idle timeout. Ensures session security and smooth navigation.
Pre-Conditions: User must be registered and active
-  User must be able to login successfully
-  Session timeout must be configured (e.g., 15 mins)
Priority: Medium
Test Type: End-to-End + Security
Defect ID: 
Jira Keys: SCRUM-2
---

## Test Steps
1. Login with valid credentials
2. Open a second browser tab and access the same app URL
3. Confirm user is logged in on both tabs
4. On original tab, click the browser “Back” button
5. Ensure app doesn't navigate back to login page or show cached sensitive data
6. Leave browser idle for more than configured timeout (e.g., 15+ minutes)
7. Refresh or perform any action in the app

**Test Data:** Valid email/password
- Timeout value = 15 mins (configurable)
- Any browser (Chrome/Edge preferred)
- Secure app URL

## Expected Result
Second tab maintains the same logged-in session
- Browser “Back” doesn’t take user back to login or expose form
- After timeout, session expires and user is redirected to login on next action with a message like “Session expired”

## Actual Result


## Status
Pending

## Comments

