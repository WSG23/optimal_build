import { useState } from 'react'

import CadDetectionPreview from './CadDetectionPreview'
import { TranslationProvider } from '../../i18n'
import type { DetectedUnit, DetectionStatus } from './types'

const meta = {
  title: 'CAD/Detection Preview',
  component: CadDetectionPreview,
}

export default meta

type SeverityKey = 'high' | 'medium' | 'low' | 'none'
type StoryProps = Parameters<typeof CadDetectionPreview>[0]

const ALL_SEVERITIES: SeverityKey[] = ['high', 'medium', 'low', 'none']
const ALL_STATUSES: DetectionStatus[] = ['source', 'pending', 'approved', 'rejected']

const arraysEqual = <T,>(a: T[], b: T[]) =>
  a.length === b.length && a.every((value) => b.includes(value))

const computePercentages = (summary: StoryProps['severitySummary']) => {
  const total = summary.high + summary.medium + summary.low + summary.none
  if (total === 0) {
    return { high: 0, medium: 0, low: 0, none: 0 }
  }
  const toPercent = (value: number) => Math.round(((value / total) * 100) * 10) / 10
  return {
    high: toPercent(summary.high),
    medium: toPercent(summary.medium),
    low: toPercent(summary.low),
    none: toPercent(summary.none),
  }
}

const PreviewStoryWrapper = (
  props: Omit<
    StoryProps,
    | 'activeSeverities'
    | 'onToggleSeverity'
    | 'onResetSeverity'
    | 'isSeverityFiltered'
    | 'hiddenSeverityCounts'
  >,
) => {
  const [activeSeverities, setActiveSeverities] = useState<SeverityKey[]>([
    ...ALL_SEVERITIES,
  ])
  const [preset, setPreset] = useState<SeverityKey[] | null>(null)
  const {
    severitySummary,
    severityPercentages: providedPercentages,
    statusCounts = { source: 0, pending: 0, approved: 0, rejected: 0 },
    hiddenStatusCounts = { source: 0, pending: 0, approved: 0, rejected: 0 },
    activeStatuses = ALL_STATUSES,
    ...rest
  } = props
  const severityPercentages = providedPercentages ?? computePercentages(severitySummary)

  const hiddenSeverityCounts = ALL_SEVERITIES.reduce(
    (acc, severity) => {
      acc[severity] = activeSeverities.includes(severity)
        ? 0
        : severitySummary[severity]
      return acc
    },
    { high: 0, medium: 0, low: 0, none: 0 } as StoryProps['hiddenSeverityCounts'],
  )

  const toggleSeverity = (severity: SeverityKey) => {
    setActiveSeverities((current) => {
      if (current.includes(severity)) {
        if (current.length === 1) {
          return current
        }
        return current.filter((value) => value !== severity)
      }
      return [...current, severity]
    })
  }

  const resetSeverity = () => {
    setActiveSeverities([...ALL_SEVERITIES])
  }

  const isFiltered = activeSeverities.length !== ALL_SEVERITIES.length
  const hasPreset = preset !== null
  const canApplyPreset =
    preset !== null && !arraysEqual(preset, activeSeverities)

  const savePreset = () => {
    setPreset([...activeSeverities])
  }

  const applyPreset = () => {
    if (preset) {
      setActiveSeverities([...preset])
    }
  }

  return (
    <TranslationProvider>
      <CadDetectionPreview
        severitySummary={severitySummary}
        severityPercentages={severityPercentages}
        hiddenSeverityCounts={hiddenSeverityCounts}
        statusCounts={statusCounts}
        hiddenStatusCounts={hiddenStatusCounts}
        activeStatuses={activeStatuses}
        {...rest}
        activeSeverities={activeSeverities}
        onToggleSeverity={toggleSeverity}
        onResetSeverity={resetSeverity}
        onSaveSeverityPreset={savePreset}
        onApplySeverityPreset={applyPreset}
        hasSeverityPreset={hasPreset}
        canApplySeverityPreset={canApplyPreset}
        isSeverityFiltered={isFiltered}
      />
    </TranslationProvider>
  )
}

const units: DetectedUnit[] = [
  {
    id: 'L01-01',
    floor: 1,
    unitLabel: '#01-01',
    areaSqm: 82,
    status: 'source',
  },
  {
    id: 'L01-02',
    floor: 1,
    unitLabel: '#01-02',
    areaSqm: 79,
    status: 'pending',
  },
  {
    id: 'L02-01',
    floor: 2,
    unitLabel: '#02-01',
    areaSqm: 85,
    status: 'approved',
  },
  {
    id: 'L03-01',
    floor: 3,
    unitLabel: '#03-01',
    areaSqm: 90,
    status: 'rejected',
  },
]

export const Default = () => (
  <PreviewStoryWrapper
    units={units}
    overlays={[
      {
        key: 'fire_access',
        title: 'Fire access clearance',
        count: 2,
        statusLabel: 'Pending',
        severity: 'high',
        severityLabel: 'High severity',
      },
      {
        key: 'community_facility',
        title: 'Provide community facility data',
        count: 1,
        statusLabel: 'Pending',
        severity: 'medium',
        severityLabel: 'Medium severity',
      },
      {
        key: 'fyi',
        title: 'For your information',
        count: 1,
        statusLabel: 'Source',
        severity: 'none',
        severityLabel: 'Informational',
      },
    ]}
    severitySummary={{ high: 1, medium: 1, low: 0, none: 1 }}
    statusCounts={{ source: 0, pending: 3, approved: 1, rejected: 1 }}
    hiddenStatusCounts={{ source: 0, pending: 0, approved: 0, rejected: 0 }}
    activeStatuses={ALL_STATUSES}
    hints={[{ key: 'staging', text: 'Coordinate with SCDF on staging' }]}
    zoneCode="RA"
  />
)

export const Locked = () => (
  <PreviewStoryWrapper
    units={units.filter((unit) => unit.status !== 'rejected')}
    overlays={[]}
    hints={[{ key: 'awaiting', text: 'Awaiting overlays' }]}
    severitySummary={{ high: 0, medium: 0, low: 0, none: 0 }}
    statusCounts={{ source: 0, pending: 1, approved: 0, rejected: 0 }}
    hiddenStatusCounts={{ source: 0, pending: 0, approved: 0, rejected: 0 }}
    activeStatuses={ALL_STATUSES}
    zoneCode="CBD"
    locked
  />
)
