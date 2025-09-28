import { useMemo } from 'react'

import { useTranslation } from '../../i18n'
import type { RuleSummary } from '../../api/client'

interface RulePackExplanationPanelProps {
  rules: RuleSummary[]
  loading?: boolean
}

export function RulePackExplanationPanel({
  rules,
  loading = false,
}: RulePackExplanationPanelProps) {
  const { t } = useTranslation()

  const grouped = useMemo(
    () =>
      rules.reduce<Record<string, RuleSummary[]>>((acc, rule) => {
        const key = rule.authority || rule.topic || 'general'
        acc[key] = [...(acc[key] ?? []), rule]
        return acc
      }, {}),
    [rules],
  )

  const keys = useMemo(() => Object.keys(grouped).sort(), [grouped])

  return (
    <section className="cad-panel">
      <h3>{t('panels.rulePackTitle')}</h3>
      {loading && <p>{t('common.loading')}</p>}
      {!loading && keys.length === 0 && <p>{t('panels.rulePackEmpty')}</p>}
      {!loading && keys.length > 0 && (
        <ul className="cad-rulepack">
          {keys.map((key) => (
            <li key={key}>
              <h4>{key}</h4>
              <ul>
                {grouped[key].map((rule) => (
                  <li key={rule.id}>
                    <strong>{rule.parameterKey}</strong> {rule.operator}{' '}
                    {rule.value}
                    {rule.unit ? ` ${rule.unit}` : ''}
                    {rule.overlays.length > 0 && (
                      <span className="cad-rulepack__overlay">
                        {rule.overlays.join(', ')}
                      </span>
                    )}
                  </li>
                ))}
              </ul>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}

export default RulePackExplanationPanel
