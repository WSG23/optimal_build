import { Layers, GridOn, Plumbing } from '@mui/icons-material'
import { ToggleButton, ToggleButtonGroup, Paper } from '@mui/material'
import { useState } from 'react'

import type { ReactNode } from 'react'

interface FeasibilityLayoutProps {
  /** Output content to render in the main panel. Receives active layer IDs. */
  renderOutput: (activeLayers: string[]) => ReactNode
  /** Content for the left control panel */
  children: ReactNode
  /** Sticky footer content for the left panel */
  renderFooter?: () => ReactNode
}

export function FeasibilityLayout({
  renderOutput,
  children,
  renderFooter,
}: FeasibilityLayoutProps) {
  const [layers, setLayers] = useState<string[]>(['zoning'])

  const handleLayerChange = (
    _event: React.MouseEvent<HTMLElement>,
    newLayers: string[],
  ) => {
    setLayers(newLayers)
    console.log('Active Layers:', newLayers)
  }

  return (
    <div className="feasibility-workspace">
      <div className="feasibility-workspace__grid">
        <aside
          className="feasibility-workspace__sidebar"
          data-testid="feasibility-controls"
        >
          <div className="feasibility-workspace__sidebar-scroll">
            {children}
          </div>
          {renderFooter && (
            <div className="feasibility-workspace__sidebar-footer">
              {renderFooter()}
            </div>
          )}
        </aside>

        <section className="feasibility-workspace__main">
          {renderOutput(layers)}
          <div className="feasibility-workspace__layer-controls">
            <Paper
              elevation={0}
              sx={{
                borderRadius: 'var(--ob-radius-sm)',
                overflow: 'visible',
                background: 'var(--ob-color-bg-surface)',
                border: '1px solid var(--ob-color-border-subtle)',
                backdropFilter: 'blur(var(--ob-blur-md))',
                boxShadow: 'var(--ob-shadow-md)',
              }}
            >
              <ToggleButtonGroup
                value={layers}
                onChange={handleLayerChange}
                exclusive={false}
                aria-label="visualization layers"
                aria-multiselectable="true"
                orientation="vertical"
                size="small"
                sx={{
                  '& .MuiToggleButton-root': {
                    color: 'var(--ob-color-text-secondary)',
                    border: 'none',
                    borderBottom: '1px solid var(--ob-color-border-subtle)',
                    '&.Mui-selected': {
                      color: 'var(--ob-color-brand-primary)',
                      background: 'var(--ob-color-brand-soft)',
                      boxShadow: 'inset 2px 0 0 var(--ob-color-neon-cyan)',
                      '&:hover': {
                        background: 'var(--ob-color-brand-muted)',
                      },
                    },
                    '&:hover': {
                      background: 'var(--ob-color-action-hover)',
                    },
                    '&:last-child': {
                      borderBottom: 'none',
                    },
                  },
                }}
              >
                <ToggleButton
                  value="zoning"
                  aria-label="zoning envelope"
                  title="Zoning Envelope"
                  data-tooltip="Zoning Envelope"
                  className="feasibility-layer-toggle"
                >
                  <Layers fontSize="small" />
                </ToggleButton>
                <ToggleButton
                  value="structure"
                  aria-label="structural grid"
                  title="Structural Grid"
                  data-tooltip="Structural Grid"
                  className="feasibility-layer-toggle"
                >
                  <GridOn fontSize="small" />
                </ToggleButton>
                <ToggleButton
                  value="mep"
                  aria-label="mep risers"
                  title="MEP Risers"
                  data-tooltip="MEP Risers"
                  className="feasibility-layer-toggle"
                >
                  <Plumbing fontSize="small" />
                </ToggleButton>
              </ToggleButtonGroup>
            </Paper>
          </div>
        </section>
      </div>
    </div>
  )
}
