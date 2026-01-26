import { History, Restore } from '@mui/icons-material'
import {
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  Typography,
  IconButton,
  Tooltip,
} from '@mui/material'
import type { PendingPayload } from '../types'
import type { BuildableSummary } from '../../../api/buildable'

export interface HistoryItem {
  id: string
  timestamp: Date
  payload: PendingPayload
  result: BuildableSummary | null
}

interface ScenarioHistorySidebarProps {
  open: boolean
  onClose: () => void
  history: HistoryItem[]
  onRestore: (item: HistoryItem) => void
}

export function ScenarioHistorySidebar({
  open,
  onClose,
  history,
  onRestore,
}: ScenarioHistorySidebarProps) {
  return (
    <Drawer
      anchor="right"
      open={open}
      onClose={onClose}
      PaperProps={{
        sx: { width: 320, padding: 'var(--ob-space-4)' },
      }}
    >
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          marginBottom: 'var(--ob-space-4)',
          paddingBottom: 'var(--ob-space-2)',
          borderBottom: '1px solid var(--ob-color-border-light)',
        }}
      >
        <History sx={{ marginRight: 1, color: 'var(--ob-color-text-muted)' }} />
        <Typography variant="h6" className="text-heading">
          Scenario History
        </Typography>
      </div>

      {history.length === 0 ? (
        <div
          style={{
            padding: 'var(--ob-space-400)',
            textAlign: 'center',
            color: 'var(--ob-color-text-muted)',
          }}
        >
          <Typography variant="body2">No scenarios run yet.</Typography>
        </div>
      ) : (
        <List>
          {history.map((item) => (
            <ListItem
              key={item.id}
              disablePadding
              sx={{
                marginBottom: 'var(--ob-space-100)',
                background: 'var(--ob-color-bg-surface-secondary)',
                borderRadius: 'var(--ob-radius-md)',
              }}
            >
              <ListItemButton onClick={() => onRestore(item)}>
                <ListItemText
                  primary={item.payload.address}
                  primaryTypographyProps={{
                    variant: 'subtitle2',
                    noWrap: true,
                  }}
                  secondary={
                    <>
                      <Typography variant="caption" display="block">
                        {item.timestamp.toLocaleTimeString()}
                      </Typography>
                      {item.result && (
                        <Typography
                          variant="caption"
                          sx={{ color: 'var(--ob-color-accent)' }}
                        >
                          {Math.round(
                            item.result.metrics.nsaEstM2,
                          ).toLocaleString()}{' '}
                          sqm NSA
                        </Typography>
                      )}
                    </>
                  }
                />
                <Tooltip title="Restore this scenario">
                  <IconButton edge="end" size="small">
                    <Restore fontSize="small" />
                  </IconButton>
                </Tooltip>
              </ListItemButton>
            </ListItem>
          ))}
        </List>
      )}
    </Drawer>
  )
}
