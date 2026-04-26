import { Suspense, lazy, useEffect, useState } from 'react'
import { ErrorBoundary } from '../ErrorBoundary'
import { NavErrorFallback } from './NavErrorFallback'
import { MobileNavDrawer } from './MobileNavDrawer'
import {
  Box,
  Button,
  IconButton,
  Stack,
  Tooltip,
  Typography,
  alpha,
  useMediaQuery,
  useTheme,
} from '@mui/material'
import ChevronLeftIcon from '@mui/icons-material/ChevronLeft'
import ChevronRightIcon from '@mui/icons-material/ChevronRight'
import MenuIcon from '@mui/icons-material/Menu'
import PushPinIcon from '@mui/icons-material/PushPin'
import PushPinOutlinedIcon from '@mui/icons-material/PushPinOutlined'
import SearchIcon from '@mui/icons-material/Search'
import { Link, useRouterPath } from '../../router'
import { useDeveloperMode } from '../../contexts/useDeveloperMode'
import { useProject } from '../../contexts/useProject'
import { useNavGroups } from '../../hooks/useNavGroups'
import { useNavReveal } from '../../hooks/useNavReveal'
import { useScrollAffordance } from '../../hooks/useScrollAffordance'

const ProjectSelector = lazy(async () => {
  const module = await import('./ProjectSelector')
  return { default: module.ProjectSelector }
})

const TopUtilityMenu = lazy(async () => {
  const module = await import('./TopUtilityMenu')
  return { default: module.TopUtilityMenu }
})

const NAV_BAR_HEIGHT = 'var(--ob-space-300)'

interface TopNavProps {
  isPinned: boolean
  onTogglePinned: () => void
}

