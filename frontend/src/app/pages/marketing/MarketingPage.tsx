import { useState } from 'react'
import { Box, Grid, Stack, Typography } from '@mui/material'
import { Check } from '@mui/icons-material'

import type { ProfessionalPackType } from '../../../api/agents'
import { useMarketingPacks } from './hooks/useMarketingPacks'
import { AlertBlock } from '../../../components/canonical/AlertBlock'
import { Button } from '../../../components/canonical/Button'
import { Card } from '../../../components/canonical/Card'
import { EmptyState } from '../../../components/canonical/EmptyState'
import { Input } from '../../../components/canonical/Input'

const PACK_TYPES: Array<{
  type: ProfessionalPackType
  label: string
  description: string
  icon: string
  estimatedTime: string
  estimatedSize: string
}> = [
  {
    type: 'universal',
    label: 'Universal Site Pack',
    description: 'Comprehensive analysis with all development scenarios',
    icon: '📊',
    estimatedTime: '45-60s',
    estimatedSize: '~2.5 MB',
  },
  {
    type: 'investment',
    label: 'Investment Memorandum',
    description: 'Financial analysis for institutional investors',
    icon: '💼',
    estimatedTime: '30-40s',
    estimatedSize: '~1.5 MB',
  },
  {
    type: 'sales',
    label: 'Sales Brief',
    description: 'Professional marketing material for property sales',
    icon: '🏢',
    estimatedTime: '20-30s',
    estimatedSize: '~1.2 MB',
  },
  {
    type: 'lease',
    label: 'Lease Brochure',
    description: 'Leasing collateral with amenity documentation',
    icon: '📋',
    estimatedTime: '20-30s',
    estimatedSize: '~1.2 MB',
  },
]

