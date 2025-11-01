Feature: Mapping (Live)
  Scenario: Floor selector changes active floor
    Given I am on the "Mapping" page
    When I select floor "3"
    Then the floorplan redraws for floor "3"
