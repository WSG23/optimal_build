import { useEffect, useMemo, useState } from 'react'

import type { OverlayInsights, PipelineSuggestion } from '../api/client'
import { AppLayout } from '../App'
import { useApiClient } from '../api/client'
import { useTranslation } from '../i18n'
import useRules from '../hooks/useRules'
import RulePackExplanationPanel from '../modules/cad/RulePackExplanationPanel'
import RoiSummary from '../modules/cad/RoiSummary'
import type { RoiMetrics } from '../modules/cad/types'

const DEFAULT_ZONE = 'RA'

export function CadPipelinesPage() {
  const apiClient = useApiClient()
  const { t } = useTranslation()
  const [zoneCode, setZoneCode] = useState(DEFAULT_ZONE)
  const [insights, setInsights] = useState<OverlayInsights | null>(null)
  const [suggestions, setSuggestions] = useState<PipelineSuggestion[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const { rules, loading: rulesLoading } = useRules(apiClient)

  useEffect(() => {
    let cancelled = false
    const load = async () => {
      setLoading(true)
      setError(null)
      try {
        const overlay = await apiClient.getOverlayInsights({ zoneCode })
        if (!cancelled) {
          setInsights(overlay)
        }
        const pipeline = await apiClient.getDefaultPipelineSuggestions({
          overlays: overlay.overlays,
          hints: overlay.advisoryHints,
        })
        if (!cancelled) {
          setSuggestions(pipeline)
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
  }, [apiClient, t, zoneCode])

  const roiMetrics = useMemo<RoiMetrics>(() => {
    if (suggestions.length === 0) {
      return {
        automationScore: 0.5,
        savingsPercent: 18,
        reviewHoursSaved: 6,
        paybackWeeks: 8,
      }
    }
    const best = suggestions[0]
    const totalHours = suggestions.reduce((sum, suggestion) => sum + suggestion.reviewHoursSaved, 0)
    return {
      automationScore: best.automationScore,
      savingsPercent: Math.min(45, best.estimatedSavingsPercent + suggestions.length * 4),
      reviewHoursSaved: totalHours,
      paybackWeeks: Math.max(2, Math.round(12 - best.estimatedSavingsPercent / 5)),
    }
  }, [suggestions])

  return (
    <AppLayout title={t('pipelines.title')} subtitle={t('pipelines.subtitle')}>
      <div className="cad-pipelines__toolbar">
        <label>
          <span>{t('uploader.zone')}</span>
          <select value={zoneCode} onChange={(event) => setZoneCode(event.target.value)}>
            <option value="RA">RA</option>
            <option value="RCR">RCR</option>
            <option value="CBD">CBD</option>
          </select>
        </label>
        {insights && (
          <p className="cad-pipelines__context">
            {t('detection.overlays')}: {insights.overlays.join(', ') || t('common.fallback.dash')}
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
