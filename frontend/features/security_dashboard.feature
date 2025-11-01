Feature: Security Dashboard
  Scenario: Period toggle updates aggregations
    Given I view the "Security Dashboard"
    When I switch the period to "30d"
    Then MTTA, MTTR, and Incident Volume recompute for "30d"
