import { useMemo, useState } from 'react'
import {
  Avatar,
  Box,
  Divider,
  IconButton,
  ListItemIcon,
  ListItemText,
  Menu,
  MenuItem,
  Snackbar,
  Stack,
  Typography,
  alpha,
  useTheme,
} from '@mui/material'
import {
  Close as CloseIcon,
  Code as CodeIcon,
  ContentCopy as ContentCopyIcon,
  DarkMode as DarkModeIcon,
  Language as LanguageIcon,
  LightMode as LightModeIcon,
  Menu as MenuIcon,
  Share as ShareIcon,
  UploadFile as UploadFileIcon,
} from '@mui/icons-material'
import { getSupportedLanguage, supportedLanguages, useTranslation } from '../../i18n'
import { Link } from '../../router'
import { useDeveloperMode } from '../../contexts/useDeveloperMode'
import { useThemeMode } from '../../theme/ThemeContext'

const DEVELOPER_LINKS = [
  { to: '/app/site-acquisition', label: 'Site Acquisition' },
  { to: '/app/asset-feasibility', label: 'Asset Feasibility' },
  { to: '/app/financial-control', label: 'Financial Control' },
  { to: '/app/phase-management', label: 'Phase Management' },
  { to: '/developers/team-coordination', label: 'Team Coordination' },
  { to: '/app/regulatory', label: 'Regulatory Navigation' },
  { to: '/developer', label: 'Developer Console' },
]

