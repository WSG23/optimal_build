import { Layers, GridOn, Plumbing } from '@mui/icons-material'
import {
  ToggleButton,
  ToggleButtonGroup,
  Tooltip,
  Paper,
  Box,
} from '@mui/material'
import { useState } from 'react'

import type { ReactNode } from 'react'
import { LiveScorecard } from './LiveScorecard'

interface FeasibilityLayoutProps {
  /** Map component to render in the right panel */
  renderMap: () => ReactNode
  /** Content for the left control panel */
  children: ReactNode
  /** Sticky footer content for the left panel */
  renderFooter?: () => ReactNode
  /** Props for live scorecard */
  scorecardProps?: {
    siteArea?: number
    efficiencyRatio?: number
    floorToFloor?: number
    plotRatio?: number
    visible?: boolean
  }
}

export function FeasibilityLayout({
  renderMap,
  children,
  renderFooter,
  scorecardProps,
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
    <div
      className="feasibility-split-layout"
      style={{
        position: 'relative',
        width: '100vw',
        height: '100vh', // Full viewport (minus header usually, handled by AppLayout)
        overflow: 'hidden',
        display: 'flex',
      }}
    >
      {/*
        Full Screen Map Backdrop
        The map takes up the entire container. The sidebar floats on top.
      */}
      <div
        className="feasibility-split-layout__map-backdrop"
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          zIndex: 1,
        }}
      >
        {renderMap()}
      </div>

      {/*
        Floating Glass Sidebar
        Positioned on the left with margin.
      */}
      <aside
        className="feasibility-split-layout__sidebar"
        style={{
          position: 'relative',
          zIndex: 10,
          width: '420px',
          height: 'calc(100% - 32px)', // Top/Bottom margin
          margin: '16px 0 16px 24px', // Floating margin
          display: 'flex',
          flexDirection: 'column',
          gap: '0',
          borderRadius: '16px', // Rounded corners for floating feel
          background: 'rgba(20, 20, 25, 0.65)', // Darker glass for "Command Center"
          backdropFilter: 'blur(24px) saturate(180%)',
          WebkitBackdropFilter: 'blur(24px) saturate(180%)',
          boxShadow: '0 8px 32px 0 rgba(0, 0, 0, 0.3)',
          border: '1px solid rgba(255, 255, 255, 0.08)',
          overflow: 'hidden',
        }}
        data-testid="feasibility-controls"
      >
        {/* Scrollable Content Area */}
        <div
          className="feasibility-split-layout__scroll-content"
          style={{
            flex: 1,
            overflowY: 'auto',
            padding: '24px',
            scrollbarWidth: 'thin',
          }}
        >
          {children}
        </div>

        {/* Sticky Footer for "Run Simulation" */}
        {renderFooter && (
          <div
            className="feasibility-split-layout__footer"
            style={{
              flex: '0 0 auto',
              padding: '16px 24px 24px',
              background:
                'linear-gradient(to top, rgba(20, 20, 25, 0.95), rgba(20, 20, 25, 0.0))', // Fade in
              zIndex: 20,
            }}
          >
            {renderFooter()}
          </div>
        )}
      </aside>

      {/* Live Feasibility Scorecard (Top Right, offset) */}
      {scorecardProps && (
        <LiveScorecard
          siteArea={scorecardProps.siteArea}
          efficiencyRatio={scorecardProps.efficiencyRatio}
          floorToFloor={scorecardProps.floorToFloor}
          plotRatio={scorecardProps.plotRatio}
          visible={scorecardProps.visible}
        />
      )}

      {/* Floating Layer Controls (Top Right) */}
      <Box
        sx={{
          position: 'absolute',
          top: '24px',
          right: '24px',
          zIndex: 20,
        }}
      >
        <Paper
          elevation={0}
          sx={{
            borderRadius: '8px',
            overflow: 'hidden',
            background: 'rgba(20, 20, 30, 0.7)',
            backdropFilter: 'blur(12px)',
            border: '1px solid rgba(255,255,255,0.1)',
            color: 'white',
          }}
        >
          <ToggleButtonGroup
            value={layers}
            onChange={handleLayerChange}
            aria-label="map layers"
            orientation="vertical"
            size="small"
            sx={{
              '& .MuiToggleButton-root': {
                color: 'rgba(255,255,255,0.7)',
                border: 'none',
                borderBottom: '1px solid rgba(255,255,255,0.05)',
                '&.Mui-selected': {
                  color: '#06b6d4', // Cyan
                  background: 'rgba(6, 182, 212, 0.15)',
                  '&:hover': {
                    background: 'rgba(6, 182, 212, 0.25)',
                  },
                },
                '&:hover': {
                  background: 'rgba(255,255,255,0.1)',
                },
                '&:last-child': {
                  borderBottom: 'none',
                },
              },
            }}
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
      </Box>
    </div>
  )
}
