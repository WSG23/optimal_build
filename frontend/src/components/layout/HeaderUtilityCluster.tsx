import { useState } from 'react'
import {
  Button,
  IconButton,
  Menu,
  MenuItem,
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

  const buttonStyle = {
    color: 'text.primary',
    borderColor: alpha(theme.palette.divider, 0.2),
    borderRadius: '2px', // Square Cyber-Minimalism: xs for buttons
    padding: '6px 16px',
    height: '40px',
    textTransform: 'none' as const,
    fontSize: '0.875rem',
    fontWeight: 500,
    background: alpha(theme.palette.background.paper, 0.05),
    backdropFilter: 'blur(var(--ob-blur-sm))',
    '&:hover': {
      background: alpha(theme.palette.text.primary, 0.05),
      borderColor: alpha(theme.palette.text.primary, 0.2),
    },
  }

  const iconButtonStyle = {
    color: 'text.secondary',
    border: `1px solid ${alpha(theme.palette.divider, 0.2)}`,
    borderRadius: '50%', // Circular
    width: '40px',
    height: '40px',
    background: alpha(theme.palette.background.paper, 0.05),
    backdropFilter: 'blur(var(--ob-blur-sm))',
    '&:hover': {
      color: 'text.primary',
      background: alpha(theme.palette.text.primary, 0.05),
      borderColor: alpha(theme.palette.text.primary, 0.2),
    },
  }

  return (
    <div
      className="header-utility-cluster"
      style={{ display: 'flex', alignItems: 'center', gap: '12px' }}
    >
      {/* Theme Toggle */}
      <Tooltip title={mode === 'dark' ? 'Light Mode' : 'Dark Mode'}>
        <IconButton
          onClick={toggleMode}
          sx={iconButtonStyle}
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
            sx={{ color: 'text.secondary', fontSize: '1rem' }}
          />
        }
        startIcon={
          <span style={{ fontSize: '1.2rem', lineHeight: 1 }}>
            {currentLangObj.flag}
          </span>
        }
        sx={buttonStyle}
      >
        <span style={{ marginRight: '4px' }}>
          {currentLangObj.code.toUpperCase()}
        </span>
      </Button>

      <Menu
        anchorEl={anchorEl}
        open={open}
        onClose={handleClose}
        PaperProps={{
          elevation: 8,
          sx: {
            mt: 1,
            borderRadius: '4px', // Square Cyber-Minimalism: sm for menus/panels
            minWidth: '160px',
            border: `1px solid ${alpha(theme.palette.divider, 0.1)}`,
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
            sx={{ gap: 2, fontSize: '0.9rem' }}
          >
            <span style={{ fontSize: '1.2rem' }}>{lang.flag}</span>
            {lang.label}
          </MenuItem>
        ))}
      </Menu>

      {/* Developer Mode Toggle */}
      <Tooltip title="Developer Mode">
        <IconButton
          onClick={toggleDeveloperMode}
          sx={{
            ...iconButtonStyle,
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
        <IconButton sx={iconButtonStyle}>
          <SettingsIcon fontSize="small" />
        </IconButton>
      </Tooltip>

      {/* User Avatar */}
      <Tooltip title="Profile">
        <Avatar
          alt="User"
          src="" // Placeholder for now
          sx={{
            width: 40,
            height: 40,
            border: `2px solid ${alpha(theme.palette.background.paper, 0.2)}`,
            cursor: 'pointer',
            bgcolor: 'primary.main',
            fontSize: '0.9rem',
          }}
        >
          US
        </Avatar>
      </Tooltip>
    </div>
  )
}