export function TopUtilityMenu() {
  const theme = useTheme()
  const { i18n, t } = useTranslation()
  const { mode, toggleMode } = useThemeMode()
  const { isDeveloperMode, toggleDeveloperMode } = useDeveloperMode()
  const showDeveloperLinks = isDeveloperMode

  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null)
  const [snackbarMessage, setSnackbarMessage] = useState<string | null>(null)

  const open = Boolean(anchorEl)

  const currentLanguage =
    typeof i18n.resolvedLanguage === 'string'
      ? i18n.resolvedLanguage
      : i18n.language

  const currentLangObj = useMemo(() => {
    return getSupportedLanguage(currentLanguage)
  }, [currentLanguage])

  const getCurrentUrl = () => {
    if (typeof window === 'undefined') return ''
    return window.location.href || ''
  }

  const copyToClipboard = async (value: string) => {
    try {
      if (typeof navigator !== 'undefined' && navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(value)
        setSnackbarMessage('Copied link')
        return
      }
    } catch {
      // fall through
    }

    try {
      if (typeof window !== 'undefined') {
        window.prompt('Copy link:', value)
      }
    } finally {
      setSnackbarMessage('Copy link opened')
    }
  }

  const handleShareLink = async () => {
    const url = getCurrentUrl()
    try {
      if (typeof navigator !== 'undefined' && 'share' in navigator) {
        await navigator.share({ url, title: document.title })
        return
      }
    } catch {
      // fall through
    }
    await copyToClipboard(url)
  }

  const handleLanguageChange = async (langCode: string) => {
    await i18n.changeLanguage(langCode)
    setSnackbarMessage(`Language: ${langCode.toUpperCase()}`)
  }

  const iconButtonSx = {
    borderRadius: 'var(--ob-radius-sm)',
    border: 'var(--ob-border-fine)',
    width: 'var(--ob-space-250)',
    height: 'var(--ob-space-250)',
    color: open ? 'var(--ob-color-neon-cyan)' : 'var(--ob-text-dim)',
    background: open
      ? 'var(--ob-color-neon-cyan-dim)'
      : 'var(--ob-overlay-subtle)',
    backdropFilter: 'blur(var(--ob-blur-sm))',
    '&:hover': {
      color: 'var(--ob-color-neon-cyan)',
      background: 'var(--ob-color-neon-cyan-dim)',
      borderColor: 'var(--ob-color-neon-cyan)',
    },
  } as const

  return (
    <>
      <IconButton
        aria-label="Open menu"
        aria-haspopup="menu"
        aria-expanded={open ? 'true' : 'false'}
        onClick={(event) => setAnchorEl(open ? null : event.currentTarget)}
        sx={iconButtonSx}
      >
        {open ? <CloseIcon fontSize="small" /> : <MenuIcon fontSize="small" />}
      </IconButton>

      <Menu
        anchorEl={anchorEl}
        open={open}
        onClose={() => setAnchorEl(null)}
        PaperProps={{
          elevation: 10,
          sx: {
            mt: 'var(--ob-space-050)',
            borderRadius: 'var(--ob-radius-sm)',
            border: 1,
            borderColor: alpha(theme.palette.divider, 0.12),
            minWidth:
              'calc(var(--ob-space-400) + var(--ob-space-400) + var(--ob-space-200))',
            overflow: 'hidden',
          },
        }}
        transformOrigin={{ horizontal: 'right', vertical: 'top' }}
        anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
      >
        <Box
          sx={{
            px: 'var(--ob-space-150)',
            py: 'var(--ob-space-100)',
            bgcolor: alpha(theme.palette.background.paper, 0.6),
            borderBottom: 1,
            borderColor: alpha(theme.palette.divider, 0.12),
          }}
        >
          <Stack
            direction="row"
            alignItems="center"
            spacing="var(--ob-space-100)"
          >
            <Avatar
              sx={{
                width: 'var(--ob-space-250)',
                height: 'var(--ob-space-250)',
                borderRadius: 'var(--ob-radius-pill)',
                bgcolor: 'var(--ob-color-neon-cyan-dim)',
                color: 'var(--ob-color-neon-cyan)',
                border: '1px solid var(--ob-color-neon-cyan)',
                fontSize: 'var(--ob-font-size-sm)',
                fontFamily: 'var(--ob-font-family-mono)',
                fontWeight: 700,
              }}
            >
              {currentLangObj.menuCode}
            </Avatar>
            <Box sx={{ minWidth: 0 }}>
              <Typography
                sx={{
                  fontWeight: 700,
                  fontSize: 'var(--ob-font-size-sm)',
                  color: 'text.primary',
                }}
              >
                Quick menu
              </Typography>
              <Typography
                sx={{
                  fontFamily: 'var(--ob-font-family-mono)',
                  fontSize: 'var(--ob-font-size-xs)',
                  color: 'text.secondary',
                }}
              >
                {t('common.language.label')} · {t(currentLangObj.labelKey)}
              </Typography>
            </Box>
          </Stack>
        </Box>

        <MenuItem
          onClick={() => {
            setAnchorEl(null)
            toggleMode()
            setSnackbarMessage(mode === 'dark' ? 'Light mode' : 'Dark mode')
          }}
        >
          <ListItemIcon>
            {mode === 'dark' ? (
              <LightModeIcon fontSize="small" />
            ) : (
              <DarkModeIcon fontSize="small" />
            )}
          </ListItemIcon>
          <ListItemText>
            Appearance
            <Typography
              component="span"
              sx={{
                ml: 'var(--ob-space-050)',
                fontFamily: 'var(--ob-font-family-mono)',
                fontSize: 'var(--ob-font-size-xs)',
                color: 'text.secondary',
              }}
            >
              {mode === 'dark' ? 'Dark' : 'Light'}
            </Typography>
          </ListItemText>
        </MenuItem>

        <Divider />

        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            gap: 'var(--ob-space-100)',
            px: 'var(--ob-space-150)',
            py: 'var(--ob-space-075)',
            color: 'text.secondary',
            fontSize: 'var(--ob-font-size-xs)',
            textTransform: 'uppercase',
            letterSpacing: '0.08em',
          }}
        >
          <Box
            component="span"
            sx={{
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'text.secondary',
            }}
          >
            <LanguageIcon fontSize="small" />
          </Box>
          <Typography component="span" variant="inherit">
            {t('common.language.label')}
          </Typography>
        </Box>
        {supportedLanguages.map((lang) => (
          <MenuItem
            key={lang.value}
            selected={currentLanguage === lang.value}
            onClick={() => {
              setAnchorEl(null)
              void handleLanguageChange(lang.value)
            }}
            sx={{
              px: 'var(--ob-space-150)',
              py: 'var(--ob-space-075)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: 'var(--ob-space-100)',
            }}
          >
            <ListItemText
              primary={t(lang.labelKey)}
              secondary={lang.nativeLabel}
              primaryTypographyProps={{
                sx: {
                  fontSize: 'var(--ob-font-size-sm)',
                  fontWeight: currentLanguage === lang.value ? 600 : 500,
                },
              }}
              secondaryTypographyProps={{
                sx: {
                  fontSize: 'var(--ob-font-size-xs)',
                  color: 'text.secondary',
                },
              }}
            />
            <Box
              component="span"
              sx={{
                minWidth: '2.5rem',
                px: 'var(--ob-space-050)',
                py: '2px',
                borderRadius: 'var(--ob-radius-pill)',
                border: '1px solid',
                borderColor:
                  currentLanguage === lang.value
                    ? 'var(--ob-color-neon-cyan)'
                    : alpha(theme.palette.divider, 0.2),
                color:
                  currentLanguage === lang.value
                    ? 'var(--ob-color-neon-cyan)'
                    : 'text.secondary',
                fontFamily: 'var(--ob-font-family-mono)',
                fontSize: 'var(--ob-font-size-xs)',
                textAlign: 'center',
              }}
            >
              {lang.menuCode}
            </Box>
          </MenuItem>
        ))}

        <Divider />

        <MenuItem
          onClick={() => {
            setAnchorEl(null)
            toggleDeveloperMode()
            setSnackbarMessage(
              isDeveloperMode ? 'Developer mode off' : 'Developer mode on',
            )
          }}
        >
          <ListItemIcon>
            <CodeIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>
            Developer mode
            <Typography
              component="span"
              sx={{
                ml: 'var(--ob-space-050)',
                fontFamily: 'var(--ob-font-family-mono)',
                fontSize: 'var(--ob-font-size-xs)',
                color: isDeveloperMode ? 'primary.main' : 'text.secondary',
              }}
            >
              {isDeveloperMode ? 'ON' : 'OFF'}
            </Typography>
          </ListItemText>
        </MenuItem>

        {showDeveloperLinks && (
          <>
            <Divider />
            <MenuItem disabled>
              <ListItemIcon>
                <CodeIcon fontSize="small" />
              </ListItemIcon>
              <ListItemText>Developer workspace</ListItemText>
            </MenuItem>
            {DEVELOPER_LINKS.map(({ to, label }) => (
              <MenuItem
                key={to}
                component={Link}
                to={to}
                onClick={() => setAnchorEl(null)}
              >
                <ListItemIcon>
                  <CodeIcon fontSize="small" />
                </ListItemIcon>
                <ListItemText>{label}</ListItemText>
              </MenuItem>
            ))}
          </>
        )}

        <Divider />

        <MenuItem
          onClick={() => {
            setAnchorEl(null)
            void copyToClipboard(getCurrentUrl())
          }}
        >
          <ListItemIcon>
            <ContentCopyIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>Copy link</ListItemText>
        </MenuItem>
        <MenuItem
          onClick={() => {
            setAnchorEl(null)
            void handleShareLink()
          }}
        >
          <ListItemIcon>
            <ShareIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>Share link</ListItemText>
        </MenuItem>
        <MenuItem
          component={Link}
          to="/cad/upload"
          onClick={() => setAnchorEl(null)}
        >
          <ListItemIcon>
            <UploadFileIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>New upload</ListItemText>
        </MenuItem>
      </Menu>

      <Snackbar
        open={Boolean(snackbarMessage)}
        message={snackbarMessage ?? ''}
        autoHideDuration={2000}
        onClose={() => setSnackbarMessage(null)}
        anchorOrigin={{ vertical: 'top', horizontal: 'right' }}
        ContentProps={{ role: 'status', 'aria-live': 'polite' as const }}
      />
    </>
  )
}
