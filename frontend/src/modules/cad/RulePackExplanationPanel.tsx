import type { RuleSummary } from '../../api/client'
import { useLocale } from '../../i18n/LocaleContext'

interface RulePackExplanationPanelProps {
  rules: RuleSummary[]
  loading?: boolean
}

export function RulePackExplanationPanel({ rules, loading = false }: RulePackExplanationPanelProps) {
  const { strings } = useLocale()

  const grouped = rules.reduce<Record<string, RuleSummary[]>>((acc, rule) => {
    const key = rule.authority || rule.topic || 'general'
    acc[key] = [...(acc[key] ?? []), rule]
    return acc
  }, {})

  const keys = Object.keys(grouped).sort()

  return (
    <section className="cad-panel">
      <h3>{strings.panels.rulePackTitle}</h3>
      {loading && <p>Loading…</p>}
      {!loading && keys.length === 0 && <p>{strings.panels.rulePackEmpty}</p>}
      {!loading && keys.length > 0 && (
        <ul className="cad-rulepack">
          {keys.map((key) => (
            <li key={key}>
              <h4>{key}</h4>
              <ul>
                {grouped[key].map((rule) => (
                  <li key={rule.id}>
                    <strong>{rule.parameterKey}</strong> {rule.operator} {rule.value}
                    {rule.unit ? ` ${rule.unit}` : ''}
                    {rule.overlays.length > 0 && (
                      <span className="cad-rulepack__overlay">{rule.overlays.join(', ')}</span>
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
