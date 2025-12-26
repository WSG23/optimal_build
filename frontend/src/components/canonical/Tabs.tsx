import { Box, SxProps, Theme } from '@mui/material'
import { ReactNode } from 'react'

export interface TabItem {
  /**
   * Unique identifier
   */
  id: string
  /**
   * Tab label
   */
  label: string
  /**
   * Optional icon
   */
  icon?: ReactNode
  /**
   * Disabled state
   */
  disabled?: boolean
}

export interface TabsProps {
  /**
   * Tab definitions
   */
  tabs: TabItem[]
  /**
   * Currently active tab ID
   */
  activeTab: string
  /**
   * Tab change handler
   */
  onTabChange: (tabId: string) => void
  /**
   * Tab variant
   * - 'underline': Bottom border indicator
   * - 'contained': Background indicator
   */
  variant?: 'underline' | 'contained'
  /**
   * Size
   */
  size?: 'sm' | 'md'
  /**
   * Full width tabs
   */
  fullWidth?: boolean
  /**
   * Additional styles
   */
  sx?: SxProps<Theme>
}

/**
 * Tabs - Square Tab Navigation
 *
 * Geometry: 2px border radius (--ob-radius-xs) for contained variant
 * Height: 36px (sm), 40px (md)
 *
 * Clean, geometric tab navigation.
 */
export function Tabs({
  tabs,
  activeTab,
  onTabChange,
  variant = 'underline',
  size = 'md',
  fullWidth = false,
  sx = {},
}: TabsProps) {
  const height = size === 'sm' ? '36px' : '40px'
  const fontSize =
    size === 'sm' ? 'var(--ob-font-size-xs)' : 'var(--ob-font-size-sm)'
  const resolvedSx = Array.isArray(sx) ? sx : [sx]

  return (
    <Box
      role="tablist"
      sx={[
        {
          display: 'flex',
          gap: variant === 'contained' ? 'var(--ob-space-025)' : 0,
          borderBottom:
            variant === 'underline' ? 'var(--ob-divider-strong)' : 'none',
          background:
            variant === 'contained'
              ? 'var(--ob-color-surface-strong)'
              : 'transparent',
          padding: variant === 'contained' ? 'var(--ob-space-025)' : 0,
          borderRadius: variant === 'contained' ? 'var(--ob-radius-sm)' : 0,
          width: fullWidth ? '100%' : 'auto',
        },
        ...resolvedSx,
      ]}
    >
      {tabs.map((tab) => {
        const isActive = tab.id === activeTab

        return (
          <Box
            key={tab.id}
            role="tab"
            aria-selected={isActive}
            aria-disabled={tab.disabled}
            tabIndex={tab.disabled ? -1 : 0}
            onClick={() => !tab.disabled && onTabChange(tab.id)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault()
                if (!tab.disabled) onTabChange(tab.id)
              }
            }}
            sx={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 'var(--ob-space-050)',
              height,
              px: 'var(--ob-space-100)',
              fontSize,
              fontWeight: isActive
                ? 'var(--ob-font-weight-semibold)'
                : 'var(--ob-font-weight-medium)',
              color: isActive
                ? 'var(--ob-color-text-primary)'
                : 'var(--ob-color-text-secondary)',
              cursor: tab.disabled ? 'not-allowed' : 'pointer',
              opacity: tab.disabled ? 0.5 : 1,
              transition: 'all 0.2s ease',
              position: 'relative',
              flex: fullWidth ? 1 : 'none',
              whiteSpace: 'nowrap',
              userSelect: 'none',

              // Underline variant
              ...(variant === 'underline' && {
                borderRadius: 0,
                background: 'transparent',
                marginBottom: '-1px',

                '&::after': {
                  content: '""',
                  position: 'absolute',
                  bottom: 0,
                  left: 0,
                  right: 0,
                  height: '2px',
                  background: isActive
                    ? 'var(--ob-color-brand-primary)'
                    : 'transparent',
                  transition: 'background 0.2s ease',
                },

                '&:hover': !tab.disabled && {
                  color: 'var(--ob-color-text-primary)',
                  '&::after': {
                    background: isActive
                      ? 'var(--ob-color-brand-primary)'
                      : 'var(--ob-color-border-subtle)',
                  },
                },
              }),

              // Contained variant
              ...(variant === 'contained' && {
                borderRadius: 'var(--ob-radius-xs)', // 2px
                background: isActive
                  ? 'var(--ob-color-bg-surface)'
                  : 'transparent',
                boxShadow: isActive ? 'var(--ob-shadow-sm)' : 'none',

                '&:hover': !tab.disabled &&
                  !isActive && {
                    background: 'var(--ob-color-action-hover)',
                  },
              }),

              '& svg': {
                fontSize: size === 'sm' ? 14 : 16,
              },
            }}
          >
            {tab.icon}
            {tab.label}
          </Box>
        )
      })}
    </Box>
  )
}

/**
 * TabPanel - Content container for tab
 */
export interface TabPanelProps {
  children: ReactNode
  tabId: string
  activeTab: string
  sx?: SxProps<Theme>
}

export function TabPanel({
  children,
  tabId,
  activeTab,
  sx = {},
}: TabPanelProps) {
  if (tabId !== activeTab) return null

  return (
    <Box
      role="tabpanel"
      sx={{
        pt: 'var(--ob-space-100)',
        ...sx,
      }}
    >
      {children}
    </Box>
  )
}
