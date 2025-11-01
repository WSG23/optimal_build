Feature: Compliance Suite
  Scenario: DPIA impact/likelihood sets risk level
    Given I am on the "Compliance - DPIA" page
    When I set impact "High" and likelihood "Medium"
    Then the risk level is "Substantial"

  Scenario: DSAR export bundle
    Given I am on the "Compliance - DSAR" page
    When I export the bundle
    Then a zip with redacted files and index.json is generated

  Scenario: Cross-Border filter
    Given I am on the "Compliance - Cross-Border Transfers" page
    When I filter by "US"
    Then only US transfers remain