export function MarketingPage() {
  const {
    packs,
    isGenerating,
    generatingType,
    error,
    generatePack,
    clearError,
  } = useMarketingPacks()
  const [propertyId, setPropertyId] = useState('')
  const [selectedPackType, setSelectedPackType] =
    useState<ProfessionalPackType>('universal')
  const [notice, setNotice] = useState<string | null>(null)

  const selectedPackInfo = PACK_TYPES.find((p) => p.type === selectedPackType)

  async function handleGenerate() {
    if (!propertyId.trim()) {
      return
    }
    try {
      const summary = await generatePack(propertyId.trim(), selectedPackType)
      setNotice(summary.warning ?? null)
      setPropertyId('')
      clearError()
    } catch {
      setNotice(null)
    }
  }

  function handleDownload(downloadUrl: string) {
    window.open(downloadUrl, '_blank')
  }

  return (
    <Box sx={{ p: 4, maxWidth: 'var(--ob-max-width-content)', mx: 'auto' }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h1">Marketing Packs</Typography>
        <Typography variant="body1" color="text.secondary" sx={{ mt: 1 }}>
          Professional materials for investors and stakeholders
        </Typography>
      </Box>

      <Box sx={{ mb: 4 }}>
        <Typography variant="h2" sx={{ mb: 2 }}>
          Choose a template
        </Typography>
        <Grid container spacing={2}>
          {PACK_TYPES.map((pack) => {
            const isSelected = selectedPackType === pack.type
            const isDisabled = isGenerating
            return (
              <Grid item xs={12} md={6} key={pack.type}>
                <Card
                  variant={isSelected ? 'default' : 'ghost'}
                  hover={isDisabled ? 'none' : 'lift'}
                  onClick={
                    isDisabled
                      ? undefined
                      : () => setSelectedPackType(pack.type)
                  }
                  sx={{
                    opacity: isDisabled ? 0.6 : 1,
                    position: 'relative',
                    p: 'var(--ob-space-150)',
                    border: isSelected
                      ? '1px solid var(--ob-color-border-strong)'
                      : undefined,
                  }}
                >
                  {isSelected && (
                    <Box
                      sx={{
                        position: 'absolute',
                        top: 'var(--ob-space-100)',
                        right: 'var(--ob-space-100)',
                        width: 'var(--ob-size-icon-sm)',
                        height: 'var(--ob-size-icon-sm)',
                        borderRadius: 'var(--ob-radius-pill)',
                        background: 'var(--ob-color-text-primary)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: 'var(--ob-color-text-inverse)',
                        '& svg': { fontSize: 16 },
                      }}
                    >
                      <Check />
                    </Box>
                  )}

                  <Stack spacing={1}>
                    <Stack direction="row" spacing={1} alignItems="center">
                      <Box
                        component="span"
                        sx={{ fontSize: 'var(--ob-font-size-2xl)' }}
                      >
                        {pack.icon}
                      </Box>
                      <Typography variant="h3">{pack.label}</Typography>
                    </Stack>

                    <Typography variant="body2" color="text.secondary">
                      {pack.description}
                    </Typography>

                    <Stack direction="row" spacing={2}>
                      <Typography variant="caption" color="text.secondary">
                        ⏱️ {pack.estimatedTime}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        📦 {pack.estimatedSize}
                      </Typography>
                    </Stack>
                  </Stack>
                </Card>
              </Grid>
            )
          })}
        </Grid>
      </Box>

      <Card variant="default" sx={{ p: 'var(--ob-space-200)', mb: 4 }}>
        <Typography variant="h3" sx={{ mb: 2 }}>
          Generate {selectedPackInfo?.label}
        </Typography>

        <Stack spacing={2}>
          <Input
            label="Property ID"
            placeholder="Enter property identifier"
            value={propertyId}
            onChange={(event) => setPropertyId(event.target.value)}
            disabled={isGenerating}
            inputProps={{ inputMode: 'text' }}
          />

          <Button
            variant="primary"
            onClick={handleGenerate}
            disabled={isGenerating || propertyId.trim() === ''}
            fullWidth
          >
            {isGenerating && generatingType
              ? `Generating... (${selectedPackInfo?.estimatedTime})`
              : isGenerating
                ? 'Generating...'
                : 'Generate'}
          </Button>

          {error && (
            <AlertBlock type="error" onDismiss={clearError}>
              {error}
            </AlertBlock>
          )}
          {notice && <AlertBlock type="warning">{notice}</AlertBlock>}
        </Stack>
      </Card>

      <Stack
        direction="row"
        alignItems="baseline"
        justifyContent="space-between"
        sx={{ mb: 2 }}
      >
        <Typography variant="h2">Library</Typography>
        <Typography variant="body2" color="text.secondary">
          {packs.length} {packs.length === 1 ? 'pack' : 'packs'}
        </Typography>
      </Stack>

      {packs.length === 0 ? (
        <EmptyState
          icon={<span>📄</span>}
          title="No packs yet"
          description="Generated materials will appear here."
          size="md"
        />
      ) : (
        <Stack spacing={1}>
          {packs.map((pack, index) => (
            <Card
              key={`${pack.propertyId}-${pack.packType}-${pack.generatedAt}-${index}`}
              variant="default"
              hover="subtle"
              sx={{
                p: 'var(--ob-space-150)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                gap: 'var(--ob-space-150)',
              }}
            >
              <Box sx={{ flex: 1, minWidth: 0 }}>
                <Typography
                  variant="h4"
                  sx={{ fontWeight: 'var(--ob-font-weight-medium)' }}
                >
                  {formatPackLabel(pack.packType)}
                </Typography>
                <Stack direction="row" spacing={1} alignItems="center">
                  <Typography
                    variant="caption"
                    sx={{ fontFamily: 'var(--ob-font-family-mono)' }}
                  >
                    {pack.propertyId.length > 20
                      ? `${pack.propertyId.substring(0, 20)}...`
                      : pack.propertyId}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    ·
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {formatSize(pack.sizeBytes)}
                  </Typography>
                </Stack>
              </Box>

              <Box sx={{ flexShrink: 0 }}>
                {pack.downloadUrl ? (
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => handleDownload(pack.downloadUrl!)}
                  >
                    Download
                  </Button>
                ) : (
                  <Typography variant="caption" color="text.secondary">
                    {pack.isFallback ? 'Preview' : 'Processing'}
                  </Typography>
                )}
              </Box>
            </Card>
          ))}
        </Stack>
      )}
    </Box>
  )
}

function formatPackLabel(type: ProfessionalPackType) {
  switch (type) {
    case 'universal':
      return 'Universal Site Pack'
    case 'investment':
      return 'Investment Memorandum'
    case 'sales':
      return 'Sales Brief'
    case 'lease':
      return 'Lease Brochure'
    default:
      return type
  }
}

function formatSize(value: number | null) {
  if (!value || Number.isNaN(value)) {
    return '—'
  }
  if (value < 1024) {
    return `${value} B`
  }
  if (value < 1024 * 1024) {
    return `${(value / 1024).toFixed(1)} KB`
  }
  return `${(value / (1024 * 1024)).toFixed(1)} MB`
}
