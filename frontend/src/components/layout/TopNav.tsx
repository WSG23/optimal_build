import { useEffect, useMemo, useRef, useState } from 'react'
import {
  Box,
  Button,
  Divider,
  Drawer,
  IconButton,
  List,
  ListItemButton,
  ListItemText,
  Stack,
  Tooltip,
  Typography,
  alpha,
  useMediaQuery,
  useTheme,
} from '@mui/material'
import {
  ChevronLeft as ChevronLeftIcon,
  ChevronRight as ChevronRightIcon,
  Menu as MenuIcon,
  PushPin as PushPinIcon,
  PushPinOutlined as PushPinOutlinedIcon,
} from '@mui/icons-material'
import { Link, useRouterPath } from '../../router'
import { useTranslation } from '../../i18n'
import { TopUtilityMenu } from './TopUtilityMenu'
import { useDeveloperMode } from '../../contexts/useDeveloperMode'
import { useProject } from '../../contexts/useProject'
import { ProjectSelector } from './ProjectSelector'

type NavGroup = {
  title?: string
  items: Array<{ path: string; label: string; description?: string }>
}

const UTILITY_BAR_HEIGHT = 'var(--ob-space-250)'
const NAV_BAR_HEIGHT = 'var(--ob-space-300)'

interface TopNavProps {
  isPinned: boolean
  onTogglePinned: () => void
}

