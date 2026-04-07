import type { DeveloperPreviewJob } from '../../../../api/siteAcquisition'
import type { DevelopmentScenario } from '../../../../api/agents'

export function selectPreviewJobForScenario(
  previewJobs: DeveloperPreviewJob[] | null | undefined,
  preferredScenario?: DevelopmentScenario | null,
): DeveloperPreviewJob | null {
  if (!previewJobs?.length) {
    return null
  }

  if (preferredScenario) {
    return previewJobs.find((job) => job.scenario === preferredScenario) ?? null
  }

  return previewJobs[0] ?? null
}
