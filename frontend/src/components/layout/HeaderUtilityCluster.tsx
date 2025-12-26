import { useState } from 'react'
import {
  Box,
  Button,
  IconButton,
  Menu,
  MenuItem,
  Stack,
  Tooltip,
  useTheme,
  alpha,
  Avatar,
} from '@mui/material'
import {
  Settings as SettingsIcon,
  LightMode as LightModeIcon,
  DarkMode as DarkModeIcon,
  KeyboardArrowDown,
  Code as CodeIcon,
} from '@mui/icons-material'
import { useTranslation } from '../../i18n'
import { useThemeMode } from '../../theme/ThemeContext'
import { useDeveloperMode } from '../../contexts/DeveloperContext'

export function HeaderUtilityCluster() {
  const { i18n } = useTranslation()
  const { mode, toggleMode } = useThemeMode()
  const { isDeveloperMode, toggleDeveloperMode } = useDeveloperMode()
  const theme = useTheme()

  // Language Menu State
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null)
  const open = Boolean(anchorEl)

  const handleClick = (event: React.MouseEvent<HTMLButtonElement>) => {
    setAnchorEl(event.currentTarget)
  }

  const handleClose = () => {
    setAnchorEl(null)
  }

  const handleLanguageChange = (langCode: string) => {
    void i18n.changeLanguage(langCode)
    handleClose()
  }

  const currentLanguage =
    typeof i18n.resolvedLanguage === 'string'
      ? i18n.resolvedLanguage
      : i18n.language

  // Map for display
  const LANGUAGES = [
    { code: 'en', label: 'English', flag: '🇺🇸' },
    { code: 'ja', label: '日本語', flag: '🇯🇵' },
    { code: 'zh', label: '中文', flag: '🇨🇳' },
  ]

  const currentLangObj =
    LANGUAGES.find((l) => l.code === currentLanguage) || LANGUAGES[0]

  const buttonSx = {
    color: 'text.primary',
    borderColor: alpha(theme.palette.divider, 0.2),
    borderRadius: 'var(--ob-radius-xs)',
    px: 'var(--ob-space-100)',
    height: 'var(--ob-space-250)',
    textTransform: 'none' as const,
    fontSize: 'var(--ob-font-size-sm)',
    fontWeight: 500,
    background: alpha(theme.palette.background.paper, 0.05),
    backdropFilter: 'blur(var(--ob-blur-sm))',
    '&:hover': {
      background: alpha(theme.palette.text.primary, 0.05),
      borderColor: alpha(theme.palette.text.primary, 0.2),
    },
  }

  const iconButtonSx = {
    color: 'var(--ob-text-dim)',
    border: 'var(--ob-border-fine)',
    borderRadius: 'var(--ob-radius-sm)',
    width: 'var(--ob-space-250)',
    height: 'var(--ob-space-250)',
    background: 'var(--ob-overlay-subtle)',
    backdropFilter: 'blur(var(--ob-blur-sm))',
    '&:hover': {
      color: 'var(--ob-color-neon-cyan)',
      background: 'var(--ob-color-neon-cyan-dim)',
      borderColor: 'var(--ob-color-neon-cyan)',
    },
  }

  return (
    <Stack
      className="header-utility-cluster"
      direction="row"
      alignItems="center"
      spacing="var(--ob-space-075)"
    >
      {/* Theme Toggle */}
      <Tooltip title={mode === 'dark' ? 'Light Mode' : 'Dark Mode'}>
        <IconButton
          onClick={toggleMode}
          sx={iconButtonSx}
          aria-label="Toggle theme"
        >
          {mode === 'dark' ? (
            <LightModeIcon fontSize="small" />
          ) : (
            <DarkModeIcon fontSize="small" />
          )}
        </IconButton>
      </Tooltip>

      {/* Language Picker */}
      <Button
        variant="outlined"
        onClick={handleClick}
        endIcon={
          <KeyboardArrowDown
            sx={{
              color: 'text.secondary',
              fontSize: 'var(--ob-font-size-sm)',
            }}
          />
        }
        startIcon={
          <Box
            component="span"
            sx={{ fontSize: 'var(--ob-font-size-lg)', lineHeight: 1 }}
          >
            {currentLangObj.flag}
          </Box>
        }
        sx={buttonSx}
      >
        <Box component="span" sx={{ mr: 'var(--ob-space-025)' }}>
          {currentLangObj.code.toUpperCase()}
        </Box>
      </Button>

      <Menu
        anchorEl={anchorEl}
        open={open}
        onClose={handleClose}
        PaperProps={{
          elevation: 8,
          sx: {
            mt: 'var(--ob-space-050)',
            borderRadius: 'var(--ob-radius-sm)',
            minWidth:
              'calc(var(--ob-space-400) + var(--ob-space-400) + var(--ob-space-200))',
            border: 1,
            borderColor: alpha(theme.palette.divider, 0.1),
          },
        }}
        transformOrigin={{ horizontal: 'right', vertical: 'top' }}
        anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
      >
        {LANGUAGES.map((lang) => (
          <MenuItem
            key={lang.code}
            onClick={() => handleLanguageChange(lang.code)}
            selected={currentLanguage === lang.code}
            sx={{ gap: 2, fontSize: 'var(--ob-font-size-sm)' }}
          >
            <Box component="span" sx={{ fontSize: 'var(--ob-font-size-lg)' }}>
              {lang.flag}
            </Box>
            {lang.label}
          </MenuItem>
        ))}
      </Menu>

      {/* Developer Mode Toggle */}
      <Tooltip title="Developer Mode">
        <IconButton
          onClick={toggleDeveloperMode}
          sx={{
            ...iconButtonSx,
            color: isDeveloperMode ? 'primary.main' : 'text.secondary',
            borderColor: isDeveloperMode
              ? 'primary.main'
              : alpha(theme.palette.divider, 0.2),
            bgcolor: isDeveloperMode
              ? alpha(theme.palette.primary.main, 0.1)
              : 'transparent',
          }}
        >
          <CodeIcon fontSize="small" />
        </IconButton>
      </Tooltip>

      {/* Settings */}
      <Tooltip title="Settings">
        <IconButton sx={iconButtonSx}>
          <SettingsIcon fontSize="small" />
        </IconButton>
      </Tooltip>

      {/* User Avatar */}
      <Tooltip title="Profile">
        <Avatar
          alt="User"
          src="" // Placeholder for now
          sx={{
            width: 'var(--ob-space-250)',
            height: 'var(--ob-space-250)',
            border: '1px solid var(--ob-color-neon-cyan)',
            cursor: 'pointer',
            bgcolor: 'var(--ob-color-neon-cyan-dim)',
            color: 'var(--ob-color-neon-cyan)',
            fontSize: 'var(--ob-font-size-sm)',
            fontWeight: 700,
            '&:hover': {
              boxShadow: 'var(--ob-glow-neon-cyan)',
            },
          }}
        >
          US
        </Avatar>
      </Tooltip>
    </Stack>
  )
}