export function TopNav({ isPinned, onTogglePinned }: TopNavProps) {
  const path = useRouterPath()
  const theme = useTheme()
  const { isDeveloperMode } = useDeveloperMode()
  const { currentProject } = useProject()
  const navGroups = useNavGroups()
  const prefersReducedMotion = useMediaQuery('(prefers-reduced-motion: reduce)')

  const { isRevealed, reveal, scheduleHide } = useNavReveal({
    isPinned,
  })
  const { navRef, canScrollLeft, canScrollRight, scroll, checkScroll } =
    useScrollAffordance()

  const [isOnline, setIsOnline] = useState(
    () => typeof navigator === 'undefined' || navigator.onLine,
  )

  useEffect(() => {
    const goOnline = () => setIsOnline(true)
    const goOffline = () => setIsOnline(false)
    window.addEventListener('online', goOnline)
    window.addEventListener('offline', goOffline)
    return () => {
      window.removeEventListener('online', goOnline)
      window.removeEventListener('offline', goOffline)
    }
  }, [])

  const projectBase = currentProject?.id
    ? `/projects/${currentProject.id}`
    : null

  // First-use tooltip for command palette
  const [cmdkTooltipOpen, setCmdkTooltipOpen] = useState(() => {
    if (typeof window === 'undefined') return false
    return !window.localStorage.getItem('ob_cmdk_seen')
  })

  useEffect(() => {
    if (!cmdkTooltipOpen) return
    const timer = window.setTimeout(() => {
      window.localStorage.setItem('ob_cmdk_seen', 'true')
      setCmdkTooltipOpen(false)
    }, 5000)
    return () => window.clearTimeout(timer)
  }, [cmdkTooltipOpen])

  // Dismiss first-use tooltip when command palette is opened
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        if (cmdkTooltipOpen) {
          window.localStorage.setItem('ob_cmdk_seen', 'true')
          setCmdkTooltipOpen(false)
        }
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [cmdkTooltipOpen])

  const [mobileDrawerOpen, setMobileDrawerOpen] = useState(false)
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'))

  const renderItem = (item: {
    path: string
    label: string
    description?: string
  }) => {
    const isActive = path === item.path || path.startsWith(`${item.path}/`)
    const needsProject = !projectBase && item.path === '/projects'
    const tooltipTitle = needsProject
      ? 'Select a project first'
      : (item.description ?? '')
    const button = (
      <Button
        key={`${item.path}-${item.label}`}
        component={Link}
        to={item.path}
        variant="text"
        disabled={needsProject}
        sx={{
          justifyContent: 'center',
          color: isActive ? 'var(--ob-color-brand-primary)' : 'text.secondary',
          bgcolor: 'transparent',
          borderRadius: 0,
          px: 'var(--ob-space-150)',
          py: 'var(--ob-space-050)',
          textTransform: 'uppercase',
          fontWeight: isActive ? 800 : 600,
          fontSize: 'var(--ob-font-size-xs)',
          letterSpacing: 'var(--ob-letter-spacing-wider)',
          whiteSpace: 'nowrap',
          position: 'relative',
          '&:focus-visible': {
            outline: '2px solid var(--ob-color-brand-primary)',
            outlineOffset: 2,
          },
          '&:hover': {
            bgcolor: 'transparent',
            color: isActive ? 'var(--ob-color-brand-primary)' : 'text.primary',
          },
          '&.Mui-disabled': {
            color: 'text.disabled',
            pointerEvents: 'auto',
            cursor: 'not-allowed',
          },
          '&::after': isActive
            ? {
                content: '""',
                position: 'absolute',
                bottom: 'calc(-1 * var(--ob-space-025))',
                left: 0,
                right: 0,
                height: '2px',
                bgcolor: 'var(--ob-color-brand-primary)',
              }
            : {},
        }}
      >
        {item.label}
      </Button>
    )
    if (tooltipTitle) {
      return (
        <Tooltip
          key={`${item.path}-${item.label}`}
          title={tooltipTitle}
          placement="bottom"
          enterDelay={400}
          arrow
        >
          {button}
        </Tooltip>
      )
    }
    return button
  }

  const headerTransition = prefersReducedMotion
    ? 'none'
    : isPinned
      ? 'none'
      : 'transform 240ms ease'

  return (
    <>
      {!isPinned && (
        <Box
          component="button"
          aria-label="Reveal navigation"
          aria-expanded={isRevealed}
          onMouseEnter={reveal}
          onTouchStart={reveal}
          onFocus={reveal}
          onKeyDown={(e: React.KeyboardEvent) => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault()
              reveal()
            }
          }}
          sx={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            height: 'var(--ob-space-075)',
            zIndex: 'var(--ob-z-fixed)',
            background: 'transparent',
            border: 'none',
            cursor: 'pointer',
            padding: 0,
            '@media (pointer: coarse)': {
              height: 44,
            },
            '&:focus-visible': {
              outline: '2px solid var(--ob-color-brand-primary)',
              outlineOffset: -2,
            },
          }}
        />
      )}

      <Box
        component="header"
        onMouseEnter={() => {
          if (!isPinned) reveal()
        }}
        onMouseLeave={() => {
          if (!isPinned) scheduleHide()
        }}
        onFocusCapture={() => {
          if (!isPinned) reveal()
        }}
        onBlurCapture={(e) => {
          if (!isPinned && !e.currentTarget.contains(e.relatedTarget)) {
            scheduleHide()
          }
        }}
        sx={{
          position: isPinned ? 'sticky' : 'fixed',
          top: 0,
          left: 0,
          right: 0,
          zIndex: 'var(--ob-z-fixed)',
          transform:
            isPinned || isRevealed ? 'translateY(0)' : 'translateY(-100%)',
          transition: headerTransition,
          pointerEvents: isPinned || isRevealed ? 'auto' : 'none',
        }}
      >
        <Box
          component="nav"
          aria-label="Primary"
          sx={{
            height: NAV_BAR_HEIGHT,
            borderBottom: 'var(--ob-border-fine)',
            bgcolor: 'background.default',
          }}
        >
          <Stack
            direction="row"
            alignItems="center"
            sx={{
              height: '100%',
              px: 'var(--ob-space-200)',
              gap: 'var(--ob-space-150)',
              // Mobile: reduce horizontal padding
              '@media (max-width: 600px)': {
                px: 'var(--ob-space-100)',
                gap: 'var(--ob-space-075)',
              },
            }}
          >
            <Button
              component={Link}
              to="/"
              variant="text"
              sx={{
                px: 'var(--ob-space-100)',
                py: 'var(--ob-space-050)',
                borderRadius: 'var(--ob-radius-xs)',
                textTransform: 'none',
                whiteSpace: 'nowrap',
                minWidth: 0,
                '&:hover': {
                  bgcolor: 'var(--ob-color-brand-muted)',
                },
              }}
            >
              <Stack
                direction="row"
                alignItems="center"
                spacing="var(--ob-space-075)"
              >
                <Box
                  sx={{
                    width: 'var(--ob-space-250)',
                    height: 'var(--ob-space-250)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    borderRadius: 'var(--ob-radius-xs)',
                    border: '1px solid var(--ob-color-brand-primary)',
                    bgcolor: 'var(--ob-color-brand-muted)',
                  }}
                >
                  <Typography
                    component="span"
                    sx={{
                      color: 'var(--ob-color-brand-primary)',
                      fontFamily: 'var(--ob-font-family-mono)',
                      fontSize: 'var(--ob-font-size-xs)',
                      fontWeight: 'var(--ob-font-weight-bold)',
                      lineHeight: 'var(--ob-line-height-none)',
                      letterSpacing: '-0.02em',
                    }}
                  >
                    OB
                  </Typography>
                </Box>
                <Typography
                  component="span"
                  sx={{
                    display: { xs: 'none', sm: 'inline' },
                    color: 'var(--ob-color-brand-primary)',
                    fontWeight: 'var(--ob-font-weight-bold)',
                    letterSpacing: 'var(--ob-letter-spacing-wider)',
                    fontSize: 'var(--ob-font-size-md)',
                    lineHeight: 'var(--ob-line-height-none)',
                  }}
                >
                  OPTIMAL BUILD
                </Typography>
                {isDeveloperMode && (
                  <Box
                    component="span"
                    sx={{
                      fontSize: 'var(--ob-font-size-2xs)',
                      fontFamily: 'var(--ob-font-family-mono)',
                      fontWeight: 'var(--ob-font-weight-bold)',
                      lineHeight: 'var(--ob-line-height-none)',
                      px: 'var(--ob-space-050)',
                      py: '1px',
                      borderRadius: 'var(--ob-radius-xs)',
                      border: 'var(--ob-border-fine)',
                      color: 'text.secondary',
                      letterSpacing: 'var(--ob-letter-spacing-wider)',
                    }}
                  >
                    ADV
                  </Box>
                )}
                <Box
                  aria-label={isOnline ? 'Connected' : 'Offline'}
                  sx={{
                    width: '6px',
                    height: '6px',
                    borderRadius: 'var(--ob-radius-pill)',
                    bgcolor: isOnline ? 'success.main' : 'warning.main',
                    flexShrink: 0,
                  }}
                />
              </Stack>
            </Button>

            {!isMobile ? (
              <Box
                sx={{
                  position: 'relative',
                  flex: 1,
                  minWidth: 0,
                  height: '100%',
                  display: 'flex',
                  alignItems: 'center',
                }}
              >
                {/* Left scroll affordance */}
                <Box
                  sx={{
                    position: 'absolute',
                    left: 0,
                    top: 0,
                    bottom: 0,
                    display: 'flex',
                    alignItems: 'center',
                    pr: 'var(--ob-space-075)',
                    background: `linear-gradient(90deg, ${alpha(theme.palette.background.default, 0.95)} 0%, ${alpha(theme.palette.background.default, 0.85)} 60%, ${alpha(theme.palette.background.default, 0)} 100%)`,
                    opacity: canScrollLeft ? 1 : 0,
                    pointerEvents: canScrollLeft ? 'auto' : 'none',
                    transition: 'opacity 200ms ease',
                    zIndex: 'calc(var(--ob-z-base) + 1)',
                  }}
                >
                  <IconButton
                    aria-label="Scroll navigation left"
                    onClick={() => scroll('left')}
                    size="small"
                    sx={{
                      borderRadius: 'var(--ob-radius-xs)',
                      border: 1,
                      borderColor: alpha(theme.palette.divider, 0.4),
                      bgcolor: alpha(theme.palette.background.paper, 0.45),
                      backdropFilter: 'blur(var(--ob-blur-sm))',
                      '&:hover': {
                        bgcolor: alpha(theme.palette.background.paper, 0.65),
                      },
                    }}
                  >
                    <ChevronLeftIcon fontSize="small" />
                  </IconButton>
                </Box>

                <Box
                  ref={navRef}
                  onScroll={checkScroll}
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    height: '100%',
                    minWidth: 0,
                    gap: 'var(--ob-space-150)',
                    overflowX: 'auto',
                    scrollbarWidth: 'none',
                    scrollBehavior: 'smooth',
                    '&::-webkit-scrollbar': { display: 'none' },
                    px: 'var(--ob-space-025)',
                  }}
                >
                  {navGroups.map((group, idx) => (
                    <Stack
                      key={group.items.map((item) => item.path).join('|')}
                      direction="row"
                      alignItems="center"
                      sx={{ gap: 'var(--ob-space-050)', flexShrink: 0 }}
                    >
                      {group.title && (
                        <Typography
                          component="span"
                          sx={{
                            fontSize: 'var(--ob-font-size-2xs)',
                            fontFamily: 'var(--ob-font-family-mono)',
                            fontWeight: 'var(--ob-font-weight-bold)',
                            color: 'text.disabled',
                            textTransform: 'uppercase',
                            letterSpacing: 'var(--ob-letter-spacing-widest)',
                            pr: 'var(--ob-space-050)',
                            pl: idx > 0 ? 'var(--ob-space-050)' : 0,
                            borderLeft: idx > 0 ? 1 : 0,
                            borderColor: alpha(theme.palette.divider, 0.2),
                            whiteSpace: 'nowrap',
                            userSelect: 'none',
                          }}
                        >
                          {group.title}
                        </Typography>
                      )}
                      {group.items.map(renderItem)}
                    </Stack>
                  ))}
                </Box>

                {/* Right scroll affordance */}
                <Box
                  sx={{
                    position: 'absolute',
                    right: 0,
                    top: 0,
                    bottom: 0,
                    display: 'flex',
                    alignItems: 'center',
                    pl: 'var(--ob-space-075)',
                    background: `linear-gradient(270deg, ${alpha(theme.palette.background.default, 0.95)} 0%, ${alpha(theme.palette.background.default, 0.85)} 60%, ${alpha(theme.palette.background.default, 0)} 100%)`,
                    opacity: canScrollRight ? 1 : 0,
                    pointerEvents: canScrollRight ? 'auto' : 'none',
                    transition: 'opacity 200ms ease',
                    zIndex: 'calc(var(--ob-z-base) + 1)',
                  }}
                >
                  <IconButton
                    aria-label="Scroll navigation right"
                    onClick={() => scroll('right')}
                    size="small"
                    sx={{
                      borderRadius: 'var(--ob-radius-xs)',
                      border: 1,
                      borderColor: alpha(theme.palette.divider, 0.4),
                      bgcolor: alpha(theme.palette.background.paper, 0.45),
                      backdropFilter: 'blur(var(--ob-blur-sm))',
                      '&:hover': {
                        bgcolor: alpha(theme.palette.background.paper, 0.65),
                      },
                    }}
                  >
                    <ChevronRightIcon fontSize="small" />
                  </IconButton>
                </Box>
              </Box>
            ) : (
              <IconButton
                aria-label="Open navigation menu"
                onClick={() => setMobileDrawerOpen(true)}
                sx={{
                  color: 'text.secondary',
                  ml: 'var(--ob-space-050)',
                }}
              >
                <MenuIcon />
              </IconButton>
            )}

            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                height: '100%',
                pl: 'var(--ob-space-150)',
                borderLeft: 1,
                borderColor: alpha(theme.palette.divider, 0.25),
                gap: 'var(--ob-space-100)',
                // Mobile: tighten utility cluster
                '@media (max-width: 600px)': {
                  pl: 'var(--ob-space-075)',
                  gap: 'var(--ob-space-050)',
                  ml: 'auto',
                },
              }}
            >
              <Tooltip
                title={
                  cmdkTooltipOpen
                    ? 'Search anything with \u2318K'
                    : 'Search commands (\u2318K)'
                }
                open={cmdkTooltipOpen || undefined}
                placement="bottom"
                arrow={cmdkTooltipOpen}
              >
                <Button
                  aria-label="Open command palette"
                  onClick={() => {
                    if (cmdkTooltipOpen) {
                      window.localStorage.setItem('ob_cmdk_seen', 'true')
                      setCmdkTooltipOpen(false)
                    }
                    window.dispatchEvent(
                      new KeyboardEvent('keydown', {
                        key: 'k',
                        metaKey: true,
                        bubbles: true,
                      }),
                    )
                  }}
                  variant="text"
                  size="small"
                  sx={{
                    minWidth: 0,
                    px: 'var(--ob-space-075)',
                    py: 'var(--ob-space-025)',
                    borderRadius: 'var(--ob-radius-xs)',
                    border: 'var(--ob-border-fine)',
                    color: 'text.secondary',
                    fontSize: 'var(--ob-font-size-xs)',
                    gap: 'var(--ob-space-050)',
                    textTransform: 'none',
                    '&:hover': {
                      color: 'text.primary',
                      borderColor: alpha(theme.palette.text.primary, 0.2),
                    },
                  }}
                >
                  <SearchIcon sx={{ fontSize: 14 }} />
                  <Box
                    component="kbd"
                    sx={{
                      fontSize: 'var(--ob-font-size-2xs)',
                      fontFamily: 'var(--ob-font-family-mono)',
                      opacity: 0.7,
                      // Hide keyboard hint on mobile
                      display: { xs: 'none', sm: 'inline' },
                    }}
                  >
                    ⌘K
                  </Box>
                </Button>
              </Tooltip>
              <ErrorBoundary fallback={<NavErrorFallback />}>
                <Suspense
                  fallback={
                    <Box
                      sx={{
                        width: 'var(--ob-space-250)',
                        height: 'var(--ob-space-250)',
                        borderRadius: 'var(--ob-radius-xs)',
                        bgcolor: 'action.hover',
                        animation: 'ob-fade-in 1s ease infinite alternate',
                      }}
                    />
                  }
                >
                  <ProjectSelector />
                  <TopUtilityMenu />
                </Suspense>
              </ErrorBoundary>
              <Tooltip
                title={isPinned ? 'Unpin header (auto-hide)' : 'Pin header'}
              >
                <IconButton
                  aria-label={isPinned ? 'Unpin header' : 'Pin header'}
                  onClick={onTogglePinned}
                  size="small"
                  sx={{
                    borderRadius: 'var(--ob-radius-xs)',
                    color: isPinned ? 'text.secondary' : 'primary.main',
                    '&:hover': {
                      color: isPinned ? 'text.primary' : 'primary.main',
                    },
                    // Pin/unpin is a desktop power-user feature
                    display: { xs: 'none', sm: 'inline-flex' },
                  }}
                >
                  {isPinned ? (
                    <PushPinIcon sx={{ fontSize: 16 }} />
                  ) : (
                    <PushPinOutlinedIcon sx={{ fontSize: 16 }} />
                  )}
                </IconButton>
              </Tooltip>
            </Box>
          </Stack>
        </Box>
      </Box>

      <MobileNavDrawer
        open={mobileDrawerOpen}
        onClose={() => setMobileDrawerOpen(false)}
        navGroups={navGroups}
        currentPath={path}
      />
    </>
  )
}
