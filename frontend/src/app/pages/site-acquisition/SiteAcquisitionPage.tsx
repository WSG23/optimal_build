import { useEffect, useMemo, useState } from 'react'
import {
  capturePropertyForDevelopment,
  fetchChecklistSummary,
  fetchPropertyChecklist,
  updateChecklistItem,
  type ChecklistItem,
  type ChecklistSummary,
  type DevelopmentScenario,
  type SiteAcquisitionResult,
} from '../../../api/siteAcquisition'

const SCENARIO_OPTIONS: Array<{
  value: DevelopmentScenario
  label: string
  description: string
  icon: string
}> = [
  {
    value: 'raw_land',
    label: 'New Construction',
    description: 'Raw land development with ground-up construction',
    icon: '🏗️',
  },
  {
    value: 'existing_building',
    label: 'Renovation',
    description: 'Existing building renovation and modernization',
    icon: '🔨',
  },
  {
    value: 'heritage_property',
    label: 'Heritage Integration',
    description: 'Heritage-protected property with conservation requirements',
    icon: '🏛️',
  },
  {
    value: 'underused_asset',
    label: 'Adaptive Reuse',
    description: 'Underutilized asset repositioning and value-add',
    icon: '♻️',
  },
  {
    value: 'mixed_use_redevelopment',
    label: 'Mixed-Use Redevelopment',
    description: 'Complex mixed-use project with residential, commercial, and retail components',
    icon: '🏙️',
  },
]

