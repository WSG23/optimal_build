import { useEffect, useMemo, useState } from 'react'

import type { OverlaySuggestion, PipelineSuggestion, ProjectRoiMetrics } from '../api/client'
import { AppLayout } from '../App'
import { useApiClient } from '../api/client'
import { useTranslation } from '../i18n'
import useRules from '../hooks/useRules'
import RulePackExplanationPanel from '../modules/cad/RulePackExplanationPanel'
import RoiSummary from '../modules/cad/RoiSummary'
import type { RoiMetrics } from '../modules/cad/types'

const DEFAULT_PROJECT_ID = 5821

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

  useEffect(() => {
    let cancelled = false
    const load = async () => {
      setLoading(true)
      setError(null)
      try {
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
