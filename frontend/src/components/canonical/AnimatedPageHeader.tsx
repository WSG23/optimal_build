import { Box, Typography, Breadcrumbs, Link, Stack } from '@mui/material'
import { NavigateNext } from '@mui/icons-material'
import type { ReactNode } from 'react'

interface AnimatedPageHeaderProps {
  title: string
  subtitle?: string
  breadcrumbs?: Array<{ label: string; href?: string }>
  actions?: ReactNode
}

export function AnimatedPageHeader({
  title,
  subtitle,
  breadcrumbs = [],
  actions,
}: AnimatedPageHeaderProps) {
  return (
    <Box
      sx={{
        mb: 4,
        animation:
          'ob-slide-down-fade var(--ob-motion-header-duration-slow) var(--ob-motion-header-ease) both',
        '@media (prefers-reduced-motion: reduce)': {
          animation: 'none',
        },
      }}
    >
      {breadcrumbs.length > 0 && (
        <Breadcrumbs
          separator={<NavigateNext fontSize="small" />}
          aria-label="breadcrumb"
          sx={{ mb: 2 }}
        >
          {breadcrumbs.map((crumb, idx) => {
            const isLast = idx === breadcrumbs.length - 1
            return (
              <Link
                key={crumb.label}
                underline="hover"
                color={isLast ? 'text.primary' : 'inherit'}
                href={crumb.href}
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  fontWeight: isLast
                    ? 'var(--ob-font-weight-semibold)'
                    : 'var(--ob-font-weight-regular)',
                  cursor: isLast ? 'default' : 'pointer',
                }}
              >
                {crumb.label}
              </Link>
            )
          })}
        </Breadcrumbs>
      )}

      <Stack
        direction="row"
        justifyContent="space-between"
        alignItems="flex-end"
      >
        <Box>
          <Typography
            variant="h3"
            sx={{
              fontWeight: 'var(--ob-font-weight-bold)',
              letterSpacing: 'var(--ob-letter-spacing-tighter)',
              background:
                'linear-gradient(45deg, var(--ob-color-text-primary), var(--ob-color-text-secondary))',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              mb: 1,
            }}
          >
            {title}
          </Typography>
          {subtitle && (
            <Typography
              variant="body1"
              color="text.secondary"
              sx={{ maxWidth: 800 }}
            >
              {subtitle}
            </Typography>
          )}
        </Box>

        {actions && <Box sx={{ display: 'flex', gap: 2 }}>{actions}</Box>}
      </Stack>
    </Box>
  )
}
