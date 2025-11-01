Feature: Mission Control
  @smoke
  Scenario: Timeline brush filters graph and events
    Given I am on the "Mission Control" page
    When I brush the timeline from "10:00" to "14:00"
    Then the graph updates to events within that range
