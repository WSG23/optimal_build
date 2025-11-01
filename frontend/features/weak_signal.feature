Feature: Weak-Signal Feed
  Scenario: Deduplication collapses near-duplicates
    Given similar items share a dedupe group
    When the feed renders
    Then they appear as a single collapsed card
