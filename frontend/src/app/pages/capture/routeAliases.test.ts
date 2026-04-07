import { describe, expect, it } from 'vitest'

import {
  AGENT_CAPTURE_ROUTE_PATHS,
  DEVELOPER_CAPTURE_ROUTE_PATHS,
  PROJECT_CAPTURE_ROUTE_PATH,
} from './routeAliases'

describe('capture route aliases', () => {
  it('keeps all developer capture aliases on the unified capture workspace', () => {
    expect(DEVELOPER_CAPTURE_ROUTE_PATHS).toEqual([
      '/app/capture',
      '/app/site-acquisition',
      '/developers/site-acquisition',
    ])
    expect(PROJECT_CAPTURE_ROUTE_PATH).toBe('/projects/:projectId/capture')
  })

  it('keeps agent capture aliases distinct and non-overlapping', () => {
    expect(AGENT_CAPTURE_ROUTE_PATHS).toEqual([
      '/app/gps-capture',
      '/agents/site-capture',
    ])

    const allPaths = [
      ...DEVELOPER_CAPTURE_ROUTE_PATHS,
      ...AGENT_CAPTURE_ROUTE_PATHS,
      PROJECT_CAPTURE_ROUTE_PATH,
    ]

    expect(new Set(allPaths).size).toBe(allPaths.length)
  })
})
