/**
 * Hook for managing checklist state
 *
 * Handles:
 * - Loading checklist items from backend or offline templates
 * - Checklist filtering by scenario and category
 * - Checklist summary computation
 * - Checklist item status updates
 */

import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  fetchChecklistSummary,
  fetchPropertyChecklist,
  updateChecklistItem,
  OFFLINE_PROPERTY_ID,
  type ChecklistItem,
  type ChecklistSummary,
  type DevelopmentScenario,
  type SiteAcquisitionResult,
} from '../../../../api/siteAcquisition'
import { SCENARIO_OPTIONS } from '../constants'
import { buildOfflineChecklistItems, computeChecklistSummary } from '../utils'

// ============================================================================
// Types
// ============================================================================

export interface UseChecklistOptions {
  /** The captured property result (may be null before capture) */
  capturedProperty: SiteAcquisitionResult | null
}

export interface UseChecklistResult {
  // Checklist state
  checklistItems: ChecklistItem[]
  setChecklistItems: React.Dispatch<React.SetStateAction<ChecklistItem[]>>
  checklistSummary: ChecklistSummary | null
  isLoadingChecklist: boolean

  // Filter state
  selectedCategory: string | null
  setSelectedCategory: React.Dispatch<React.SetStateAction<string | null>>
  activeScenario: DevelopmentScenario | 'all'
  setActiveScenario: React.Dispatch<
    React.SetStateAction<DevelopmentScenario | 'all'>
  >
  availableChecklistScenarios: DevelopmentScenario[]

  // Derived values
  filteredChecklistItems: ChecklistItem[]
  displaySummary: ChecklistSummary | null
  activeScenarioDetails: (typeof SCENARIO_OPTIONS)[number] | null
  scenarioFilterOptions: DevelopmentScenario[]
  scenarioFocusOptions: Array<'all' | DevelopmentScenario>
  scenarioChecklistProgress: Record<
    string,
    { total: number; completed: number }
  >
  scenarioLookup: Map<DevelopmentScenario, (typeof SCENARIO_OPTIONS)[number]>

  // Actions
  handleChecklistUpdate: (
    itemId: string,
    newStatus: 'pending' | 'in_progress' | 'completed' | 'not_applicable',
  ) => Promise<void>
}

// ============================================================================
// Hook Implementation
// ============================================================================