export function TopNav({ isPinned, onTogglePinned }: TopNavProps) {
  const { t } = useTranslation()
  const path = useRouterPath()
  const theme = useTheme()
  const { isDeveloperMode } = useDeveloperMode()
  const { currentProject } = useProject()

  const projectBase = currentProject?.id
    ? `/projects/${currentProject.id}`
    : null

  const hostLabel = useMemo(() => {
    if (typeof window === 'undefined') return 'localhost'
    return window.location.host || 'localhost'
  }, [])

  const navGroups: NavGroup[] = useMemo(() => {
    const groups: NavGroup[] = [
      {
        title: 'CAD',
        items: [
          {
            path: '/cad/upload',
            label: t('nav.upload'),
            description: 'Upload CAD files for analysis',
          },
          {
            path: '/cad/detection',
            label: t('nav.detection'),
            description: 'AI-powered feature detection',
          },
          {
            path: '/cad/pipelines',
            label: t('nav.pipelines'),
            description: 'Processing pipeline status',
          },
        ],
      },
      {
        title: 'Analysis',
        items: [
          {
            path: '/visualizations/intelligence',
            label: t('nav.intelligence'),
            description: 'Market intelligence and insights',
          },
          {
            path: projectBase ? `${projectBase}/feasibility` : '/projects',
            label: t('nav.feasibility'),
            description: 'Development feasibility analysis',
          },
          {
            path: projectBase ? `${projectBase}/finance` : '/projects/finance',
            label: t('nav.finance'),
            description: 'Financial modeling and scenarios',
          },
        ],
      },
      {
        title: 'Field',
        items: [
          {
            path: '/app/capture',
            label: t('nav.capture'),
            description: 'GPS site capture and observations',
          },
        ],
      },
    ]

    if (isDeveloperMode) {
      groups.push({
        title: 'Execution',
        items: [
          {
            path: projectBase
              ? `${projectBase}/due-diligence`
              : '/app/due-diligence',
            label: t('nav.dueDiligence'),
            description: 'Property condition and inspection history',
          },
          {
            path: projectBase ? `${projectBase}/feasibility` : '/projects',
            label: t('nav.assetFeasibility'),
            description: 'Multi-use optimizer and asset modeling',
          },
          {
            path: projectBase ? `${projectBase}/finance` : '/projects',
            label: t('nav.financialControl'),
            description: 'Development economics and financing',
          },
          {
            path: projectBase ? `${projectBase}/phases` : '/projects',
            label: t('nav.phaseManagement'),
            description: 'Multi-phase development sequencing',
          },
          {
            path: projectBase ? `${projectBase}/team` : '/projects',
            label: t('nav.teamCoordination'),
            description: 'Consultant coordination and approvals',
          },
          {
            path: projectBase ? `${projectBase}/regulatory` : '/projects',
            label: t('nav.regulatoryNavigation'),
            description: 'Authority submissions and compliance',
          },
        ],
      })
    }

    return groups
  }, [isDeveloperMode, t, projectBase])

  const navRef = useRef<HTMLDivElement | null>(null)
  const [canScrollLeft, setCanScrollLeft] = useState(false)
  const [canScrollRight, setCanScrollRight] = useState(false)
  const [mobileDrawerOpen, setMobileDrawerOpen] = useState(false)
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'))
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
    // Reveal on any pin state change so the user sees the transition.
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

  const renderItem = (item: {
    path: string
    label: string
    description?: string
  }) => {
    const isActive = path === item.path || path.startsWith(`${item.path}/`)
    const button = (
      <Button
        key={`${item.path}-${item.label}`}
        component={Link}
        to={item.path}
        variant="text"
        sx={{
          justifyContent: 'center',
          color: isActive ? 'var(--ob-color-brand-primary)' : 'text.secondary',
          bgcolor: 'transparent',
          borderRadius: 0,
          px: 'var(--ob-space-150)',
          py: 'var(--ob-space-100)',
          textTransform: 'uppercase',
          fontWeight: isActive ? 800 : 600,
          fontSize: 'var(--ob-font-size-xs)',
          letterSpacing: 'var(--ob-letter-spacing-wider)',
          whiteSpace: 'nowrap',
          position: 'relative',
          textShadow: isActive ? 'none' : 'none',
          '&:hover': {
            bgcolor: 'transparent',
            color: isActive ? 'var(--ob-color-brand-primary)' : 'text.primary',
          },
          '&::after': isActive
            ? {
                content: '""',
                position: 'absolute',
                bottom: '-4px',
                left: 0,
                right: 0,
                height: '2px',
                bgcolor: 'var(--ob-color-brand-primary)',
                boxShadow: 'none',
              }
            : {},
        }}
      >
        {item.label}
      </Button>
    )
    if (item.description) {
      return (
        <Tooltip
          key={`${item.path}-${item.label}`}
          title={item.description}
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
          tabIndex={0}
          role="button"
          aria-label="Reveal navigation"
          onMouseEnter={reveal}
          onFocus={reveal}
          sx={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            height: 'var(--ob-space-075)',
            zIndex: 'var(--ob-z-fixed)',
            background: 'transparent',
            '&:focus-visible': {
              outline: '2px solid var(--ob-color-brand-primary)',
              outlineOffset: -2,
            },
          }}
        />
      )}

      <Box
        component="header"
        aria-expanded={isPinned || isRevealed}
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
            sx={{ display: { xs: 'none', sm: 'flex' } }}
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
                    borderRadius: 'var(--ob-radius-sm)',
                    border: '1px solid var(--ob-color-brand-primary)',
                    boxShadow: 'none',
                    bgcolor: 'var(--ob-color-brand-muted)',
                  }}
                >
                  <Box
                    component="span"
                    sx={{
                      color: 'var(--ob-color-brand-primary)',
                      fontSize: 'var(--ob-font-size-md)',
                      lineHeight: 1,
                    }}
                  >
                    ⬡
                  </Box>
                </Box>
                <Typography
                  component="span"
                  sx={{
                    color: 'var(--ob-color-brand-primary)',
                    textShadow: 'none',
                    fontWeight: 700,
                    letterSpacing: 'var(--ob-letter-spacing-wider)',
                    fontSize: 'var(--ob-font-size-md)',
                    lineHeight: 1,
                  }}
                >
                  OPTIMAL BUILD
                </Typography>
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
                            fontWeight: 700,
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
              }}
            >
              <ProjectSelector />
              <TopUtilityMenu />
            </Box>
          </Stack>
        </Box>
      </Box>

      <Drawer
        anchor="left"
        open={mobileDrawerOpen}
        onClose={() => setMobileDrawerOpen(false)}
        PaperProps={{
          sx: {
            width: 280,
            bgcolor: 'background.default',
            borderRight: 'var(--ob-border-fine)',
          },
        }}
      >
        <Box
          sx={{
            p: 'var(--ob-space-150)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <Typography
            sx={{
              fontWeight: 700,
              fontSize: 'var(--ob-font-size-sm)',
              color: 'var(--ob-color-brand-primary)',
              letterSpacing: '0.1em',
              textTransform: 'uppercase',
            }}
          >
            OPTIMAL BUILD
          </Typography>
          <IconButton
            aria-label="Close navigation"
            onClick={() => setMobileDrawerOpen(false)}
            size="small"
            sx={{ color: 'text.secondary' }}
          >
            <ChevronLeftIcon fontSize="small" />
          </IconButton>
        </Box>
        <Divider />
        <List sx={{ pt: 'var(--ob-space-050)' }}>
          {navGroups.map((group) => (
            <Box key={group.title ?? 'default'}>
              {group.title && (
                <Typography
                  sx={{
                    px: 'var(--ob-space-100)',
                    pt: 'var(--ob-space-100)',
                    pb: 'var(--ob-space-025)',
                    fontSize: 'var(--ob-font-size-2xs)',
                    fontWeight: 700,
                    color: 'text.disabled',
                    textTransform: 'uppercase',
                    letterSpacing: '0.1em',
                  }}
                >
                  {group.title}
                </Typography>
              )}
              {group.items.map((item) => (
                <ListItemButton
                  key={item.path}
                  component={Link}
                  to={item.path}
                  selected={path === item.path}
                  onClick={() => setMobileDrawerOpen(false)}
                  sx={{
                    borderRadius: 'var(--ob-radius-sm)',
                    mx: 'var(--ob-space-050)',
                    '&.Mui-selected': {
                      bgcolor: 'var(--ob-color-action-hover)',
                    },
                  }}
                >
                  <ListItemText
                    primary={item.label}
                    primaryTypographyProps={{
                      fontSize: 'var(--ob-font-size-sm)',
                      fontWeight: 600,
                    }}
                    secondary={item.description}
                    secondaryTypographyProps={{
                      fontSize: 'var(--ob-font-size-xs)',
                    }}
                  />
                </ListItemButton>
              ))}
            </Box>
          ))}
        </List>
      </Drawer>
    </>
  )
}