function formatCategoryName(category: string): string {
  return category
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

function computeChecklistSummary(
  items: ChecklistItem[],
  propertyId: string,
): ChecklistSummary {
  const totals = {
    total: items.length,
    completed: 0,
    inProgress: 0,
    pending: 0,
    notApplicable: 0,
  }

  const byCategoryStatus: Record<
    string,
    {
      total: number
      completed: number
      inProgress: number
      pending: number
      notApplicable: number
    }
  > = {}

  items.forEach((item) => {
    switch (item.status) {
      case 'completed':
        totals.completed += 1
        break
      case 'in_progress':
        totals.inProgress += 1
        break
      case 'not_applicable':
        totals.notApplicable += 1
        break
      default:
        totals.pending += 1
        break
    }

    const categoryEntry =
      byCategoryStatus[item.category] ?? {
        total: 0,
        completed: 0,
        inProgress: 0,
        pending: 0,
        notApplicable: 0,
      }

    categoryEntry.total += 1
    if (item.status === 'completed') {
      categoryEntry.completed += 1
    } else if (item.status === 'in_progress') {
      categoryEntry.inProgress += 1
    } else if (item.status === 'not_applicable') {
      categoryEntry.notApplicable += 1
    } else {
      categoryEntry.pending += 1
    }

    byCategoryStatus[item.category] = categoryEntry
  })

  const completionPercentage =
    totals.total > 0 ? Math.round((totals.completed / totals.total) * 100) : 0

  return {
    propertyId,
    total: totals.total,
    completed: totals.completed,
    inProgress: totals.inProgress,
    pending: totals.pending,
    notApplicable: totals.notApplicable,
    completionPercentage,
    byCategoryStatus,
  }
}

export function SiteAcquisitionPage() {
  const [latitude, setLatitude] = useState('1.3000')
  const [longitude, setLongitude] = useState('103.8500')
  const [selectedScenarios, setSelectedScenarios] = useState<DevelopmentScenario[]>([])
  const [isCapturing, setIsCapturing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [capturedProperty, setCapturedProperty] = useState<SiteAcquisitionResult | null>(null)

  // Checklist state
  const [checklistItems, setChecklistItems] = useState<ChecklistItem[]>([])
  const [checklistSummary, setChecklistSummary] = useState<ChecklistSummary | null>(null)
  const [isLoadingChecklist, setIsLoadingChecklist] = useState(false)
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null)
  const [availableChecklistScenarios, setAvailableChecklistScenarios] = useState<
    DevelopmentScenario[]
  >([])
  const [activeScenario, setActiveScenario] = useState<DevelopmentScenario | 'all'>('all')

  const scenarioLookup = useMemo(
    () => new Map(SCENARIO_OPTIONS.map((option) => [option.value, option])),
    [],
  )

  // Load checklist when property is captured
  useEffect(() => {
    async function loadChecklist() {
      if (!capturedProperty) {
        setChecklistItems([])
        setChecklistSummary(null)
        setAvailableChecklistScenarios([])
        setActiveScenario('all')
        setSelectedCategory(null)
        return
      }

      setIsLoadingChecklist(true)
      try {
        const [items, summary] = await Promise.all([
          fetchPropertyChecklist(capturedProperty.propertyId),
          fetchChecklistSummary(capturedProperty.propertyId),
        ])
        const sortedItems = [...items].sort((a, b) => {
          const orderA = a.displayOrder ?? Number.MAX_SAFE_INTEGER
          const orderB = b.displayOrder ?? Number.MAX_SAFE_INTEGER
          if (orderA !== orderB) {
            return orderA - orderB
          }
          return a.itemTitle.localeCompare(b.itemTitle)
        })
        setChecklistItems(sortedItems)
        setChecklistSummary(summary)
        const scenarioSet = new Set<DevelopmentScenario>()
        sortedItems.forEach((item) => {
          if (scenarioLookup.has(item.developmentScenario)) {
            scenarioSet.add(item.developmentScenario)
          }
        })
        const scenarios = Array.from(scenarioSet)
        setAvailableChecklistScenarios(scenarios)
        setActiveScenario((prev) => {
          if (scenarios.length === 0) {
            return 'all'
          }
          if (prev !== 'all' && scenarios.includes(prev)) {
            return prev
          }
          if (scenarios.length === 1) {
            return scenarios[0]
          }
          return 'all'
        })
        setSelectedCategory(null)
      } catch (err) {
        console.error('Failed to load checklist:', err)
      } finally {
        setIsLoadingChecklist(false)
      }
    }

    loadChecklist()
  }, [capturedProperty, scenarioLookup])

  const filteredChecklistItems = useMemo(
    () =>
      activeScenario === 'all'
        ? checklistItems
        : checklistItems.filter(
            (item) => item.developmentScenario === activeScenario,
          ),
    [checklistItems, activeScenario],
  )

  const displaySummary = useMemo(() => {
    if (!capturedProperty) {
      return null
    }
    if (activeScenario === 'all' && checklistSummary) {
      return checklistSummary
    }
    return computeChecklistSummary(filteredChecklistItems, capturedProperty.propertyId)
  }, [activeScenario, capturedProperty, checklistSummary, filteredChecklistItems])

  const activeScenarioDetails = useMemo(
    () => (activeScenario === 'all' ? null : scenarioLookup.get(activeScenario)),
    [activeScenario, scenarioLookup],
  )

  useEffect(() => {
    setSelectedCategory(null)
  }, [activeScenario])

  function toggleScenario(scenario: DevelopmentScenario) {
    setSelectedScenarios((prev) =>
      prev.includes(scenario)
        ? prev.filter((s) => s !== scenario)
        : [...prev, scenario]
    )
  }

  async function handleCapture(e: React.FormEvent) {
    e.preventDefault()
    const lat = parseFloat(latitude)
    const lon = parseFloat(longitude)

    if (isNaN(lat) || isNaN(lon)) {
      setError('Please enter valid coordinates')
      return
    }

    if (selectedScenarios.length === 0) {
      setError('Please select at least one development scenario')
      return
    }

    setIsCapturing(true)
    setError(null)

    try {
      const result = await capturePropertyForDevelopment({
        latitude: lat,
        longitude: lon,
        developmentScenarios: selectedScenarios,
      })

      setCapturedProperty(result)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to capture property')
    } finally {
      setIsCapturing(false)
    }
  }

  async function handleChecklistUpdate(
    itemId: string,
    newStatus: 'pending' | 'in_progress' | 'completed' | 'not_applicable',
  ) {
    const updated = await updateChecklistItem(itemId, { status: newStatus })
    if (updated) {
      // Update local state
      setChecklistItems((prev) =>
        prev.map((item) => (item.id === itemId ? updated : item)),
      )

      // Reload summary
      if (capturedProperty) {
        const summary = await fetchChecklistSummary(capturedProperty.propertyId)
        setChecklistSummary(summary)
      }
    }
  }

  return (
    <div
      style={{
        padding: '3rem 2rem',
        maxWidth: '1200px',
        margin: '0 auto',
        fontFamily: '-apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", system-ui, sans-serif',
        color: '#1d1d1f',
      }}
    >
      {/* Header */}
      <header style={{ marginBottom: '3rem' }}>
        <h1
          style={{
            fontSize: '3rem',
            fontWeight: 700,
            letterSpacing: '-0.015em',
            margin: '0 0 0.5rem',
            lineHeight: 1.1,
          }}
        >
          Site Acquisition
        </h1>
        <p
          style={{
            fontSize: '1.25rem',
            color: '#6e6e73',
            margin: 0,
            lineHeight: 1.5,
            letterSpacing: '-0.005em',
          }}
        >
          Comprehensive property capture and development feasibility analysis for developers
        </p>
      </header>

      {/* Property Capture Form */}
      <section
        style={{
          background: 'white',
          border: '1px solid #d2d2d7',
          borderRadius: '18px',
          padding: '2rem',
          marginBottom: '2rem',
        }}
      >
        <h2
          style={{
            fontSize: '1.5rem',
            fontWeight: 600,
            marginBottom: '1.5rem',
            letterSpacing: '-0.01em',
          }}
        >
          Property Coordinates
        </h2>

        <form onSubmit={handleCapture}>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(2, 1fr)',
              gap: '1rem',
              marginBottom: '2rem',
            }}
          >
            <div>
              <label
                htmlFor="latitude"
                style={{
                  display: 'block',
                  fontSize: '0.9375rem',
                  fontWeight: 500,
                  marginBottom: '0.5rem',
                  color: '#1d1d1f',
                }}
              >
                Latitude
              </label>
              <input
                id="latitude"
                type="text"
                value={latitude}
                onChange={(e) => setLatitude(e.target.value)}
                style={{
                  width: '100%',
                  padding: '0.875rem 1rem',
                  fontSize: '1rem',
                  border: '1px solid #d2d2d7',
                  borderRadius: '12px',
                  outline: 'none',
                  fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Monaco, monospace',
                  transition: 'all 0.2s ease',
                }}
                onFocus={(e) => {
                  e.currentTarget.style.borderColor = '#1d1d1f'
                  e.currentTarget.style.boxShadow = '0 0 0 4px rgba(0, 0, 0, 0.04)'
                }}
                onBlur={(e) => {
                  e.currentTarget.style.borderColor = '#d2d2d7'
                  e.currentTarget.style.boxShadow = 'none'
                }}
              />
            </div>

            <div>
              <label
                htmlFor="longitude"
                style={{
                  display: 'block',
                  fontSize: '0.9375rem',
                  fontWeight: 500,
                  marginBottom: '0.5rem',
                  color: '#1d1d1f',
                }}
              >
                Longitude
              </label>
              <input
                id="longitude"
                type="text"
                value={longitude}
                onChange={(e) => setLongitude(e.target.value)}
                style={{
                  width: '100%',
                  padding: '0.875rem 1rem',
                  fontSize: '1rem',
                  border: '1px solid #d2d2d7',
                  borderRadius: '12px',
                  outline: 'none',
                  fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Monaco, monospace',
                  transition: 'all 0.2s ease',
                }}
                onFocus={(e) => {
                  e.currentTarget.style.borderColor = '#1d1d1f'
                  e.currentTarget.style.boxShadow = '0 0 0 4px rgba(0, 0, 0, 0.04)'
                }}
                onBlur={(e) => {
                  e.currentTarget.style.borderColor = '#d2d2d7'
                  e.currentTarget.style.boxShadow = 'none'
                }}
              />
            </div>
          </div>

          <h3
            style={{
              fontSize: '1.125rem',
              fontWeight: 600,
              marginBottom: '1rem',
              letterSpacing: '-0.01em',
            }}
          >
            Development Scenarios
          </h3>

          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
              gap: '1rem',
              marginBottom: '2rem',
            }}
          >
            {SCENARIO_OPTIONS.map((scenario) => {
              const isSelected = selectedScenarios.includes(scenario.value)
              return (
                <button
                  key={scenario.value}
                  type="button"
                  onClick={() => toggleScenario(scenario.value)}
                  style={{
                    background: isSelected ? '#f5f5f7' : 'white',
                    border: `1px solid ${isSelected ? '#1d1d1f' : '#d2d2d7'}`,
                    borderRadius: '12px',
                    padding: '1.25rem',
                    cursor: 'pointer',
                    textAlign: 'left',
                    transition: 'all 0.2s ease',
                    position: 'relative',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.transform = 'translateY(-2px)'
                    e.currentTarget.style.boxShadow = '0 8px 16px rgba(0, 0, 0, 0.08)'
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.transform = 'translateY(0)'
                    e.currentTarget.style.boxShadow = 'none'
                  }}
                >
                  {isSelected && (
                    <div
                      style={{
                        position: 'absolute',
                        top: '1rem',
                        right: '1rem',
                        width: '20px',
                        height: '20px',
                        borderRadius: '50%',
                        background: '#1d1d1f',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: '12px',
                        color: 'white',
                      }}
                    >
                      ✓
                    </div>
                  )}
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.75rem',
                      marginBottom: '0.5rem',
                    }}
                  >
                    <span style={{ fontSize: '1.5rem' }}>{scenario.icon}</span>
                    <div
                      style={{
                        fontSize: '1.0625rem',
                        fontWeight: 600,
                        color: '#1d1d1f',
                        letterSpacing: '-0.005em',
                      }}
                    >
                      {scenario.label}
                    </div>
                  </div>
                  <div
                    style={{
                      fontSize: '0.875rem',
                      color: '#6e6e73',
                      lineHeight: 1.4,
                      letterSpacing: '-0.005em',
                    }}
                  >
                    {scenario.description}
                  </div>
                </button>
              )
            })}
          </div>

          <button
            type="submit"
            disabled={isCapturing || selectedScenarios.length === 0}
            style={{
              width: '100%',
              padding: '0.875rem 2rem',
              fontSize: '1.0625rem',
              fontWeight: 500,
              color: 'white',
              background:
                isCapturing || selectedScenarios.length === 0 ? '#d2d2d7' : '#1d1d1f',
              border: 'none',
              borderRadius: '12px',
              cursor:
                isCapturing || selectedScenarios.length === 0 ? 'not-allowed' : 'pointer',
              transition: 'all 0.2s ease',
              letterSpacing: '-0.005em',
            }}
            onMouseEnter={(e) => {
              if (!isCapturing && selectedScenarios.length > 0) {
                e.currentTarget.style.background = '#424245'
              }
            }}
            onMouseLeave={(e) => {
              if (!isCapturing && selectedScenarios.length > 0) {
                e.currentTarget.style.background = '#1d1d1f'
              }
            }}
          >
            {isCapturing ? 'Capturing Property...' : 'Capture Property'}
          </button>

          {error && (
            <div
              style={{
                marginTop: '1rem',
                padding: '1rem',
                background: '#fff5f5',
                border: '1px solid #fed7d7',
                borderRadius: '12px',
                color: '#c53030',
                fontSize: '0.9375rem',
              }}
            >
              {error}
            </div>
          )}

          {capturedProperty && (
            <div
              style={{
                marginTop: '1rem',
                padding: '1rem',
                background: '#f0fdf4',
                border: '1px solid #bbf7d0',
                borderRadius: '12px',
                color: '#15803d',
                fontSize: '0.9375rem',
              }}
            >
              <strong>Property captured successfully</strong>
              <div style={{ marginTop: '0.5rem', fontSize: '0.875rem' }}>
                {capturedProperty.address.fullAddress} • {capturedProperty.address.district}
              </div>
            </div>
          )}
        </form>
      </section>

      {/* Due Diligence Checklist */}
      <section
        style={{
          background: 'white',
          border: '1px solid #d2d2d7',
          borderRadius: '18px',
          padding: '2rem',
          marginBottom: '2rem',
        }}
      >
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'flex-start',
            marginBottom: '1.5rem',
          }}
        >
          <div>
            <h2
              style={{
                fontSize: '1.5rem',
                fontWeight: 600,
                marginBottom: '0.5rem',
                letterSpacing: '-0.01em',
              }}
            >
              Due Diligence Checklist
            </h2>
            {displaySummary && (
              <p
                style={{
                  margin: 0,
                  fontSize: '0.9375rem',
                  color: '#6e6e73',
                }}
              >
                {activeScenario === 'all'
                  ? 'Overall progress'
                  : `${activeScenarioDetails?.label ?? 'Scenario'}`}
                : {displaySummary.completed} of {displaySummary.total} items completed (
                {displaySummary.completionPercentage.toFixed(0)}%)
              </p>
            )}
            {activeScenarioDetails?.description && (
              <p
                style={{
                  margin: '0.25rem 0 0',
                  fontSize: '0.875rem',
                  color: '#86868b',
                }}
              >
                {activeScenarioDetails.description}
              </p>
            )}
          </div>
        </div>

        {availableChecklistScenarios.length > 0 && (
          <div
            style={{
              display: 'flex',
              flexWrap: 'wrap',
              gap: '0.75rem',
              marginBottom: '1.5rem',
            }}
          >
            <button
              type="button"
              onClick={() => setActiveScenario('all')}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                padding: '0.5rem 0.85rem',
                borderRadius: '9999px',
                border: `1px solid ${
                  activeScenario === 'all' ? '#1d1d1f' : '#d2d2d7'
                }`,
                background: activeScenario === 'all' ? '#1d1d1f' : '#f5f5f7',
                color: activeScenario === 'all' ? 'white' : '#1d1d1f',
                cursor: 'pointer',
                fontSize: '0.875rem',
                fontWeight: 500,
                transition: 'all 0.2s ease',
              }}
            >
              All scenarios
            </button>
            {availableChecklistScenarios.map((scenario) => {
              const option = scenarioLookup.get(scenario)
              const isActive = activeScenario === scenario
              return (
                <button
                  key={scenario}
                  type="button"
                  onClick={() => setActiveScenario(scenario)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem',
                    padding: '0.5rem 0.85rem',
                    borderRadius: '9999px',
                    border: `1px solid ${isActive ? '#1d1d1f' : '#d2d2d7'}`,
                    background: isActive ? '#1d1d1f' : '#f5f5f7',
                    color: isActive ? 'white' : '#1d1d1f',
                    cursor: 'pointer',
                    fontSize: '0.875rem',
                    fontWeight: 500,
                    transition: 'all 0.2s ease',
                  }}
                >
                  {option?.icon ? (
                    <span style={{ fontSize: '1rem' }}>{option.icon}</span>
                  ) : null}
                  <span>{option?.label ?? formatCategoryName(scenario)}</span>
                </button>
              )
            })}
          </div>
        )}

        {isLoadingChecklist ? (
          <div
            style={{
              padding: '3rem 2rem',
              textAlign: 'center',
              color: '#6e6e73',
            }}
          >
            <p>Loading checklist...</p>
          </div>
        ) : !capturedProperty ? (
          <div
            style={{
              padding: '3rem 2rem',
              textAlign: 'center',
              color: '#6e6e73',
              background: '#f5f5f7',
              borderRadius: '12px',
            }}
          >
            <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>📋</div>
            <p style={{ margin: 0, fontSize: '1.0625rem' }}>
              Capture a property to view the comprehensive due diligence checklist
            </p>
            <p style={{ margin: '0.5rem 0 0', fontSize: '0.9375rem' }}>
              Automatically generated based on selected development scenarios
            </p>
          </div>
        ) : checklistItems.length === 0 ? (
          <div
            style={{
              padding: '2rem',
              textAlign: 'center',
              color: '#6e6e73',
              background: '#f5f5f7',
              borderRadius: '12px',
            }}
          >
            <p>No checklist items found for this property.</p>
          </div>
        ) : filteredChecklistItems.length === 0 ? (
          <div
            style={{
              padding: '2rem',
              textAlign: 'center',
              color: '#6e6e73',
              background: '#f5f5f7',
              borderRadius: '12px',
            }}
          >
            <p>
              No checklist items for{' '}
              {activeScenarioDetails?.label ?? 'this scenario'} yet.
            </p>
          </div>
        ) : (
          <>
            {/* Progress bar */}
            {displaySummary && (
              <div
                style={{
                  marginBottom: '1.5rem',
                  background: '#f5f5f7',
                  borderRadius: '12px',
                  height: '8px',
                  overflow: 'hidden',
                }}
              >
                <div
                  style={{
                    width: `${displaySummary.completionPercentage}%`,
                    height: '100%',
                    background: 'linear-gradient(90deg, #0071e3 0%, #005bb5 100%)',
                    transition: 'width 0.3s ease',
                  }}
                />
              </div>
            )}

            {/* Group by category */}
            {Object.entries(
              filteredChecklistItems.reduce((acc, item) => {
                const category = item.category
                if (!acc[category]) {
                  acc[category] = []
                }
                acc[category].push(item)
                return acc
              }, {} as Record<string, ChecklistItem[]>),
            ).map(([category, items]) => (
              <div
                key={category}
                style={{
                  marginBottom: '1.5rem',
                  border: '1px solid #e5e5e7',
                  borderRadius: '12px',
                  overflow: 'hidden',
                }}
              >
                <button
                  type="button"
                  onClick={() =>
                    setSelectedCategory(selectedCategory === category ? null : category)
                  }
                  style={{
                    width: '100%',
                    padding: '1rem 1.25rem',
                    background: '#f5f5f7',
                    border: 'none',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    cursor: 'pointer',
                    fontSize: '1rem',
                    fontWeight: 600,
                    textAlign: 'left',
                  }}
                >
                  <span>{formatCategoryName(category)}</span>
                  <span
                    style={{
                      fontSize: '0.875rem',
                      color: '#6e6e73',
                    }}
                  >
                    {items.filter((item) => item.status === 'completed').length}/{items.length}
                  </span>
                </button>
                {(selectedCategory === category || selectedCategory === null) && (
                  <div style={{ padding: '0' }}>
                    {items.map((item) => (
                      <div
                        key={item.id}
                        style={{
                          padding: '1rem 1.25rem',
                          borderTop: '1px solid #e5e5e7',
                          display: 'flex',
                          gap: '1rem',
                          alignItems: 'flex-start',
                        }}
                      >
                        <select
                          value={item.status}
                          onChange={(e) =>
                            handleChecklistUpdate(
                              item.id,
                              e.target.value as
                                | 'pending'
                                | 'in_progress'
                                | 'completed'
                                | 'not_applicable',
                            )
                          }
                          style={{
                            padding: '0.5rem',
                            border: '1px solid #d2d2d7',
                            borderRadius: '8px',
                            fontSize: '0.875rem',
                            background: 'white',
                            cursor: 'pointer',
                          }}
                        >
                          <option value="pending">Pending</option>
                          <option value="in_progress">In Progress</option>
                          <option value="completed">Completed</option>
                          <option value="not_applicable">Not Applicable</option>
                        </select>
                        <div style={{ flex: 1 }}>
                          <div
                            style={{
                              display: 'flex',
                              gap: '0.75rem',
                              alignItems: 'center',
                              marginBottom: '0.25rem',
                            }}
                          >
                            <h4
                              style={{
                                margin: 0,
                                fontSize: '0.9375rem',
                                fontWeight: 600,
                              }}
                            >
                              {item.itemTitle}
                            </h4>
                            {item.priority === 'critical' && (
                              <span
                                style={{
                                  padding: '0.125rem 0.5rem',
                                  background: '#fee2e2',
                                  color: '#991b1b',
                                  fontSize: '0.75rem',
                                  fontWeight: 600,
                                  borderRadius: '6px',
                                }}
                              >
                                CRITICAL
                              </span>
                            )}
                            {item.priority === 'high' && (
                              <span
                                style={{
                                  padding: '0.125rem 0.5rem',
                                  background: '#fef3c7',
                                  color: '#92400e',
                                  fontSize: '0.75rem',
                                  fontWeight: 600,
                                  borderRadius: '6px',
                                }}
                              >
                                HIGH
                              </span>
                            )}
                          </div>
                          {item.itemDescription && (
                            <p
                              style={{
                                margin: '0.5rem 0 0',
                                fontSize: '0.875rem',
                                color: '#6e6e73',
                                lineHeight: 1.5,
                              }}
                            >
                              {item.itemDescription}
                            </p>
                          )}
                          {item.requiresProfessional && item.professionalType && (
                            <p
                              style={{
                                margin: '0.5rem 0 0',
                                fontSize: '0.8125rem',
                                color: '#0071e3',
                              }}
                            >
                              Requires: {item.professionalType}
                            </p>
                          )}
                          {item.dueDate && (
                            <p
                              style={{
                                margin: '0.25rem 0 0',
                                fontSize: '0.8125rem',
                                color: '#6e6e73',
                              }}
                            >
                              Due: {new Date(item.dueDate).toLocaleDateString()}
                            </p>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </>
        )}
      </section>

      <section
        style={{
          background: 'white',
          border: '1px solid #d2d2d7',
          borderRadius: '18px',
          padding: '2rem',
          marginBottom: '2rem',
        }}
      >
        <h2
          style={{
            fontSize: '1.5rem',
            fontWeight: 600,
            marginBottom: '1rem',
            letterSpacing: '-0.01em',
          }}
        >
          Multi-Scenario Comparison
        </h2>
        <div
          style={{
            padding: '3rem 2rem',
            textAlign: 'center',
            color: '#6e6e73',
            background: '#f5f5f7',
            borderRadius: '12px',
          }}
        >
          <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>📊</div>
          <p style={{ margin: 0, fontSize: '1.0625rem' }}>
            Side-by-side scenario comparison will appear here
          </p>
          <p style={{ margin: '0.5rem 0 0', fontSize: '0.9375rem' }}>
            Cost analysis, timeline, ROI/IRR, and risk assessment matrix
          </p>
        </div>
      </section>

      <section
        style={{
          background: 'white',
          border: '1px solid #d2d2d7',
          borderRadius: '18px',
          padding: '2rem',
        }}
      >
        <h2
          style={{
            fontSize: '1.5rem',
            fontWeight: 600,
            marginBottom: '1rem',
            letterSpacing: '-0.01em',
          }}
        >
          Property Condition Assessment
        </h2>
        <div
          style={{
            padding: '3rem 2rem',
            textAlign: 'center',
            color: '#6e6e73',
            background: '#f5f5f7',
            borderRadius: '12px',
          }}
        >
          <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>🏢</div>
          <p style={{ margin: 0, fontSize: '1.0625rem' }}>
            Developer condition assessment toolkit coming soon
          </p>
          <p style={{ margin: '0.5rem 0 0', fontSize: '0.9375rem' }}>
            Scenario-specific building scores, intrusive survey guidance, and capex planning support will live here.
          </p>
        </div>
      </section>
    </div>
  )
}
