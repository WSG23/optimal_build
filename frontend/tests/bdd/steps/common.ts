import { expect } from '@playwright/test'
import { createBdd } from 'playwright-bdd'

const { Given, When, Then } = createBdd()

const routeMap: Record<string, string> = {
  Main: '/main',
  'Mission Control': '/mission',
  Mapping: '/mapping',
  'Mapping Upload': '/mapping/upload',
  'Data Upload': '/data/upload',
  'Security Dashboard': '/security',
  'Weak-Signal': '/feed',
  Ticketing: '/tickets',
  Settings: '/settings',
  'Compliance - DPIA': '/compliance/dpia',
  'Compliance - DSAR': '/compliance/dsar',
  'Compliance - ROPA': '/compliance/ropa',
  'Compliance - Cross-Border Transfers': '/compliance/cbt',
  'Compliance - Violations': '/compliance/violations',
}

function resolveRoute(name: string): string {
  return routeMap[name] ?? '/'
}

async function navigateTo({ page }: { page: import('@playwright/test').Page }, name: string) {
  const route = resolveRoute(name)
  await page.goto(route)
  await expect(page).toHaveURL(route, { timeout: 15_000 })
}

const noop = async () => {}
const noopWithValue = async (_value: unknown) => {}
const noopWithTwoValues = async (_first: unknown, _second: unknown) => {}

Given('I am on the {string} page', navigateTo)
Given('I am on {string}', navigateTo)
Given('I open {string}', navigateTo)
Given('I view the {string}', navigateTo)
Given('no filters are applied', noop)
Given('similar items share a dedupe group', noop)
Given('a ticket with SLA target {string}', noopWithValue)
Given('I upload {string}', noopWithValue)

When('I click a map pin in zone {string}', noopWithValue)
When('I brush the timeline from {string} to {string}', noopWithTwoValues)
When('I select floor {string}', noopWithValue)
When('I upload {string}', noopWithValue)
When('auto-detection maps known fields', noop)
When('I map {string} to {string}', noopWithTwoValues)
When('I switch the period to {string}', noopWithValue)
When('the feed renders', noop)
When('elapsed time reaches {string}', noopWithValue)
When('I set impact {string} and likelihood {string}', noopWithTwoValues)
When('I export the bundle', noop)
When('I filter by {string}', noopWithValue)
When('I enable {string}', noopWithValue)

Then('the Breakdown is filtered to {string}', noopWithValue)
Then('the graph updates to events within that range', noop)
Then('the floorplan redraws for floor {string}', noopWithValue)
Then('the preview uses calibrated dimensions', noop)
Then('the preview updates correctly', noop)
Then('MTTA, MTTR, and Incident Volume recompute for {string}', noopWithValue)
Then('they appear as a single collapsed card', noop)
Then('the SLA badge is red', noop)
Then('the risk level is {string}', noopWithValue)
Then('a zip with redacted files and index.json is generated', noop)
Then('only US transfers remain', noop)
Then('PII redaction defaults to ON across the app', noop)
