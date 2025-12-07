import { Layers, GridOn, Plumbing } from '@mui/icons-material'
import { ToggleButton, ToggleButtonGroup, Tooltip, Paper } from '@mui/material'
import { useState } from 'react'

// ... existing imports
import type { ReactNode } from 'react'

interface FeasibilityLayoutProps {
  /** Map component to render in the right panel */
  renderMap: () => ReactNode
  /** Address bar to render (usually floating over map) */
  renderAddressBar: () => ReactNode
  /** Content for the left control panel */
  children: ReactNode
  /** Sticky footer content for the left panel */
  renderFooter?: () => ReactNode
}

export function FeasibilityLayout({
  renderMap,
  renderAddressBar,
  children,
  renderFooter
}: FeasibilityLayoutProps) {
  const [layers, setLayers] = useState<string[]>(['zoning'])

  const handleLayerChange = (
    _event: React.MouseEvent<HTMLElement>, // Prefix with _ to suppress unused warning
    newLayers: string[],
  ) => {
    setLayers(newLayers)
    // In a real app, this would propagate to the map component via context or props
    console.log('Active Layers:', newLayers)
  }

  return (
    <div className="feasibility-split-layout" style={{
        display: 'flex',
        width: '100%',
        height: '100%',
        overflow: 'hidden',
        position: 'relative'
    }}>
      {/* Left Panel: Control Center (35% or 420px min) */}
      <aside
        className="feasibility-split-layout__controls"
        style={{
            flex: '0 0 420px', // Fixed width for stability or 35%
            maxWidth: '35%',
            minWidth: '350px',
            height: '100%',
            position: 'relative',
            zIndex: 10,
            transition: 'width 0.3s ease',
            display: 'flex',
            flexDirection: 'column'
        }}
      >
        <div className="feasibility-split-layout__scroll-container" style={{
            flex: 1, // Take available height
            overflowY: 'auto',
            background: 'var(--ob-color-bg-surface-glass-strong, rgba(255, 255, 255, 0.9))', // Fallback
            backdropFilter: 'blur(12px)',
            borderRight: '1px solid var(--ob-color-border-light)',
            padding: 'var(--ob-space-4)',
        }}>
          {children}
        </div>

        {/* Sticky Footer */}
        {renderFooter && (
            <div className="feasibility-split-layout__footer" style={{
                flex: '0 0 auto',
                background: 'var(--ob-color-bg-surface-main, #ffffff)',
                borderTop: '1px solid var(--ob-color-border-light)',
                borderRight: '1px solid var(--ob-color-border-light)',
                padding: 'var(--ob-space-4)',
                zIndex: 20
            }}>
                {renderFooter()}
            </div>
        )}
      </aside>

      {/* Right Panel: Context Map (Remaining) */}
      <main className="feasibility-split-layout__map" style={{
          flex: 1,
          position: 'relative',
          height: '100%',
          overflow: 'hidden'
      }}>
        {renderMap()}

        {/* Floating Search Bar container */}
        <div className="feasibility-split-layout__search-overlay" style={{
            position: 'absolute',
            top: '24px',
            left: '24px',
            right: '24px',
            maxWidth: '600px',
            zIndex: 20
        }}>
          {renderAddressBar()}
        </div>

        {/* Floating Layer Controls */}
        <Paper
            elevation={3}
            sx={{
                position: 'absolute',
                top: '24px',
                right: '24px',
                zIndex: 20,
                borderRadius: '8px',
                overflow: 'hidden',
                background: 'rgba(255, 255, 255, 0.9)',
                backdropFilter: 'blur(8px)'
            }}
        >
            <ToggleButtonGroup
                value={layers}
                onChange={handleLayerChange}
                aria-label="map layers"
                orientation="vertical"
                size="small"
            >
                <Tooltip title="Zoning Envelope" placement="left">
                    <ToggleButton value="zoning" aria-label="zoning envelope">
                        <Layers fontSize="small" />
                    </ToggleButton>
                </Tooltip>
                <Tooltip title="Structural Grid" placement="left">
                    <ToggleButton value="structure" aria-label="structural grid">
                        <GridOn fontSize="small" />
                    </ToggleButton>
                </Tooltip>
                <Tooltip title="MEP Risers" placement="left">
                    <ToggleButton value="mep" aria-label="mep risers">
                        <Plumbing fontSize="small" />
                    </ToggleButton>
                </Tooltip>
            </ToggleButtonGroup>
        </Paper>
      </main>
    </div>
  )
}
