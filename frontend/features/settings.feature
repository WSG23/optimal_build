Feature: Settings
  Scenario: Toggle GDPR mode
    Given I am on "Settings"
    When I enable "GDPR mode"
    Then PII redaction defaults to ON across the app
