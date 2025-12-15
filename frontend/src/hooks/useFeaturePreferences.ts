import { useCallback, useEffect, useMemo, useState } from 'react'

export type UserRole = 'agent' | 'developer'

export interface FeaturePreferences {
  preview3D: boolean
  assetOptimization: boolean
  financialSummary: boolean
  heritageContext: boolean
  photoDocumentation: boolean
}

export type FeatureEntitlements = FeaturePreferences

interface StoredFeatureState {
  preferences: FeaturePreferences
  entitlements: FeatureEntitlements
}

const STORAGE_KEY = 'optimal_build_feature_preferences_v2'

const DEFAULT_PREFERENCES: FeaturePreferences = {
  preview3D: false,
  assetOptimization: false,
  financialSummary: false,
  heritageContext: false,
  photoDocumentation: false,
}

const DEFAULT_ENTITLEMENTS_BY_ROLE: Record<UserRole, FeatureEntitlements> = {
  agent: {
    preview3D: false,
    assetOptimization: false,
    financialSummary: false,
    heritageContext: false,
    photoDocumentation: false,
  },
  developer: {
    preview3D: true,
    assetOptimization: true,
    financialSummary: true,
    heritageContext: true,
    photoDocumentation: true,
  },
}

function loadState(role: UserRole): StoredFeatureState {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (!stored) {
      return {
        preferences: {
          ...DEFAULT_PREFERENCES,
          ...(role === 'developer'
            ? DEFAULT_ENTITLEMENTS_BY_ROLE.developer
            : {}),
        },
        entitlements: DEFAULT_ENTITLEMENTS_BY_ROLE[role],
      }
    }
    const parsed = JSON.parse(stored) as Partial<StoredFeatureState>
    const preferences =
      parsed.preferences ?? ({} as Partial<FeaturePreferences>)
    const entitlements =
      parsed.entitlements ?? ({} as Partial<FeatureEntitlements>)
    const defaultsForRole = DEFAULT_ENTITLEMENTS_BY_ROLE[role]
    return {
      preferences: {
        preview3D:
          typeof preferences.preview3D === 'boolean'
            ? preferences.preview3D
            : defaultsForRole.preview3D,
        assetOptimization:
          typeof preferences.assetOptimization === 'boolean'
            ? preferences.assetOptimization
            : defaultsForRole.assetOptimization,
        financialSummary:
          typeof preferences.financialSummary === 'boolean'
            ? preferences.financialSummary
            : defaultsForRole.financialSummary,
        heritageContext:
          typeof preferences.heritageContext === 'boolean'
            ? preferences.heritageContext
            : defaultsForRole.heritageContext,
        photoDocumentation:
          typeof preferences.photoDocumentation === 'boolean'
            ? preferences.photoDocumentation
            : defaultsForRole.photoDocumentation,
      },
      entitlements: {
        preview3D:
          typeof entitlements.preview3D === 'boolean'
            ? entitlements.preview3D
            : defaultsForRole.preview3D,
        assetOptimization:
          typeof entitlements.assetOptimization === 'boolean'
            ? entitlements.assetOptimization
            : defaultsForRole.assetOptimization,
        financialSummary:
          typeof entitlements.financialSummary === 'boolean'
            ? entitlements.financialSummary
            : defaultsForRole.financialSummary,
        heritageContext:
          typeof entitlements.heritageContext === 'boolean'
            ? entitlements.heritageContext
            : defaultsForRole.heritageContext,
        photoDocumentation:
          typeof entitlements.photoDocumentation === 'boolean'
            ? entitlements.photoDocumentation
            : defaultsForRole.photoDocumentation,
      },
    }
  } catch {
    return {
      preferences: DEFAULT_PREFERENCES,
      entitlements: DEFAULT_ENTITLEMENTS_BY_ROLE[role],
    }
  }
}

function saveState(state: StoredFeatureState): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state))
  } catch {
    console.warn(
      '[useFeaturePreferences] Failed to save preferences to localStorage',
    )
  }
}

export function hasAnyDeveloperFeatureEnabled(
  preferences: FeaturePreferences,
): boolean {
  return (
    preferences.preview3D ||
    preferences.assetOptimization ||
    preferences.financialSummary ||
    preferences.heritageContext ||
    preferences.photoDocumentation
  )
}

export function useFeaturePreferences(role: UserRole) {
  const defaults = useMemo(
    () => ({
      preferences: {
        ...DEFAULT_PREFERENCES,
        ...(role === 'developer' ? DEFAULT_ENTITLEMENTS_BY_ROLE.developer : {}),
      },
      entitlements: DEFAULT_ENTITLEMENTS_BY_ROLE[role],
    }),
    [role],
  )

  const [state, setState] = useState<StoredFeatureState>(() => loadState(role))

  useEffect(() => {
    const handleStorage = (event: StorageEvent) => {
      if (event.key === STORAGE_KEY) {
        setState(loadState(role))
      }
    }
    window.addEventListener('storage', handleStorage)
    return () => window.removeEventListener('storage', handleStorage)
  }, [role])

  const setPreferences = useCallback((updates: Partial<FeaturePreferences>) => {
    setState((prev) => {
      const next = { ...prev, preferences: { ...prev.preferences, ...updates } }
      saveState(next)
      return next
    })
  }, [])

  const toggleFeature = useCallback((feature: keyof FeaturePreferences) => {
    setState((prev) => {
      if (!prev.entitlements[feature]) {
        return prev
      }
      const nextPrefs = {
        ...prev.preferences,
        [feature]: !prev.preferences[feature],
      }
      const next = { ...prev, preferences: nextPrefs }
      saveState(next)
      return next
    })
  }, [])

  const unlockFeature = useCallback((feature: keyof FeaturePreferences) => {
    setState((prev) => {
      const nextEntitlements = { ...prev.entitlements, [feature]: true }
      const nextPrefs = { ...prev.preferences, [feature]: true }
      const next = { preferences: nextPrefs, entitlements: nextEntitlements }
      saveState(next)
      return next
    })
  }, [])

  const resetPreferences = useCallback(() => {
    setState(defaults)
    saveState(defaults)
  }, [defaults])

  const hasAnyEnabled = hasAnyDeveloperFeatureEnabled(state.preferences)

  return {
    preferences: state.preferences,
    entitlements: state.entitlements,
    setPreferences,
    toggleFeature,
    unlockFeature,
    resetPreferences,
    hasAnyEnabled,
  }
}
