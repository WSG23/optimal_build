import { useEffect, useMemo, useRef, useState } from 'react'

import type { OverlaySuggestion, PipelineSuggestion, ProjectRoiMetrics } from '../api/client'
import { AppLayout } from '../App'
import { useApiClient } from '../api/client'
import { useTranslation } from '../i18n'
import useRules from '../hooks/useRules'
import RulePackExplanationPanel from '../modules/cad/RulePackExplanationPanel'
import RoiSummary from '../modules/cad/RoiSummary'
import type { RoiMetrics } from '../modules/cad/types'

const DEFAULT_PROJECT_ID = 5821
const OVERLAY_RUN_POLL_INTERVAL_MS = 2500
const OVERLAY_RUN_POLL_TIMEOUT_MS = 60000

export function CadPipelinesPage() {
  const apiClient = useApiClient()
  const { t } = useTranslation()
  const [projectId, setProjectId] = useState<number>(DEFAULT_PROJECT_ID)
  const [overlaySuggestions, setOverlaySuggestions] = useState<OverlaySuggestion[]>([])
  const [suggestions, setSuggestions] = useState<PipelineSuggestion[]>([])
  const [roi, setRoi] = useState<ProjectRoiMetrics | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const { rules, loading: rulesLoading } = useRules(apiClient)
  const processedProjectRef = useRef<{ id: number | null; processed: boolean }>({ id: null, processed: false })

  useEffect(() => {
    if (processedProjectRef.current.id !== projectId) {
      processedProjectRef.current = { id: projectId, processed: false }
    }
    if (processedProjectRef.current.processed) {
      return
    }
    processedProjectRef.current.processed = true

    let cancelled = false
    const waitForOverlayRun = async (
      status: string,
      jobId: string | null,
      lastEventIdBeforeRun: number,
      startedAt: number,
    ): Promise<void> => {
      const normalisedStatus = status.toLowerCase()
      if (normalisedStatus === 'completed') {
        return
      }
      if (normalisedStatus === 'failed') {
        throw new Error(t('common.errors.pipelineLoad'))
      }
      if (!jobId) {
        throw new Error(t('common.errors.pipelineLoad'))
      }

      const deadline = startedAt + OVERLAY_RUN_POLL_TIMEOUT_MS
      while (!cancelled && Date.now() < deadline) {
        await new Promise((resolve) => setTimeout(resolve, OVERLAY_RUN_POLL_INTERVAL_MS))
        if (cancelled) {
          return
        }

        const events = await apiClient.listAuditTrail(projectId, { eventType: 'overlay_run' })
        const completed = events.some((event) => event.id > lastEventIdBeforeRun)
        if (completed) {
          return
        }
      }

      if (!cancelled) {
        throw new Error(t('common.errors.pipelineLoad'))
      }
    }

    const load = async () => {
      setLoading(true)
      setError(null)
      try {
        const eventsBeforeRun = await apiClient.listAuditTrail(projectId, { eventType: 'overlay_run' })
        if (cancelled) {
          return
        }
        const lastEventIdBeforeRun = eventsBeforeRun.reduce<number>((max, event) => {
          return event.id > max ? event.id : max
        }, 0)
        const runRequestedAt = Date.now()
        const runResult = await apiClient.runOverlay(projectId)
        await waitForOverlayRun(runResult.status, runResult.jobId, lastEventIdBeforeRun, runRequestedAt)
        if (cancelled) {
          return
        }

        const overlays = await apiClient.listOverlaySuggestions(projectId)
        if (!cancelled) {
          setOverlaySuggestions(overlays)
          const pipeline = await apiClient.getDefaultPipelineSuggestions({
            overlays: overlays.map((item) => item.code),
            hints: overlays.map((item) => item.rationale).filter((value): value is string => Boolean(value)),
          })
          if (!cancelled) {
            setSuggestions(pipeline)
          }
        }
        if (cancelled) {
          return
        }
        const roiMetrics = await apiClient.getProjectRoi(projectId)
        if (!cancelled) {
          setRoi(roiMetrics)
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : t('common.errors.pipelineLoad'))
          setSuggestions([])
        }
      } finally {
        if (!cancelled) {
          setLoading(false)
        }
      }
    }

    load().catch((err: unknown) => {
      console.error('Failed to load pipeline suggestions', err)
    })

    return () => {
      cancelled = true
    }
  }, [apiClient, projectId, t])

  const overlayCodes = useMemo(() => overlaySuggestions.map((item) => item.code), [overlaySuggestions])

  const roiMetrics = useMemo<RoiMetrics>(() => {
    if (!roi) {
      return {
        automationScore: 0,
        savingsPercent: 0,
        reviewHoursSaved: 0,
        paybackWeeks: 0,
      }
    }
    return {
      automationScore: roi.automationScore,
      savingsPercent: roi.savingsPercent,
      reviewHoursSaved: Number(roi.reviewHoursSaved.toFixed(1)),
      paybackWeeks: roi.paybackWeeks,
    }
  }, [roi])

  return (
    <AppLayout title={t('pipelines.title')} subtitle={t('pipelines.subtitle')}>
      <div className="cad-pipelines__toolbar">
        <label>
          <span>{t('pipelines.projectLabel')}</span>
          <input
            type="number"
            min={1}
            value={projectId}
            onChange={(event) => setProjectId(Number(event.target.value) || DEFAULT_PROJECT_ID)}
          />
        </label>
        {overlayCodes.length > 0 && (
          <p className="cad-pipelines__context">
            {t('detection.overlays')}: {overlayCodes.join(', ')}
          </p>
        )}
      </div>

      {error && <p className="cad-pipelines__error">{error}</p>}

      <section className="cad-pipelines">
        <h2>{t('pipelines.suggestionHeading')}</h2>
        {loading && <p>{t('common.loading')}</p>}
        {!loading && suggestions.length === 0 && <p>{t('panels.rulePackEmpty')}</p>}
        {!loading && suggestions.length > 0 && (
          <ul>
            {suggestions.map((suggestion) => (
              <li key={suggestion.id} className="cad-pipelines__item">
                <h3>{suggestion.title}</h3>
                <p>{suggestion.description}</p>
                <dl>
                  <div>
                    <dt>{t('pipelines.pipelineFocus')}</dt>
                    <dd>{suggestion.focus}</dd>
                  </div>
                  <div>
                    <dt>{t('pipelines.automationScore')}</dt>
                    <dd>{Math.round(suggestion.automationScore * 100)}%</dd>
                  </div>
                  <div>
                    <dt>{t('pipelines.reviewHours')}</dt>
                    <dd>{suggestion.reviewHoursSaved}h</dd>
                  </div>
                  <div>
                    <dt>{t('pipelines.savings')}</dt>
                    <dd>{suggestion.estimatedSavingsPercent}%</dd>
                  </div>
                </dl>
              </li>
            ))}
          </ul>
        )}
      </section>

      <RoiSummary metrics={roiMetrics} />

      <RulePackExplanationPanel rules={rules} loading={rulesLoading} />
    </AppLayout>
  )
}

export default CadPipelinesPage
