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
        animation: 'slideDownFade 0.5s ease-out forwards',
        '@keyframes slideDownFade': {
          from: { opacity: 0, transform: 'translateY(-20px)' },
          to: { opacity: 1, transform: 'translateY(0)' },
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
                  fontWeight: isLast ? 600 : 400,
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
              fontWeight: 700,
              letterSpacing: '-0.02em',
              background: 'linear-gradient(45deg, #111827, #4B5563)',
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
