import {
  Box,
  Divider,
  Drawer,
  IconButton,
  List,
  ListItemButton,
  ListItemText,
  Typography,
} from '@mui/material'
import ChevronLeftIcon from '@mui/icons-material/ChevronLeft'
import { Link } from '../../router'
import type { NavGroup } from '../../hooks/useNavGroups'

interface MobileNavDrawerProps {
  open: boolean
  onClose: () => void
  navGroups: NavGroup[]
  currentPath: string
}

export function MobileNavDrawer({
  open,
  onClose,
  navGroups,
  currentPath,
}: MobileNavDrawerProps) {
  return (
    <Drawer
      anchor="left"
      open={open}
      onClose={onClose}
      PaperProps={{
        sx: {
          width: 'var(--ob-size-sidebar-width)',
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
            fontWeight: 'var(--ob-font-weight-bold)',
            fontSize: 'var(--ob-font-size-sm)',
            color: 'var(--ob-color-brand-primary)',
            letterSpacing: 'var(--ob-letter-spacing-wider)',
            textTransform: 'uppercase',
          }}
        >
          OB
        </Typography>
        <IconButton
          aria-label="Close navigation"
          onClick={onClose}
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
                  pt: 'var(--ob-space-150)',
                  pb: 'var(--ob-space-050)',
                  fontSize: 'var(--ob-font-size-2xs)',
                  fontWeight: 'var(--ob-font-weight-bold)',
                  color: 'text.disabled',
                  textTransform: 'uppercase',
                  letterSpacing: 'var(--ob-letter-spacing-wider)',
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
                selected={currentPath === item.path}
                onClick={onClose}
                sx={{
                  borderRadius: 'var(--ob-radius-sm)',
                  mx: 'var(--ob-space-050)',
                  '&.Mui-selected': {
                    bgcolor: 'var(--ob-color-brand-muted)',
                    color: 'var(--ob-color-brand-primary)',
                  },
                  '&.Mui-selected:hover': {
                    bgcolor: 'var(--ob-color-brand-muted)',
                  },
                }}
              >
                <ListItemText
                  primary={item.label}
                  primaryTypographyProps={{
                    fontSize: 'var(--ob-font-size-sm)',
                    fontWeight: 'var(--ob-font-weight-semibold)',
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
  )
}
