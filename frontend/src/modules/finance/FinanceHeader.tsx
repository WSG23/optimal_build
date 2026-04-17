import { Box, Stack, Tabs, Tab, Typography } from '@mui/material'
import PushPinIcon from '@mui/icons-material/PushPin'
import PushPinOutlinedIcon from '@mui/icons-material/PushPinOutlined'

import { Button } from '../../components/canonical/Button'
import {
  FinanceHeaderControls,
  type FinanceProjectOption,
} from './components/FinanceHeaderControls'
import type { TranslationOptions } from '../../i18n/i18n'

type TranslateFn = (key: string, options?: TranslationOptions) => string

interface FinanceHeaderProps {
  path: string
  activeTab: number
  setActiveTab: (tab: number) => void
  isHeaderPinned: boolean
  setIsHeaderPinned: React.Dispatch<React.SetStateAction<boolean>>
  isMobile: boolean
  t: TranslateFn
  hasAccess: boolean
  headerControlsProps: {
    selectedProjectId: string
    selectedProjectName: string | null
    options: FinanceProjectOption[]
    onProjectChange: (projectId: string, projectName?: string | null) => void
    onRefresh: () => void
    refreshing: boolean
    onImportWorkbook: () => void
    importingWorkbook: boolean
    importDisabled: boolean
    onExportWorkbook: () => void
    exportingWorkbook: boolean
    onExportCsv: () => void
    exportingCsv: boolean
    exportDisabled: boolean
  }
}

export function FinanceHeader({
  path,
  activeTab,
  setActiveTab,
  isHeaderPinned,
  setIsHeaderPinned,
  isMobile,
  t,
  hasAccess,
  headerControlsProps,
}: FinanceHeaderProps) {
  const headerActions = hasAccess ? (
    <Stack
      direction="row"
      spacing="var(--ob-space-100)"
      alignItems="center"
      justifyContent="flex-end"
      sx={{
        flexWrap: 'nowrap',
        minWidth: 0,
        columnGap: 'var(--ob-space-100)',
      }}
    >
      <FinanceHeaderControls {...headerControlsProps} />

      <Button
        size="sm"
        variant="secondary"
        onClick={() => setIsHeaderPinned((prev) => !prev)}
        aria-label={
          isHeaderPinned
            ? t('finance.header.unpin', {
                defaultValue: 'Unpin header (scroll)',
              })
            : t('finance.header.pin', {
                defaultValue: 'Pin header (sticky)',
              })
        }
        title={
          isHeaderPinned
            ? t('finance.header.unpin', {
                defaultValue: 'Unpin header (scroll)',
              })
            : t('finance.header.pin', {
                defaultValue: 'Pin header (sticky)',
              })
        }
        sx={{
          width: 'var(--ob-size-icon-md)',
          minWidth: 'var(--ob-size-icon-md)',
          px: 0,
        }}
      >
        {isHeaderPinned ? (
          <PushPinIcon fontSize="small" />
        ) : (
          <PushPinOutlinedIcon fontSize="small" />
        )}
      </Button>
    </Stack>
  ) : undefined

  return (
    <Box
      sx={{
        ...(isHeaderPinned
          ? {
              position: 'sticky',
              top: 0,
              zIndex: 'var(--ob-z-sticky)',
            }
          : {}),
        mb: 'var(--ob-space-150)',
      }}
    >
      {/* Finance Header - Depth 0 (Direct on Grid)
          AI Studio Protocol: Headers sit directly on the background
          NO glass, NO cyan edge for Depth 0 elements */}
      <Box
        component="header"
        key={path}
        className="ob-page-header"
        sx={{
          borderBottom: 1,
          borderColor: 'divider',
          animation:
            'ob-slide-down-fade var(--ob-motion-header-duration) var(--ob-motion-header-ease) both',
          '@media (prefers-reduced-motion: reduce)': {
            animation: 'none',
          },
        }}
      >
        <Box
          sx={{
            px: 'var(--ob-space-300)',
            py: 'var(--ob-space-200)',
            display: 'flex',
            alignItems: 'flex-start',
            justifyContent: 'space-between',
            gap: 'var(--ob-space-150)',
            flexWrap: { xs: 'wrap', md: 'nowrap' },
          }}
        >
          <Box sx={{ minWidth: 0 }}>
            <Typography variant="h4" sx={{ fontWeight: 700 }}>
              {t('finance.title')}
            </Typography>
            <Typography
              variant="body2"
              sx={{ color: 'text.secondary', mt: 'var(--ob-space-025)' }}
            >
              {t('finance.subtitle')}
            </Typography>
          </Box>
          {headerActions}
        </Box>

        <Box
          sx={{
            borderTop: 1,
            borderColor: 'divider',
            px: 'var(--ob-space-300)',
          }}
        >
          <Tabs
            value={activeTab}
            onChange={(_, v) => setActiveTab(v)}
            variant="scrollable"
            scrollButtons="auto"
            allowScrollButtonsMobile
            sx={{
              minHeight: 'var(--ob-space-300)',
              '& .MuiTabs-indicator': {
                backgroundColor: 'var(--ob-color-neon-cyan)',
                boxShadow: 'var(--ob-glow-neon-cyan)',
                height: '2px',
              },
              '& .MuiTab-root': {
                minHeight: 'var(--ob-space-300)',
                textTransform: 'uppercase',
                fontSize: 'var(--ob-font-size-xs)',
                fontWeight: 'var(--ob-font-weight-semibold)',
                letterSpacing: 'var(--ob-letter-spacing-wider)',
                px: 'var(--ob-space-100)',
                color: 'text.secondary',
                transition: 'all 0.2s ease',
                '&.Mui-selected': {
                  color: 'var(--ob-color-neon-cyan)',
                  textShadow: 'var(--ob-glow-neon-text)',
                },
                '&:hover': {
                  color: 'var(--ob-color-neon-cyan)',
                },
              },
            }}
          >
            <Tab
              label={isMobile ? 'Capital' : t('finance.tabs.capitalStack')}
            />
            <Tab
              label={isMobile ? 'Drawdown' : t('finance.tabs.drawdownSchedule')}
            />
            <Tab
              label={isMobile ? 'Assets' : t('finance.tabs.assetBreakdown')}
            />
            <Tab
              label={isMobile ? 'Facilities' : t('finance.tabs.facilityEditor')}
            />
            <Tab label={isMobile ? 'Jobs' : t('finance.tabs.jobTimeline')} />
            <Tab
              label={isMobile ? 'Interest' : t('finance.tabs.loanInterest')}
            />
            <Tab label={isMobile ? 'Analytics' : t('finance.tabs.analytics')} />
            <Tab
              label={isMobile ? 'Sensitivity' : t('finance.tabs.sensitivity')}
            />
          </Tabs>
        </Box>
      </Box>
    </Box>
  )
}
