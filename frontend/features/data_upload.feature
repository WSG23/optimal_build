Feature: Data Upload
  Scenario: Auto-map schema with manual correction
    Given I upload "access_logs.csv"
    When auto-detection maps known fields
    And I map "time" to "timestamp"
    Then the preview updates correctly
