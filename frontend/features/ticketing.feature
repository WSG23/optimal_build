Feature: Ticketing
  Scenario: SLA badge colorization
    Given a ticket with SLA target "30m"
    When elapsed time reaches "31m"
    Then the SLA badge is red
