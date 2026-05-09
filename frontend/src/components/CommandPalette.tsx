import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type KeyboardEvent,
} from 'react'
import {
  Box,
  Dialog,
  InputAdornment,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  TextField,
  Typography,
} from '@mui/material'
import SearchIcon from '@mui/icons-material/Search'
import KeyboardReturnIcon from '@mui/icons-material/KeyboardReturn'
import { useRouterController } from '../router'
import {
  AGENT_NAV_ITEMS,
  DEVELOPER_NAV_ITEMS,
  NAV_ITEMS,
  type NavItem,
} from '../app/navigation'
import { Kbd } from './canonical/Kbd'

const RECENT_STORAGE_KEY = 'ob_recent_nav'
const MAX_RECENT = 5

interface RecentEntry {
  path: string
  label: string
}

function loadRecentItems(): RecentEntry[] {
  if (typeof window === 'undefined') return []
  try {
    const raw = window.localStorage.getItem(RECENT_STORAGE_KEY)
    if (!raw) return []
    const parsed: unknown = JSON.parse(raw)
    if (!Array.isArray(parsed)) return []
    return parsed
      .filter(
        (entry): entry is RecentEntry =>
          typeof entry === 'object' &&
          entry !== null &&
          typeof (entry as Record<string, unknown>).path === 'string' &&
          typeof (entry as Record<string, unknown>).label === 'string',
      )
      .slice(0, MAX_RECENT)
  } catch {
    return []
  }
}

function saveRecentItems(items: RecentEntry[]) {
  if (typeof window === 'undefined') return
  window.localStorage.setItem(
    RECENT_STORAGE_KEY,
    JSON.stringify(items.slice(0, MAX_RECENT)),
  )
}

function pushRecentItem(path: string, label: string): RecentEntry[] {
  const current = loadRecentItems()
  const filtered = current.filter((entry) => entry.path !== path)
  const updated = [{ path, label }, ...filtered].slice(0, MAX_RECENT)
  saveRecentItems(updated)
  return updated
}

interface GroupedItems {
  label: string
  items: NavItem[]
}

const GROUPS: GroupedItems[] = [
  { label: 'Agent Tools', items: AGENT_NAV_ITEMS },
  { label: 'Developer Tools', items: DEVELOPER_NAV_ITEMS },
]

function matchesQuery(item: NavItem, query: string): boolean {
  const q = query.toLowerCase()
  const label = item.label.toLowerCase()
  const desc = (item.description ?? '').toLowerCase()

  // Exact substring match on label or description
  if (label.includes(q) || desc.includes(q)) return true

  // Simple fuzzy: all query chars appear in order in the label
  let qi = 0
  for (let i = 0; i < label.length && qi < q.length; i++) {
    if (label[i] === q[qi]) qi++
  }
  return qi === q.length
}

