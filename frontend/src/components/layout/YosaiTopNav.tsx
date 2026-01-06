import { useEffect, useMemo, useRef, useState } from 'react'
import {
  Box,
  Button,
  IconButton,
  Stack,
  Tooltip,
  Typography,
  alpha,
  useTheme,
} from '@mui/material'
import {
  ChevronLeft as ChevronLeftIcon,
  ChevronRight as ChevronRightIcon,
  PushPin as PushPinIcon,
  PushPinOutlined as PushPinOutlinedIcon,
} from '@mui/icons-material'
import { Link, useRouterPath } from '../../router'
import { useTranslation } from '../../i18n'
import { TopUtilityMenu } from './TopUtilityMenu'
import { useDeveloperMode } from '../../contexts/useDeveloperMode'

type NavGroup = {
  items: Array<{ path: string; label: string }>
}

const UTILITY_BAR_HEIGHT = 'var(--ob-space-250)'
const NAV_BAR_HEIGHT = 'var(--ob-space-300)'

interface YosaiTopNavProps {
  isPinned: boolean
  onTogglePinned: () => void
}

export function YosaiTopNav({ isPinned, onTogglePinned }: YosaiTopNavProps) {
  const { t } = useTranslation()
  const path = useRouterPath()
  const theme = useTheme()
  const { isDeveloperMode } = useDeveloperMode()

  const hostLabel = useMemo(() => {
    if (typeof window === 'undefined') return 'localhost'
    return window.location.host || 'localhost'
  }, [])

  const navGroups: NavGroup[] = useMemo(() => {
    const groups: NavGroup[] = [
      {
        items: [
          { path: '/cad/upload', label: t('nav.upload') },
          { path: '/cad/detection', label: t('nav.detection') },
          { path: '/cad/pipelines', label: t('nav.pipelines') },
        ],
      },
      {
        items: [
          {
            path: '/visualizations/intelligence',
            label: t('nav.intelligence'),
          },
          { path: '/feasibility', label: t('nav.feasibility') },
          { path: '/finance', label: t('nav.finance') },
        ],
      },
      // Unified capture - single entry point for both agents and developers
      {
        items: [{ path: '/app/capture', label: t('nav.capture') }],
      },
    ]

    if (isDeveloperMode) {
      groups.push({
        items: [
          {
            path: '/app/asset-feasibility',
            label: t('nav.assetFeasibility'),
          },
          {
            path: '/app/financial-control',
            label: t('nav.financialControl'),
          },
          { path: '/app/phase-management', label: t('nav.phaseManagement') },
          { path: '/app/team-coordination', label: t('nav.teamCoordination') },
          { path: '/app/regulatory', label: t('nav.regulatoryNavigation') },
        ],
      })
    }

    return groups
  }, [isDeveloperMode, t])

  const navRef = useRef<HTMLDivElement | null>(null)
  const [canScrollLeft, setCanScrollLeft] = useState(false)
  const [canScrollRight, setCanScrollRight] = useState(false)
  const [isRevealed, setIsRevealed] = useState(false)
  const hideTimerRef = useRef<number | null>(null)

  const checkScroll = () => {
    const node = navRef.current
    if (!node) return

    const { scrollLeft, scrollWidth, clientWidth } = node
    setCanScrollLeft(scrollLeft > 0)
    setCanScrollRight(scrollLeft < scrollWidth - clientWidth - 1)
  }

  useEffect(() => {
    checkScroll()
    if (typeof window === 'undefined') return
    window.addEventListener('resize', checkScroll)
    return () => window.removeEventListener('resize', checkScroll)
  }, [])

  useEffect(() => {
    if (isPinned) {
      setIsRevealed(true)
      return
    }
    // Keep the ribbon visible immediately after unpin so the user can see the
    // state change; it will auto-hide on mouse leave.
    setIsRevealed(true)
  }, [isPinned])

  const scroll = (direction: 'left' | 'right') => {
    const node = navRef.current
    if (!node) return

    const scrollAmount = 240
    node.scrollBy({
      left: direction === 'left' ? -scrollAmount : scrollAmount,
      behavior: 'smooth',
    })
  }

  const renderItem = (item: { path: string; label: string }) => {
    const isActive = path === item.path || path.startsWith(`${item.path}/`)
    return (
      <Button
        key={item.path}
        component={Link}
        to={item.path}
        variant="text"
        sx={{
          justifyContent: 'center',
          color: isActive ? 'var(--ob-color-neon-cyan)' : 'text.secondary',
          bgcolor: 'transparent', // Always transparent - no filled background
          borderRadius: 0,
          px: 'var(--ob-space-150)',
          py: 'var(--ob-space-100)',
          textTransform: 'uppercase',
          fontWeight: isActive ? 800 : 600,
          fontSize: 'var(--ob-font-size-2xs)', // 10px - matches V3 reference
          letterSpacing: 'var(--ob-letter-spacing-wider)',
          whiteSpace: 'nowrap',
          position: 'relative',
          textShadow: isActive ? 'var(--ob-glow-neon-text)' : 'none',
          '&:hover': {
            bgcolor: 'transparent', // Keep transparent on hover
            color: isActive ? 'var(--ob-color-neon-cyan)' : 'text.primary',
          },
          // Glowing underline for active state - positioned below the nav bar
          '&::after': isActive
            ? {
                content: '""',
                position: 'absolute',
                bottom: '-4px',
                left: 0,
                right: 0,
                height: '2px',
                bgcolor: 'var(--ob-color-neon-cyan)',
                boxShadow: '0 0 8px var(--ob-color-neon-cyan)',
              }
            : {},
        }}
      >
        {item.label}
      </Button>
    )
  }

  const cancelHide = () => {
    if (typeof window === 'undefined') return
    if (hideTimerRef.current === null) return
    window.clearTimeout(hideTimerRef.current)
    hideTimerRef.current = null
  }

  const scheduleHide = () => {
    if (typeof window === 'undefined') return
    cancelHide()
    hideTimerRef.current = window.setTimeout(() => {
      setIsRevealed(false)
      hideTimerRef.current = null
    }, 350)
  }

  const reveal = () => {
    cancelHide()
    setIsRevealed(true)
  }

  return (
    <>
      {!isPinned && (
        <Box
          aria-hidden
          onMouseEnter={reveal}
          sx={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            height: 'var(--ob-space-075)',
            zIndex: 'var(--ob-z-fixed)',
            background: 'transparent',
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
        sx={{
          position: isPinned ? 'sticky' : 'fixed',
          top: 0,
          left: 0,
          right: 0,
          zIndex: 'var(--ob-z-fixed)',
          transform:
            isPinned || isRevealed ? 'translateY(0)' : 'translateY(-100%)',
          transition: isPinned ? 'none' : 'transform 240ms ease',
          pointerEvents: isPinned || isRevealed ? 'auto' : 'none',
        }}
      >
        <Box
          className="ob-glass"
          sx={{
            height: UTILITY_BAR_HEIGHT,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            px: 'var(--ob-space-200)',
            borderBottom: 'var(--ob-border-fine)',
          }}
        >
          <Stack
            direction="row"
            alignItems="center"
            spacing="var(--ob-space-100)"
          >
            <Box
              sx={{
                width: 'var(--ob-space-025)',
                height: 'var(--ob-space-025)',
                borderRadius: 'var(--ob-radius-pill)',
                bgcolor: 'success.main',
              }}
            />
            <Typography
              sx={{
                color: 'text.secondary',
                fontFamily: 'var(--ob-font-family-mono)',
                fontSize: 'var(--ob-font-size-xs)',
                letterSpacing: 'var(--ob-letter-spacing-wider)',
              }}
            >
              {hostLabel}
            </Typography>
          </Stack>

          <Tooltip title={isPinned ? 'Unpin header (auto-hide)' : 'Pin header'}>
            <IconButton
              aria-label={isPinned ? 'Unpin header' : 'Pin header'}
              onClick={onTogglePinned}
              sx={{
                borderRadius: 'var(--ob-radius-pill)',
                border: 1,
                borderColor: alpha(theme.palette.divider, 0.2),
                width: 'var(--ob-space-250)',
                height: 'var(--ob-space-250)',
                color: isPinned ? 'text.secondary' : 'primary.main',
                background: alpha(theme.palette.background.paper, 0.05),
                backdropFilter: 'blur(var(--ob-blur-sm))',
                '&:hover': {
                  color: isPinned ? 'text.primary' : 'primary.main',
                  background: alpha(theme.palette.text.primary, 0.05),
                  borderColor: alpha(theme.palette.text.primary, 0.2),
                },
              }}
            >
              {isPinned ? (
                <PushPinIcon fontSize="small" />
              ) : (
                <PushPinOutlinedIcon fontSize="small" />
              )}
            </IconButton>
          </Tooltip>
        </Box>

        <Box
          component="nav"
          aria-label="Primary"
          className="ob-glass"
          sx={{
            height: NAV_BAR_HEIGHT,
            borderBottom: 'var(--ob-border-fine)',
          }}
        >
          <Stack
            direction="row"
            alignItems="center"
            sx={{
              height: '100%',
              px: 'var(--ob-space-200)',
              gap: 'var(--ob-space-150)',
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
                  bgcolor: 'var(--ob-color-neon-cyan-dim)',
                },
              }}
            >
              <Stack direction="row" alignItems="center" spacing={1.5}>
                {/* Neon CPU Icon */}
                <Box
                  sx={{
                    width: 'var(--ob-space-250)',
                    height: 'var(--ob-space-250)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    borderRadius: 'var(--ob-radius-sm)',
                    border: '1px solid var(--ob-color-neon-cyan)',
                    boxShadow: 'var(--ob-glow-neon-cyan)',
                    bgcolor: 'var(--ob-color-neon-cyan-dim)',
                  }}
                >
                  <Box
                    component="span"
                    sx={{
                      color: 'var(--ob-color-neon-cyan)',
                      fontSize: 'var(--ob-font-size-md)',
                      lineHeight: 1,
                    }}
                  >
                    ⬡
                  </Box>
                </Box>
                <Stack direction="row" alignItems="baseline" spacing={1}>
                  <Typography
                    component="span"
                    sx={{
                      color: 'var(--ob-color-neon-cyan)',
                      textShadow: 'var(--ob-glow-neon-text)',
                      fontWeight: 800,
                      letterSpacing: 'var(--ob-letter-spacing-wider)',
                      fontSize: 'var(--ob-font-size-md)',
                    }}
                  >
                    OPTIMAL BUILD
                  </Typography>
                  <Box
                    component="span"
                    className="ob-neon-text"
                    sx={{
                      fontSize: 'var(--ob-font-size-2xs)',
                      fontWeight: 800,
                      border: '1px solid var(--ob-color-neon-cyan-dim)',
                      padding: '2px 6px',
                      borderRadius: 'var(--ob-radius-xs)',
                    }}
                  >
                    V2.5_PRO
                  </Box>
                </Stack>
              </Stack>
            </Button>

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
                    borderRadius: 'var(--ob-radius-pill)',
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
                {navGroups.map((group) => (
                  <Stack
                    key={group.items.map((item) => item.path).join('|')}
                    direction="row"
                    alignItems="center"
                    sx={{ gap: 'var(--ob-space-050)', flexShrink: 0 }}
                  >
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
                    borderRadius: 'var(--ob-radius-pill)',
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

            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                height: '100%',
                pl: 'var(--ob-space-150)',
                borderLeft: 1,
                borderColor: alpha(theme.palette.divider, 0.25),
              }}
            >
              <TopUtilityMenu />
            </Box>
          </Stack>
        </Box>
      </Box>
    </>
  )
}
