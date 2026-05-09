import { useMemo, useState } from 'react'
import {
  Avatar,
  Box,
  Button,
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
import CloseIcon from '@mui/icons-material/Close'
import CodeIcon from '@mui/icons-material/Code'
import ContentCopyIcon from '@mui/icons-material/ContentCopy'
import DarkModeIcon from '@mui/icons-material/DarkMode'
import LanguageIcon from '@mui/icons-material/Language'
import LightModeIcon from '@mui/icons-material/LightMode'
import MenuIcon from '@mui/icons-material/Menu'
import ShareIcon from '@mui/icons-material/Share'
import UploadFileIcon from '@mui/icons-material/UploadFile'
import { useTranslation } from '../../i18n'
import { Link } from '../../router'
import { useDeveloperMode } from '../../contexts/useDeveloperMode'
import { useThemeMode } from '../../theme/ThemeContext'

const LANGUAGES = [
  { code: 'en', label: 'English', flag: '🇺🇸' },
  { code: 'ja', label: '日本語', flag: '🇯🇵' },
  { code: 'zh', label: '中文', flag: '🇨🇳' },
]

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
  const { i18n } = useTranslation()
  const { mode, toggleMode } = useThemeMode()
  const { isDeveloperMode, toggleDeveloperMode } = useDeveloperMode()
  const showDeveloperLinks = isDeveloperMode

  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null)
  const [snackbarMessage, setSnackbarMessage] = useState<string | null>(null)
  const [snackbarUndo, setSnackbarUndo] = useState<(() => void) | null>(null)

  const open = Boolean(anchorEl)

  const currentLanguage =
    typeof i18n.resolvedLanguage === 'string'
      ? i18n.resolvedLanguage
      : i18n.language

  const currentLangObj = useMemo(() => {
    return LANGUAGES.find((l) => l.code === currentLanguage) || LANGUAGES[0]
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
    borderRadius: 'var(--ob-radius-xs)',
    border: 'var(--ob-border-fine)',
    width: 'var(--ob-space-250)',
    height: 'var(--ob-space-250)',
    color: open ? 'var(--ob-color-brand-primary)' : 'text.secondary',
    background: open
      ? 'var(--ob-color-brand-muted)'
      : 'var(--ob-overlay-subtle)',
    backdropFilter: 'blur(var(--ob-blur-sm))',
    '&:hover': {
      color: 'var(--ob-color-brand-primary)',
      background: 'var(--ob-color-brand-muted)',
      borderColor: 'var(--ob-color-brand-primary)',
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
          elevation: 0,
          sx: {
            mt: 'var(--ob-space-050)',
            borderRadius: 'var(--ob-radius-sm)',
            border: 1,
            borderColor: alpha(theme.palette.divider, 0.12),
            minWidth: '10rem',
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
                bgcolor: 'primary.main',
                fontSize: 'var(--ob-font-size-xs)',
                fontFamily: 'var(--ob-font-family-mono)',
                fontWeight: 'var(--ob-font-weight-bold)',
              }}
            >
              OB
            </Avatar>
            <Box sx={{ minWidth: 0 }}>
              <Typography
                sx={{
                  fontWeight: 'var(--ob-font-weight-bold)',
                  fontSize: 'var(--ob-font-size-sm)',
                  color: 'text.primary',
                }}
              >
                Settings
              </Typography>
              <Typography
                sx={{
                  fontFamily: 'var(--ob-font-family-mono)',
                  fontSize: 'var(--ob-font-size-xs)',
                  color: 'text.secondary',
                }}
              >
                {currentLangObj.flag} {currentLangObj.code.toUpperCase()}
              </Typography>
            </Box>
          </Stack>
        </Box>

        <MenuItem
          onClick={() => {
            setAnchorEl(null)
            toggleMode()
            setSnackbarMessage(mode === 'dark' ? 'Light mode' : 'Dark mode')
            setSnackbarUndo(() => () => toggleMode())
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

        <MenuItem disabled>
          <ListItemIcon>
            <LanguageIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>Language</ListItemText>
        </MenuItem>
        {LANGUAGES.map((lang) => (
          <MenuItem
            key={lang.code}
            selected={currentLanguage === lang.code}
            onClick={() => {
              setAnchorEl(null)
              void handleLanguageChange(lang.code)
            }}
            sx={{ pl: 'var(--ob-space-200)' }}
          >
            <ListItemText>
              <Box
                component="span"
                sx={{
                  mr: 'var(--ob-space-050)',
                  fontSize: 'var(--ob-font-size-lg)',
                }}
              >
                {lang.flag}
              </Box>
              {lang.label}
            </ListItemText>
          </MenuItem>
        ))}

        <Divider />

        <MenuItem
          role="menuitemcheckbox"
          aria-checked={isDeveloperMode}
          onClick={() => {
            setAnchorEl(null)
            toggleDeveloperMode()
            setSnackbarMessage(
              isDeveloperMode ? 'Advanced tools off' : 'Advanced tools on',
            )
            setSnackbarUndo(() => () => toggleDeveloperMode())
          }}
        >
          <ListItemIcon>
            <CodeIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>
            Advanced tools
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
            <MenuItem disabled sx={{ opacity: 0.6 }}>
              <ListItemIcon>
                <CodeIcon fontSize="small" />
              </ListItemIcon>
              <ListItemText
                primaryTypographyProps={{
                  sx: {
                    fontSize: 'var(--ob-font-size-2xs)',
                    textTransform: 'uppercase',
                    letterSpacing: 'var(--ob-letter-spacing-wider)',
                  },
                }}
              >
                Advanced workspace
              </ListItemText>
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
        autoHideDuration={3000}
        onClose={() => {
          setSnackbarMessage(null)
          setSnackbarUndo(null)
        }}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
        ContentProps={{ role: 'status', 'aria-live': 'polite' as const }}
        action={
          snackbarUndo ? (
            <Button
              size="small"
              sx={{
                color: 'var(--ob-color-brand-primary)',
                fontWeight: 'var(--ob-font-weight-bold)',
                fontSize: 'var(--ob-font-size-xs)',
              }}
              onClick={() => {
                snackbarUndo()
                setSnackbarMessage(null)
                setSnackbarUndo(null)
              }}
            >
              Undo
            </Button>
          ) : undefined
        }
      />
    </>
  )
}
