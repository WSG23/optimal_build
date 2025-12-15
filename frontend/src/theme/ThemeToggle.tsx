import { IconButton, Tooltip } from '@mui/material'
import LightModeIcon from '@mui/icons-material/LightMode'
import DarkModeIcon from '@mui/icons-material/DarkMode'
import { useThemeMode } from './ThemeContext'

export function ThemeToggle() {
  const { mode, toggleMode } = useThemeMode()

  return (
    <Tooltip
      title={mode === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
    >
      <IconButton
        onClick={toggleMode}
        size="small"
        sx={{
          color: 'text.secondary',
          '&:hover': {
            color: 'text.primary',
            bgcolor: 'action.hover',
          },
        }}
        aria-label={
          mode === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'
        }
      >
        {mode === 'dark' ? <LightModeIcon /> : <DarkModeIcon />}
      </IconButton>
    </Tooltip>
  )
}
