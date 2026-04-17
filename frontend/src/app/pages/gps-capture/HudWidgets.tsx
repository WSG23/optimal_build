/**
 * HUD Widgets
 *
 * Right-panel widgets for the GPS capture page: Quick Analysis,
 * Market Intelligence, and Marketing Packs.
 * Extracted from GpsCapturePage for component size management.
 */

import LockIcon from '@mui/icons-material/Lock'
import PictureAsPdfIcon from '@mui/icons-material/PictureAsPdf'
import DescriptionIcon from '@mui/icons-material/Description'

import type {
  GpsCaptureSummaryWithFeatures,
  MarketIntelligenceSummary,
  ProfessionalPackType,
} from '../../../api/agents'
import {
  PACK_TYPES,
  formatScenarioLabel,
  formatPackLabel,
  humanizeMetricKey,
  formatMetricValue,
  extractReportValue,
  extractTransactions,
} from './gpsCaptureUtils'

interface HudWidgetsProps {
  quickAnalysis: GpsCaptureSummaryWithFeatures['quickAnalysis'] | null
  captureSummary: GpsCaptureSummaryWithFeatures | null
  marketSummary: MarketIntelligenceSummary | null
  marketLoading: boolean
  packLoadingType: ProfessionalPackType | null
  onGeneratePack: (packType: ProfessionalPackType) => void
}

export function HudWidgets({
  quickAnalysis,
  captureSummary,
  marketSummary,
  marketLoading,
  packLoadingType,
  onGeneratePack,
}: HudWidgetsProps) {
  return (
    <div className="gps-hud-group">
      {/* Widget 1: Quick Analysis */}
      <div className={`gps-hud-card ${!quickAnalysis ? 'locked' : ''}`}>
        <h3>
          Quick Analysis
          {!quickAnalysis && <LockIcon fontSize="small" />}
        </h3>

        {quickAnalysis ? (
          <div className="gps-hud-content">
            <ul className="gps-panel__list">
              {quickAnalysis.scenarios.slice(0, 1).map((scenario) => {
                const displayMetrics = Object.entries(scenario.metrics)
                  .filter(([key]) => key !== 'accuracy_bands')
                  .slice(0, 3)
                return (
                  <li key={scenario.scenario}>
                    <div className="gps-panel__headline">
                      <strong>{formatScenarioLabel(scenario.scenario)}</strong>
                    </div>
                    {displayMetrics.length > 0 && (
                      <dl className="gps-panel__metrics">
                        {displayMetrics.map(([k, v]) => (
                          <div key={k}>
                            <dt>{humanizeMetricKey(k)}</dt>
                            <dd>
                              {formatMetricValue(
                                v,
                                k,
                                captureSummary?.currencySymbol,
                              )}
                            </dd>
                          </div>
                        ))}
                      </dl>
                    )}
                  </li>
                )
              })}
              {quickAnalysis.scenarios.length > 1 && (
                <p className="gps-hud-more-scenarios">
                  + {quickAnalysis.scenarios.length - 1} more scenarios
                </p>
              )}
            </ul>
          </div>
        ) : (
          <div className="gps-hud-locked-overlay">
            <span>Awaiting Scan</span>
          </div>
        )}
      </div>

      {/* Widget 2: Market Intelligence */}
      <div className={`gps-hud-card ${!marketSummary ? 'locked' : ''}`}>
        <h3>
          Market Intelligence
          {!marketSummary && <LockIcon fontSize="small" />}
        </h3>
        {marketLoading ? (
          <div className="gps-hud-loading">
            <div className="gps-spinner gps-spinner--sm"></div>
            Decrypting market data...
          </div>
        ) : marketSummary ? (
          <div className="gps-hud-content">
            <dl className="gps-panel__metrics">
              <div>
                <dt>Type</dt>
                <dd>
                  {extractReportValue(marketSummary.report, 'property_type')}
                </dd>
              </div>
              <div>
                <dt>Zone</dt>
                <dd>{extractReportValue(marketSummary.report, 'location')}</dd>
              </div>
              <div>
                <dt>Trans</dt>
                <dd>{extractTransactions(marketSummary.report)} recent</dd>
              </div>
            </dl>
          </div>
        ) : (
          <div className="gps-hud-locked-overlay">
            <span>Downlink Offline</span>
          </div>
        )}
      </div>

      {/* Widget 3: Marketing Packs */}
      <div className={`gps-hud-card ${!captureSummary ? 'locked' : ''}`}>
        <h3>
          Marketing Packs
          {!captureSummary && <LockIcon fontSize="small" />}
        </h3>
        <div className="gps-pack-grid gps-hud-content">
          {PACK_TYPES.map((packType) => (
            <button
              key={packType}
              type="button"
              className="gps-pack-btn"
              disabled={packLoadingType === packType || !captureSummary}
              onClick={() => {
                onGeneratePack(packType)
              }}
            >
              {packLoadingType === packType ? (
                <div className="gps-spinner gps-spinner--xs"></div>
              ) : packType === 'investment' || packType === 'sales' ? (
                <PictureAsPdfIcon />
              ) : (
                <DescriptionIcon />
              )}
              <span>{formatPackLabel(packType).split(' ')[0]}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
