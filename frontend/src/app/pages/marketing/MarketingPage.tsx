import { useMemo, useState } from 'react'
import type { ProfessionalPackType } from '../../../api/agents'
import { useMarketingPacks } from './hooks/useMarketingPacks'

const PACK_TYPES: ProfessionalPackType[] = [
  'universal',
  'investment',
  'sales',
  'lease',
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
  const [notes, setNotes] = useState('')
  const [modules] = useState(() => ({
    siteOverview: true,
    quickAnalysis: true,
    marketIntel: true,
    advisoryHighlights: false,
  }))

  const formattedDate = useMemo(
    () => new Date().toLocaleString(undefined, { dateStyle: 'medium' }),
    [],
  )

  async function handleGenerate() {
    if (!propertyId.trim()) {
      return
    }
    try {
      await generatePack(propertyId.trim(), selectedPackType)
      setNotes('')
      clearError()
    } catch {
      // error handled in hook state
    }
  }

  return (
    <div className="mkt-page">
      <section className="mkt-card">
        <header className="mkt-card__header">
          <div>
            <h2>Generate a marketing pack</h2>
            <p>
              Create investor-ready documents using captured site data. Select a
              property, pick a template, and add optional notes before
              generation.
            </p>
          </div>
          <span className="mkt-card__timestamp">Today: {formattedDate}</span>
        </header>
        <div className="mkt-generator">
          <div className="mkt-form">
            <label htmlFor="property-id">Property ID</label>
            <input
              id="property-id"
              placeholder="e.g. 4b7c0f9e-..."
              value={propertyId}
              onChange={(event) => setPropertyId(event.target.value)}
            />
            <label htmlFor="pack-type">Pack template</label>
            <select
              id="pack-type"
              value={selectedPackType}
              onChange={(event) =>
                setSelectedPackType(event.target.value as ProfessionalPackType)
              }
            >
              {PACK_TYPES.map((type) => (
                <option key={type} value={type}>
                  {formatPackLabel(type)}
                </option>
              ))}
            </select>
          </div>
          <div className="mkt-modules">
            <h3>Included modules</h3>
            <ul>
              <li>
                <input type="checkbox" checked={modules.siteOverview} readOnly />
                <span>Site overview & zoning notes</span>
              </li>
              <li>
                <input type="checkbox" checked={modules.quickAnalysis} readOnly />
                <span>Quick analysis scenarios</span>
              </li>
              <li>
                <input type="checkbox" checked={modules.marketIntel} readOnly />
                <span>Market intelligence snapshot</span>
              </li>
              <li>
                <input
                  type="checkbox"
                  checked={modules.advisoryHighlights}
                  readOnly
                />
                <span>Advisory highlights (coming soon)</span>
              </li>
            </ul>
          </div>
          <div className="mkt-notes">
            <label htmlFor="pack-notes">Optional memo</label>
            <textarea
              id="pack-notes"
              placeholder="Add context for developers or investors…"
              value={notes}
              onChange={(event) => setNotes(event.target.value)}
            />
          </div>
        </div>
        <footer className="mkt-actions">
          <button
            type="button"
            onClick={handleGenerate}
            disabled={isGenerating || propertyId.trim() === ''}
          >
            {isGenerating ? 'Generating…' : 'Generate pack'}
          </button>
          {error && <span className="mkt-error">{error}</span>}
        </footer>
      </section>

      <section className="mkt-card">
        <h2>Generated packs</h2>
        {packs.length === 0 ? (
          <p>No packs generated in this session.</p>
        ) : (
          <table className="mkt-table">
            <thead>
              <tr>
                <th>Pack</th>
                <th>Property</th>
                <th>Generated</th>
                <th>Size</th>
                <th>Download</th>
              </tr>
            </thead>
            <tbody>
              {packs.map((pack) => (
                <tr key={`${pack.propertyId}-${pack.packType}-${pack.generatedAt}`}>
                  <td>
                    <span className="mkt-badge">
                      {formatPackLabel(pack.packType)}
                    </span>
                  </td>
                  <td>{pack.propertyId}</td>
                  <td>{new Date(pack.generatedAt).toLocaleString()}</td>
                  <td>{formatSize(pack.sizeBytes)}</td>
                  <td>
                    {pack.downloadUrl ? (
                      <a href={pack.downloadUrl} target="_blank" rel="noreferrer">
                        Download
                      </a>
                    ) : (
                      'Pending link'
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      <section className="mkt-card">
        <h2>Sharing & follow-up</h2>
        <p>
          Sharing workflows (recipient list, expiry controls, audit log) will be
          added once backend endpoints are available. For now, download packs and
          share externally.
        </p>
        <ul>
          <li>Automatic sharing reminders and recipient tracking (planned)</li>
          <li>Branding customization and localized templates</li>
          <li>Developer/investor access portal with audit trail</li>
        </ul>
      </section>

      {generatingType && (
        <div className="mkt-toast">
          <span>
            Generating {formatPackLabel(generatingType)} pack for {propertyId ||
              'property'}…
          </span>
        </div>
      )}
    </div>
  )
}

function formatPackLabel(type: ProfessionalPackType) {
  switch (type) {
    case 'universal':
      return 'Universal pack'
    case 'investment':
      return 'Investment memo'
    case 'sales':
      return 'Sales brief'
    case 'lease':
      return 'Lease brochure'
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

