Feature: Main Dashboard
  @smoke
  Scenario: Map pin filters Breakdown and Feed
    Given I am on the "Main" page
    And no filters are applied
    When I click a map pin in zone "F2-Z14"
    Then the Breakdown is filtered to "F2-Z14"
