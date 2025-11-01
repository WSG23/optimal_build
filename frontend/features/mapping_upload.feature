Feature: Mapping Upload
  @smoke
  Scenario: Upload and calibrate blueprint
    Given I open "Mapping Upload"
    When I upload "floor2.svg"
    Then the preview uses calibrated dimensions