export function CommandPalette() {
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState('')
  const [selectedIndex, setSelectedIndex] = useState(0)
  const [recentItems, setRecentItems] = useState<RecentEntry[]>([])
  const { navigate } = useRouterController()
  const listRef = useRef<HTMLUListElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  // Load recent items when palette opens
  useEffect(() => {
    if (open) {
      setRecentItems(loadRecentItems())
    }
  }, [open])

  // Global keyboard listener
  useEffect(() => {
    function handleKeyDown(e: globalThis.KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault()
        setOpen((prev) => !prev)
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [])

  // Build recent NavItems from stored entries
  const recentNavItems: NavItem[] = useMemo(() => {
    if (query.trim()) return []
    return recentItems
      .map((entry) => {
        const existing = NAV_ITEMS.find((nav) => nav.path === entry.path)
        if (existing) return existing
        // Build a synthetic NavItem for paths not in nav items
        return {
          key: entry.path as NavItem['key'],
          label: entry.label,
          path: entry.path,
        }
      })
      .filter(
        (item, index, arr) =>
          arr.findIndex((other) => other.path === item.path) === index,
      )
  }, [recentItems, query])

  // Filter groups based on query
  const filteredGroups = useMemo(() => {
    if (!query.trim()) return GROUPS

    return GROUPS.map((group) => ({
      ...group,
      items: group.items.filter((item) => matchesQuery(item, query.trim())),
    })).filter((group) => group.items.length > 0)
  }, [query])

  // Combined groups: recent (when no query) + filtered groups
  const displayGroups = useMemo(() => {
    const groups: GroupedItems[] = []
    if (recentNavItems.length > 0) {
      groups.push({ label: 'Recent', items: recentNavItems })
    }
    groups.push(...filteredGroups)
    return groups
  }, [recentNavItems, filteredGroups])

  // Flat list of visible items for keyboard navigation
  const flatItems = useMemo(
    () => displayGroups.flatMap((g) => g.items),
    [displayGroups],
  )

  // Reset selection when results change
  useEffect(() => {
    setSelectedIndex(0)
  }, [flatItems.length])

  const handleClose = useCallback(() => {
    setOpen(false)
    setQuery('')
    setSelectedIndex(0)
  }, [])

  const handleNavigate = useCallback(
    (item: NavItem) => {
      handleClose()
      const updated = pushRecentItem(item.path, item.label)
      setRecentItems(updated)
      navigate(item.path)
    },
    [handleClose, navigate],
  )

  const handleKeyDown = useCallback(
    (e: KeyboardEvent<HTMLDivElement>) => {
      switch (e.key) {
        case 'ArrowDown':
          e.preventDefault()
          setSelectedIndex((prev) =>
            prev < flatItems.length - 1 ? prev + 1 : 0,
          )
          break
        case 'ArrowUp':
          e.preventDefault()
          setSelectedIndex((prev) =>
            prev > 0 ? prev - 1 : flatItems.length - 1,
          )
          break
        case 'Enter':
          e.preventDefault()
          if (
            flatItems[selectedIndex] &&
            !flatItems[selectedIndex].comingSoon
          ) {
            handleNavigate(flatItems[selectedIndex])
          }
          break
      }
    },
    [flatItems, selectedIndex, handleNavigate],
  )

  // Scroll selected item into view
  useEffect(() => {
    if (!listRef.current) return
    const selected = listRef.current.querySelector(
      '[data-selected="true"]',
    ) as HTMLElement | null
    selected?.scrollIntoView({ block: 'nearest' })
  }, [selectedIndex])

  const isMac =
    typeof navigator !== 'undefined' &&
    /Mac|iPhone|iPad/.test(navigator.userAgent)
  const shortcutHint = isMac ? '\u2318K' : 'Ctrl+K'

  let flatIndex = -1

  return (
    <Dialog
      open={open}
      onClose={handleClose}
      maxWidth={false}
      disableRestoreFocus
      slotProps={{
        backdrop: {
          sx: {
            backgroundColor: 'rgba(0, 0, 0, 0.6)',
            backdropFilter: 'blur(2px)',
          },
        },
      }}
      PaperProps={{
        sx: {
          width: '100%',
          maxWidth: 560,
          borderRadius: 'var(--ob-radius-lg)',
          bgcolor: 'background.paper',
          border: '1px solid',
          borderColor: 'divider',
          overflow: 'hidden',
          position: 'fixed',
          top: '20%',
          m: 0,
        },
      }}
    >
      <Box
        sx={{
          p: 'var(--ob-space-100)',
          borderBottom: '1px solid',
          borderColor: 'divider',
        }}
      >
        <TextField
          inputRef={inputRef}
          fullWidth
          autoFocus
          placeholder={`Search commands... ${shortcutHint}`}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          variant="outlined"
          size="small"
          inputProps={{
            role: 'combobox',
            'aria-autocomplete': 'list' as const,
            'aria-controls': 'command-palette-list',
            'aria-activedescendant': flatItems[selectedIndex]
              ? `command-palette-item-${flatItems[selectedIndex].key}`
              : undefined,
          }}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon sx={{ fontSize: 18, color: 'text.secondary' }} />
              </InputAdornment>
            ),
            sx: {
              borderRadius: 'var(--ob-radius-sm)',
              fontSize: 'var(--ob-font-size-sm)',
            },
          }}
        />
      </Box>

      <List
        ref={listRef}
        id="command-palette-list"
        role="listbox"
        aria-label="Command results"
        sx={{
          maxHeight: 400,
          overflowY: 'auto',
          py: 'var(--ob-space-050)',
        }}
      >
        {displayGroups.length === 0 && query.trim() && (
          <Box
            sx={{
              py: 'var(--ob-space-300)',
              textAlign: 'center',
            }}
          >
            <Typography variant="body2" color="text.secondary">
              No results for &ldquo;{query}&rdquo;
            </Typography>
          </Box>
        )}

        {displayGroups.map((group) => (
          <Box key={group.label}>
            <Typography
              variant="overline"
              sx={{
                px: 'var(--ob-space-200)',
                py: 'var(--ob-space-050)',
                display: 'block',
                fontSize: 'var(--ob-font-size-xs)',
                color: 'text.secondary',
                letterSpacing: '0.08em',
                lineHeight: 'var(--ob-line-height-loose)',
              }}
            >
              {group.label}
            </Typography>

            {group.items.map((item) => {
              flatIndex++
              const isSelected = flatIndex === selectedIndex
              const currentFlatIndex = flatIndex

              return (
                <ListItem
                  key={`${group.label}-${item.key}`}
                  id={`command-palette-item-${item.key}`}
                  role="option"
                  aria-selected={isSelected}
                  disablePadding
                  data-selected={isSelected}
                >
                  <ListItemButton
                    selected={isSelected}
                    onClick={() => !item.comingSoon && handleNavigate(item)}
                    onMouseEnter={() => setSelectedIndex(currentFlatIndex)}
                    sx={{
                      px: 'var(--ob-space-200)',
                      py: 'var(--ob-space-075)',
                      mx: 'var(--ob-space-050)',
                      borderRadius: 'var(--ob-radius-sm)',
                      borderLeft: '2px solid',
                      borderLeftColor: isSelected
                        ? 'var(--ob-color-brand-primary)'
                        : 'transparent',
                      '&.Mui-selected': {
                        bgcolor: 'action.hover',
                      },
                      '&.Mui-selected:hover': {
                        bgcolor: 'action.hover',
                      },
                    }}
                  >
                    <ListItemText
                      primary={
                        <Box
                          sx={{
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'space-between',
                          }}
                        >
                          <Typography
                            variant="body2"
                            sx={{
                              fontWeight: isSelected ? 600 : 400,
                              fontSize: 'var(--ob-font-size-sm)',
                            }}
                          >
                            {item.label}
                            {item.comingSoon && (
                              <Typography
                                component="span"
                                sx={{
                                  ml: 'var(--ob-space-100)',
                                  fontSize: 'var(--ob-font-size-xs)',
                                  color: 'text.disabled',
                                  fontStyle: 'italic',
                                }}
                              >
                                Coming soon
                              </Typography>
                            )}
                          </Typography>
                          {isSelected && (
                            <KeyboardReturnIcon
                              sx={{
                                fontSize: 14,
                                color: 'text.secondary',
                                flexShrink: 0,
                              }}
                            />
                          )}
                        </Box>
                      }
                      secondary={
                        item.description ? (
                          <Typography
                            variant="caption"
                            sx={{
                              color: 'text.secondary',
                              fontSize: 'var(--ob-font-size-xs)',
                              lineHeight: 'var(--ob-line-height-snug)',
                            }}
                          >
                            {item.description}
                          </Typography>
                        ) : undefined
                      }
                    />
                  </ListItemButton>
                </ListItem>
              )
            })}
          </Box>
        ))}
      </List>

      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'flex-end',
          gap: 'var(--ob-space-200)',
          px: 'var(--ob-space-200)',
          py: 'var(--ob-space-075)',
          borderTop: '1px solid',
          borderColor: 'divider',
          fontSize: 'var(--ob-font-size-xs)',
          color: 'text.secondary',
        }}
      >
        <Box
          component="span"
          sx={{
            display: 'flex',
            alignItems: 'center',
            gap: 'var(--ob-space-050)',
          }}
        >
          <Kbd>↑↓</Kbd> navigate
        </Box>
        <Box
          component="span"
          sx={{
            display: 'flex',
            alignItems: 'center',
            gap: 'var(--ob-space-050)',
          }}
        >
          <Kbd>↵</Kbd> open
        </Box>
        <Box
          component="span"
          sx={{
            display: 'flex',
            alignItems: 'center',
            gap: 'var(--ob-space-050)',
          }}
        >
          <Kbd>esc</Kbd> close
        </Box>
      </Box>
    </Dialog>
  )
}
