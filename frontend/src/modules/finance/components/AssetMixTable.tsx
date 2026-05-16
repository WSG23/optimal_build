import { type CSSProperties, type ReactElement, memo } from 'react'
import {
  Box,
  Typography,
  IconButton,
  Stack,
  alpha,
  useTheme,
} from '@mui/material'
import Close from '@mui/icons-material/Close'
import { List as VirtualList } from 'react-window'
import { Button } from '../../../components/canonical/Button'
import { Card } from '../../../components/canonical/Card'
import { Input } from '../../../components/canonical/Input'
import { useTranslation } from '../../../i18n'
import type { AssetFormRow } from './financeScenarioConstants'

interface AssetMixTableProps {
  assets: AssetFormRow[]
  isCompactLayout: boolean
  onAssetChange: (id: string, key: keyof AssetFormRow, value: string) => void
  onAddAsset: () => void
  onRemoveAsset: (id: string) => void
  onReset: () => void
}

export function AssetMixTable({
  assets,
  isCompactLayout,
  onAssetChange,
  onAddAsset,
  onRemoveAsset,
  onReset,
}: AssetMixTableProps) {
  const { t } = useTranslation()
  const theme = useTheme()

  return (
    <Card sx={{ overflow: 'hidden' }}>
      <Box
        sx={{
          px: 'var(--ob-space-150)',
          py: 'var(--ob-space-125)',
          borderBottom: 1,
          borderColor: 'divider',
          bgcolor: alpha(theme.palette.background.default, 0.5),
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <Typography
          variant="h6"
          sx={{ fontWeight: 'var(--ob-font-weight-semibold)' }}
        >
          {t('finance.scenarioCreator.title')}
        </Typography>
        <Button variant="ghost" size="sm" onClick={onReset}>
          {t('finance.scenarioCreator.actions.reset')}
        </Button>
      </Box>

      {isCompactLayout ? (
        <CompactAssetCards
          assets={assets}
          onAssetChange={onAssetChange}
          onRemoveAsset={onRemoveAsset}
        />
      ) : (
        <DesktopAssetTable
          assets={assets}
          onAssetChange={onAssetChange}
          onRemoveAsset={onRemoveAsset}
        />
      )}

      <Box
        sx={{
          p: 'var(--ob-space-100)',
          borderTop: 1,
          borderColor: 'divider',
        }}
      >
        <Button variant="ghost" size="sm" onClick={onAddAsset}>
          {t('finance.scenarioCreator.actions.addAsset')}
        </Button>
      </Box>
    </Card>
  )
}

// ============================================================================
// Virtualization Constants
// ============================================================================

/** Only virtualize when the row count exceeds this threshold */
const VIRTUALIZE_THRESHOLD = 20

/** Height of a single asset table row in pixels */
const ROW_HEIGHT = 52

/** Maximum visible rows before scrolling */
const MAX_VISIBLE_ROWS = 20

interface AssetRowsProps {
  assets: AssetFormRow[]
  onAssetChange: (id: string, key: keyof AssetFormRow, value: string) => void
  onRemoveAsset: (id: string) => void
}

const CompactAssetCards = memo(function CompactAssetCards({
  assets,
  onAssetChange,
  onRemoveAsset,
}: AssetRowsProps) {
  const { t } = useTranslation()

  return (
    <Stack spacing="var(--ob-space-100)" sx={{ p: 'var(--ob-space-100)' }}>
      {assets.map((asset, index) => (
        <Box
          key={asset.id}
          sx={{
            border: '1px solid',
            borderColor: 'divider',
            borderRadius: 'var(--ob-radius-sm)',
            p: 'var(--ob-space-100)',
          }}
        >
          <Stack
            direction="row"
            justifyContent="space-between"
            alignItems="center"
            spacing="var(--ob-space-100)"
            sx={{ mb: 'var(--ob-space-100)' }}
          >
            <Typography
              variant="subtitle2"
              sx={{ fontWeight: 'var(--ob-font-weight-semibold)' }}
            >
              Asset {index + 1}
            </Typography>
            <IconButton
              aria-label={t('finance.scenarioCreator.actions.remove')}
              size="small"
              onClick={() => {
                onRemoveAsset(asset.id)
              }}
              disabled={assets.length <= 1}
              sx={{
                borderRadius: 'var(--ob-radius-xs)',
                border: 'var(--ob-border-fine)',
              }}
            >
              <Close fontSize="small" />
            </IconButton>
          </Stack>

          <Stack spacing="var(--ob-space-100)">
            <Input
              label={t('finance.scenarioCreator.assets.headers.assetType')}
              value={asset.assetType}
              onChange={(e) => {
                onAssetChange(asset.id, 'assetType', e.target.value)
              }}
              placeholder="Type"
              size="small"
            />
            <Input
              label={t('finance.scenarioCreator.fields.allocation')}
              value={asset.allocationPct}
              onChange={(e) => {
                onAssetChange(asset.id, 'allocationPct', e.target.value)
              }}
              type="number"
              size="small"
              endAdornment="%"
            />
            <Input
              label={t('finance.scenarioCreator.assets.headers.nia')}
              value={asset.niaSqm}
              onChange={(e) => {
                onAssetChange(asset.id, 'niaSqm', e.target.value)
              }}
              type="number"
              size="small"
            />
            <Input
              label={t('finance.scenarioCreator.assets.headers.rent')}
              value={asset.rentPsmMonth}
              onChange={(e) => {
                onAssetChange(asset.id, 'rentPsmMonth', e.target.value)
              }}
              type="number"
              size="small"
              startAdornment="$"
            />
            <Input
              label={t('finance.scenarioCreator.assets.headers.vacancy')}
              value={asset.vacancyPct}
              onChange={(e) => {
                onAssetChange(asset.id, 'vacancyPct', e.target.value)
              }}
              type="number"
              size="small"
              endAdornment="%"
            />
            <Input
              label={t('finance.scenarioCreator.assets.headers.capex')}
              value={asset.estimatedCapex}
              onChange={(e) => {
                onAssetChange(asset.id, 'estimatedCapex', e.target.value)
              }}
              type="number"
              size="small"
              startAdornment="$"
            />
            <Box>
              <Typography variant="caption" color="text.secondary">
                {t('finance.scenarioCreator.assets.headers.revenue')}
              </Typography>
              <Typography
                variant="body2"
                sx={{
                  mt: 'var(--ob-space-025)',
                  fontFamily: 'var(--ob-font-family-mono)',
                  fontWeight: 'var(--ob-font-weight-semibold)',
                }}
              >
                ${Number(asset.estimatedRevenue).toLocaleString()}
              </Typography>
            </Box>
          </Stack>
        </Box>
      ))}
    </Stack>
  )
})

// ============================================================================
// Virtualized Asset Row (react-window v2 API)
// ============================================================================

interface VirtualAssetRowProps {
  assets: AssetFormRow[]
  onAssetChange: (id: string, key: keyof AssetFormRow, value: string) => void
  onRemoveAsset: (id: string) => void
  assetsLength: number
  removeLabel: string
}

function VirtualAssetRow(
  props: {
    ariaAttributes: {
      'aria-posinset': number
      'aria-setsize': number
      role: 'listitem'
    }
    index: number
    style: CSSProperties
  } & VirtualAssetRowProps,
): ReactElement {
  const {
    index,
    style,
    assets,
    onAssetChange,
    onRemoveAsset,
    assetsLength,
    removeLabel,
  } = props
  const asset = assets[index]
  return (
    <table
      style={{
        ...style,
        width: '100%',
        borderCollapse: 'separate',
        borderSpacing: 0,
        tableLayout: 'fixed',
      }}
    >
      <tbody>
        <AssetTableRow
          asset={asset}
          onAssetChange={onAssetChange}
          onRemoveAsset={onRemoveAsset}
          assetsLength={assetsLength}
          removeLabel={removeLabel}
        />
      </tbody>
    </table>
  )
}

// ============================================================================
// Shared Asset Table Row
// ============================================================================

interface AssetTableRowProps {
  asset: AssetFormRow
  onAssetChange: (id: string, key: keyof AssetFormRow, value: string) => void
  onRemoveAsset: (id: string) => void
  assetsLength: number
  removeLabel: string
}

const AssetTableRow = memo(function AssetTableRow({
  asset,
  onAssetChange,
  onRemoveAsset,
  assetsLength,
  removeLabel,
}: AssetTableRowProps) {
  return (
    <tr key={asset.id}>
      <td>
        <Input
          value={asset.assetType}
          onChange={(e) => {
            onAssetChange(asset.id, 'assetType', e.target.value)
          }}
          placeholder="Type"
          size="small"
        />
      </td>
      <td>
        <Input
          value={asset.allocationPct}
          onChange={(e) => {
            onAssetChange(asset.id, 'allocationPct', e.target.value)
          }}
          type="number"
          size="small"
          endAdornment="%"
        />
      </td>
      <td>
        <Input
          value={asset.niaSqm}
          onChange={(e) => {
            onAssetChange(asset.id, 'niaSqm', e.target.value)
          }}
          type="number"
          size="small"
        />
      </td>
      <td>
        <Input
          value={asset.rentPsmMonth}
          onChange={(e) => {
            onAssetChange(asset.id, 'rentPsmMonth', e.target.value)
          }}
          type="number"
          size="small"
          startAdornment="$"
        />
      </td>
      <td>
        <Input
          value={asset.vacancyPct}
          onChange={(e) => {
            onAssetChange(asset.id, 'vacancyPct', e.target.value)
          }}
          type="number"
          size="small"
          endAdornment="%"
        />
      </td>
      <td>
        <Typography
          variant="body2"
          sx={{
            fontFamily: 'var(--ob-font-family-mono)',
            fontWeight: 'var(--ob-font-weight-semibold)',
          }}
        >
          ${Number(asset.estimatedRevenue).toLocaleString()}
        </Typography>
      </td>
      <td>
        <Input
          value={asset.estimatedCapex}
          onChange={(e) => {
            onAssetChange(asset.id, 'estimatedCapex', e.target.value)
          }}
          type="number"
          size="small"
          startAdornment="$"
        />
      </td>
      <td>
        <IconButton
          aria-label={removeLabel}
          size="small"
          onClick={() => {
            onRemoveAsset(asset.id)
          }}
          disabled={assetsLength <= 1}
          sx={{
            borderRadius: 'var(--ob-radius-xs)',
            border: 'var(--ob-border-fine)',
          }}
        >
          <Close fontSize="small" />
        </IconButton>
      </td>
    </tr>
  )
})

// ============================================================================
// Desktop Asset Table (with optional virtualization)
// ============================================================================

const tableSx = {
  width: '100%',
  minWidth: '960px',
  borderCollapse: 'separate',
  borderSpacing: 0,
  '& th': {
    px: 'var(--ob-space-100)',
    py: 'var(--ob-space-100)',
    textAlign: 'left',
    color: 'text.secondary',
    fontSize: 'var(--ob-font-size-xs)',
    fontWeight: 'var(--ob-font-weight-semibold)',
    textTransform: 'uppercase',
    letterSpacing: 'var(--ob-letter-spacing-wider)',
    whiteSpace: 'nowrap',
    borderBottom: 1,
    borderColor: 'divider',
  },
  '& td': {
    px: 'var(--ob-space-100)',
    py: 'var(--ob-space-100)',
    borderBottom: 1,
    borderColor: 'divider',
    verticalAlign: 'middle',
  },
  '& tr:last-child td': {
    borderBottom: 'none',
  },
  '& th:nth-of-type(1), & td:nth-of-type(1)': { minWidth: '160px' },
  '& th:nth-of-type(2), & td:nth-of-type(2)': {
    minWidth: 'var(--ob-size-drop-zone)',
  },
  '& th:nth-of-type(3), & td:nth-of-type(3)': { minWidth: '112px' },
  '& th:nth-of-type(4), & td:nth-of-type(4)': { minWidth: '128px' },
  '& th:nth-of-type(5), & td:nth-of-type(5)': { minWidth: '128px' },
  '& th:nth-of-type(6), & td:nth-of-type(6)': { minWidth: '140px' },
  '& th:nth-of-type(7), & td:nth-of-type(7)': { minWidth: '140px' },
  '& th:nth-of-type(8), & td:nth-of-type(8)': {
    minWidth: '72px',
    width: '72px',
  },
} as const

const DesktopAssetTable = memo(function DesktopAssetTable({
  assets,
  onAssetChange,
  onRemoveAsset,
}: AssetRowsProps) {
  const { t } = useTranslation()
  const shouldVirtualize = assets.length > VIRTUALIZE_THRESHOLD
  const removeLabel = t('finance.scenarioCreator.actions.remove')

  return (
    <Box sx={{ overflowX: 'auto' }}>
      <Box component="table" sx={tableSx}>
        <thead>
          <tr>
            <th>{t('finance.scenarioCreator.assets.headers.assetType')}</th>
            <th>{t('finance.scenarioCreator.fields.allocation')}</th>
            <th>{t('finance.scenarioCreator.assets.headers.nia')}</th>
            <th>{t('finance.scenarioCreator.assets.headers.rent')}</th>
            <th>{t('finance.scenarioCreator.assets.headers.vacancy')}</th>
            <th>{t('finance.scenarioCreator.assets.headers.revenue')}</th>
            <th>{t('finance.scenarioCreator.assets.headers.capex')}</th>
            <th>{removeLabel}</th>
          </tr>
        </thead>
        {shouldVirtualize ? (
          <tbody>
            <tr>
              <td colSpan={8} style={{ padding: 0, border: 'none' }}>
                <VirtualList
                  rowComponent={VirtualAssetRow}
                  rowCount={assets.length}
                  rowHeight={ROW_HEIGHT}
                  rowProps={{
                    assets,
                    onAssetChange,
                    onRemoveAsset,
                    assetsLength: assets.length,
                    removeLabel,
                  }}
                  overscanCount={5}
                  style={{
                    height:
                      Math.min(assets.length, MAX_VISIBLE_ROWS) * ROW_HEIGHT,
                  }}
                />
              </td>
            </tr>
          </tbody>
        ) : (
          <tbody>
            {assets.map((asset) => (
              <AssetTableRow
                key={asset.id}
                asset={asset}
                onAssetChange={onAssetChange}
                onRemoveAsset={onRemoveAsset}
                assetsLength={assets.length}
                removeLabel={removeLabel}
              />
            ))}
          </tbody>
        )}
      </Box>
    </Box>
  )
})
