import type { DetectionStatus } from './types'

export function computeNextLayers(
  activeLayers: DetectionStatus[],
  status: DetectionStatus,
) {
  const isActive = activeLayers.includes(status)
  return isActive
    ? activeLayers.filter((layer) => layer !== status)
    : [...activeLayers, status]
}