export function useChecklist({
  capturedProperty,
}: UseChecklistOptions): UseChecklistResult {
  // Checklist state
  const [checklistItems, setChecklistItems] = useState<ChecklistItem[]>([])
  const [checklistSummary, setChecklistSummary] =
    useState<ChecklistSummary | null>(null)
  const [isLoadingChecklist, setIsLoadingChecklist] = useState(false)

  // Filter state
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null)
  const [activeScenario, setActiveScenario] = useState<
    DevelopmentScenario | 'all'
  >('all')
  const [availableChecklistScenarios, setAvailableChecklistScenarios] =
    useState<DevelopmentScenario[]>([])

  // Scenario lookup
  const scenarioLookup = useMemo(
    () => new Map(SCENARIO_OPTIONS.map((option) => [option.value, option])),
    [],
  )

  // ============================================================================
  // Load Checklist Effect
  // ============================================================================

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
        if (capturedProperty.propertyId === OFFLINE_PROPERTY_ID) {
          const offlineItems = buildOfflineChecklistItems(
            capturedProperty.propertyId,
            capturedProperty.quickAnalysis.scenarios.map(
              (scenario) => scenario.scenario,
            ),
          )
          const sortedOffline = [...offlineItems].sort((a, b) => {
            const orderA = a.displayOrder ?? Number.MAX_SAFE_INTEGER
            const orderB = b.displayOrder ?? Number.MAX_SAFE_INTEGER
            if (orderA !== orderB) {
              return orderA - orderB
            }
            return a.itemTitle.localeCompare(b.itemTitle)
          })
          setChecklistItems(sortedOffline)
          const offlineScenarios = Array.from(
            new Set(sortedOffline.map((item) => item.developmentScenario)),
          )
          setAvailableChecklistScenarios(offlineScenarios)
          setActiveScenario(
            offlineScenarios.length === 1 ? offlineScenarios[0] : 'all',
          )
          setChecklistSummary(
            computeChecklistSummary(sortedOffline, capturedProperty.propertyId),
          )
          setSelectedCategory(null)
          return
        }

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
        if (sortedItems.length === 0) {
          const fallbackItems = buildOfflineChecklistItems(
            capturedProperty.propertyId,
            capturedProperty.quickAnalysis.scenarios.map(
              (scenario) => scenario.scenario,
            ),
          )
          if (fallbackItems.length > 0) {
            const sortedFallback = [...fallbackItems].sort((a, b) => {
              const orderA = a.displayOrder ?? Number.MAX_SAFE_INTEGER
              const orderB = b.displayOrder ?? Number.MAX_SAFE_INTEGER
              if (orderA !== orderB) {
                return orderA - orderB
              }
              return a.itemTitle.localeCompare(b.itemTitle)
            })
            setChecklistItems(sortedFallback)
            setChecklistSummary(
              computeChecklistSummary(
                sortedFallback,
                capturedProperty.propertyId,
              ),
            )
            const fallbackScenarios = Array.from(
              new Set(sortedFallback.map((item) => item.developmentScenario)),
            )
            setAvailableChecklistScenarios(fallbackScenarios)
            setActiveScenario(
              fallbackScenarios.length === 1 ? fallbackScenarios[0] : 'all',
            )
            setSelectedCategory(null)
            return
          }
        }
        setChecklistSummary(summary)
        const scenarioSet = new Set<DevelopmentScenario>()
        sortedItems.forEach((item) => {
          if (scenarioLookup.has(item.developmentScenario)) {
            scenarioSet.add(item.developmentScenario)
          }
        })
        const scenarios = Array.from(scenarioSet)
        setAvailableChecklistScenarios(scenarios)
        setActiveScenario((prev: 'all' | DevelopmentScenario) => {
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

  // ============================================================================
  // Derived Values
  // ============================================================================

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
    return computeChecklistSummary(
      filteredChecklistItems,
      capturedProperty.propertyId,
    )
  }, [
    activeScenario,
    capturedProperty,
    checklistSummary,
    filteredChecklistItems,
  ])

  const activeScenarioDetails = useMemo(
    () =>
      activeScenario === 'all'
        ? null
        : (scenarioLookup.get(activeScenario) ?? null),
    [activeScenario, scenarioLookup],
  )

  const scenarioChecklistProgress = useMemo(() => {
    const progress: Record<string, { total: number; completed: number }> = {}
    checklistItems.forEach((item) => {
      const key = item.developmentScenario
      if (!progress[key]) {
        progress[key] = { total: 0, completed: 0 }
      }
      progress[key].total += 1
      if (item.status === 'completed') {
        progress[key].completed += 1
      }
    })
    return progress
  }, [checklistItems])

  // ============================================================================
  // Callbacks
  // ============================================================================

  const handleChecklistUpdate = useCallback(
    async (
      itemId: string,
      newStatus: 'pending' | 'in_progress' | 'completed' | 'not_applicable',
    ) => {
      const updated = await updateChecklistItem(itemId, { status: newStatus })
      if (updated) {
        // Update local state
        setChecklistItems((prev) =>
          prev.map((item) => (item.id === itemId ? updated : item)),
        )

        // Reload summary
        if (capturedProperty) {
          const summary = await fetchChecklistSummary(
            capturedProperty.propertyId,
          )
          setChecklistSummary(summary)
        }
      }
    },
    [capturedProperty],
  )

  // ============================================================================
  // Return
  // ============================================================================

  return {
    // Checklist state
    checklistItems,
    setChecklistItems,
    checklistSummary,
    isLoadingChecklist,

    // Filter state
    selectedCategory,
    setSelectedCategory,
    activeScenario,
    setActiveScenario,
    availableChecklistScenarios,

    // Derived values
    filteredChecklistItems,
    displaySummary,
    activeScenarioDetails,
    scenarioFilterOptions: availableChecklistScenarios, // Simplified for now
    scenarioFocusOptions: ['all', ...availableChecklistScenarios] as Array<
      'all' | DevelopmentScenario
    >,
    scenarioChecklistProgress,
    scenarioLookup,

    // Actions
    handleChecklistUpdate,
  }
}
