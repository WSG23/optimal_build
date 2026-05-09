import { useMemo } from 'react'
import { Breadcrumbs as MuiBreadcrumbs, Typography } from '@mui/material'
import NavigateNextIcon from '@mui/icons-material/NavigateNext'

import { Link, useRouterPath } from '../../router'
import { useOptionalProject } from '../../contexts/useProject'

/**
 * Maps project-scoped URL path segments to human-readable display names.
 */
const MODULE_DISPLAY_NAMES: Record<string, string> = {
  'due-diligence': 'Due Diligence',
  feasibility: 'Asset Feasibility',
  finance: 'Financial Control',
  phases: 'Phase Management',
  team: 'Consultant Coordination',
  regulatory: 'Regulatory Navigation',
  evidence: 'Evidence Room',
  capture: 'Site Capture',
}

interface BreadcrumbSegment {
  label: string
  href: string | null
}

/**
 * Parses the current path into breadcrumb segments for project-scoped routes.
 * Returns null when the current route is not project-scoped.
 */
function parseProjectBreadcrumbs(
  path: string,
  projectName: string | undefined,
): BreadcrumbSegment[] | null {
  const match = path.match(/^\/projects\/([^/]+)(?:\/([^/]+))?/)
  if (!match) {
    return null
  }

  const projectId = match[1]
  const moduleSlug = match[2]

  const segments: BreadcrumbSegment[] = [
    { label: 'Projects', href: '/projects' },
    {
      label: projectName ?? 'Project',
      href: `/projects/${projectId}`,
    },
  ]

  if (moduleSlug) {
    const moduleName =
      MODULE_DISPLAY_NAMES[moduleSlug] ?? formatSegment(moduleSlug)
    segments.push({ label: moduleName, href: null })
  }

  return segments
}

/** Fallback: converts a slug like "my-module" to "My Module". */
function formatSegment(slug: string): string {
  return slug
    .split('-')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

const separatorSx = {
  color: 'text.disabled',
  fontSize: 'var(--ob-font-size-2xs)',
} as const

const linkSx = {
  fontFamily: 'var(--ob-font-family-mono)',
  fontSize: 'var(--ob-font-size-xs)',
  color: 'text.secondary',
  textDecoration: 'none',
  '&:hover': {
    color: 'text.primary',
    textDecoration: 'underline',
  },
} as const

const currentSx = {
  fontFamily: 'var(--ob-font-family-mono)',
  fontSize: 'var(--ob-font-size-xs)',
  color: 'text.primary',
  fontWeight: 'var(--ob-font-weight-semibold)',
} as const

/**
 * ProjectBreadcrumbs
 *
 * Renders a breadcrumb trail for project-scoped routes
 * (paths matching `/projects/:projectId/*`).
 * Renders nothing when the current route is outside project scope.
 */
export function ProjectBreadcrumbs() {
  const path = useRouterPath()
  const projectContext = useOptionalProject()
  const currentProject = projectContext?.currentProject ?? null

  const segments = useMemo(
    () => parseProjectBreadcrumbs(path, currentProject?.name),
    [path, currentProject?.name],
  )

  if (!segments) {
    return null
  }

  return (
    <MuiBreadcrumbs
      separator={<NavigateNextIcon sx={separatorSx} aria-hidden="true" />}
      aria-label="Project navigation"
      sx={{
        py: 'var(--ob-space-050)',
        px: 'var(--ob-space-200)',
      }}
    >
      {segments.map((segment, idx) => {
        const isLast = idx === segments.length - 1

        if (isLast || !segment.href) {
          return (
            <Typography key={segment.label} sx={currentSx}>
              {segment.label}
            </Typography>
          )
        }

        return (
          <Link key={segment.label} to={segment.href} style={{}}>
            <Typography component="span" sx={linkSx}>
              {segment.label}
            </Typography>
          </Link>
        )
      })}
    </MuiBreadcrumbs>
  )
}
