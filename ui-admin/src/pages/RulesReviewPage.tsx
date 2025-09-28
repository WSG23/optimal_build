import { useEffect, useMemo, useState } from 'react'
import Header from '../components/Header'
import { ReviewAPI } from '../api/client'
import type { RuleRecord } from '../types'
import { toErrorMessage } from '../utils/error'

const RulesReviewPage = () => {
  const [rules, setRules] = useState<RuleRecord[]>([])
  const [selectedRuleId, setSelectedRuleId] = useState<number | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [isSubmitting, setIsSubmitting] = useState(false)

  useEffect(() => {
    const loadRules = async () => {
      setLoading(true)
      try {
        const response = await ReviewAPI.getRules()
        setRules(response.items)
        setError(null)
        if (response.items.length && selectedRuleId === null) {
          setSelectedRuleId(response.items[0].id)
        }
      } catch (error) {
        setError(toErrorMessage(error, 'Failed to load rules'))
      } finally {
        setLoading(false)
      }
    }

    void loadRules()
    // We only want to load rules on initial mount.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const selectedRule = useMemo(
    () => rules.find((rule) => rule.id === selectedRuleId) ?? null,
    [rules, selectedRuleId],
  )

  const handleAction = async (action: 'approve' | 'reject' | 'publish') => {
    if (!selectedRule) return
    setIsSubmitting(true)
    try {
      const { item } = await ReviewAPI.reviewRule(selectedRule.id, action)
      setRules((prev) =>
        prev.map((rule) => (rule.id === item.id ? item : rule)),
      )
    } catch (err) {
      setError(toErrorMessage(err, 'Failed to update rule'))
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div>
      <Header title="Rules Review" />
      {loading && (
        <p className="text-sm text-text-inverse/70">Loading rules…</p>
      )}
      {error && <p className="text-sm text-error-strong/85">{error}</p>}
      {!loading && !error && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <div className="overflow-hidden rounded-lg border border-border-neutral/40">
              <table className="min-w-full divide-y divide-border-neutral/40">
                <thead className="bg-surface-inverse/60">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium uppercase text-text-inverse/70">
                      Parameter
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium uppercase text-text-inverse/70">
                      Requirement
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium uppercase text-text-inverse/70">
                      Status
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border-neutral/40">
                  {rules.map((rule) => (
                    <tr
                      key={rule.id}
                      className={`cursor-pointer hover:bg-surface-inverse/50 ${
                        selectedRuleId === rule.id
                          ? 'bg-surface-inverse/60'
                          : ''
                      }`}
                      onClick={() => {
                        setSelectedRuleId(rule.id)
                      }}
                    >
                      <td className="px-4 py-3 text-sm text-text-inverse">
                        <div className="font-semibold">
                          {rule.parameter_key}
                        </div>
                        <div className="text-xs text-text-inverse/70">
                          {rule.jurisdiction} · {rule.authority}
                        </div>
                      </td>
                      <td className="px-4 py-3 text-sm text-text-inverse/80">
                        {rule.operator} {rule.value} {rule.unit || ''}
                      </td>
                      <td className="px-4 py-3 text-sm">
                        <span
                          className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ${
                            rule.review_status === 'approved'
                              ? 'bg-success-strong/20 text-success-strong/80'
                              : rule.review_status === 'rejected'
                                ? 'bg-error-strong/20 text-error-strong/80'
                                : 'bg-warning-strong/20 text-warning-strong/80'
                          }`}
                        >
                          {rule.review_status.replace('_', ' ')}
                        </span>
                      </td>
                    </tr>
                  ))}
                  {rules.length === 0 && (
                    <tr>
                      <td
                        colSpan={3}
                        className="px-4 py-6 text-center text-sm text-text-inverse/70"
                      >
                        No rules awaiting review.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          <div className="border border-border-neutral/40 rounded-lg p-4 bg-surface-inverse/40">
            {selectedRule ? (
              <div className="space-y-4">
                <div>
                  <h3 className="text-sm font-semibold text-text-inverse">
                    Overlays
                  </h3>
                  <div className="flex flex-wrap gap-2 mt-2">
                    {selectedRule.overlays.length ? (
                      selectedRule.overlays.map((overlay) => (
                        <span
                          key={overlay}
                          className="px-3 py-1 text-xs rounded-full bg-brand-primary/20 text-brand-soft"
                        >
                          {overlay}
                        </span>
                      ))
                    ) : (
                      <span className="text-xs text-text-inverse/70">
                        No overlays
                      </span>
                    )}
                  </div>
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-text-inverse">
                    Advisory Hints
                  </h3>
                  <ul className="mt-2 space-y-2 text-sm text-text-inverse/80 list-disc list-inside">
                    {selectedRule.advisory_hints.map((hint, index) => (
                      <li key={index}>{hint}</li>
                    ))}
                    {selectedRule.advisory_hints.length === 0 && (
                      <li className="text-xs text-text-inverse/70">
                        No hints available.
                      </li>
                    )}
                  </ul>
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-text-inverse">
                    Normalized Parameters
                  </h3>
                  <ul className="mt-2 space-y-2 text-xs text-text-inverse/80">
                    {selectedRule.normalized.map((param) => (
                      <li
                        key={param.parameter_key}
                        className="border border-border-neutral/40 rounded p-2"
                      >
                        <div className="font-semibold text-text-inverse">
                          {param.parameter_key}
                        </div>
                        <div>
                          {param.operator} {param.value} {param.unit || ''}
                        </div>
                        {param.hints.length > 0 && (
                          <ul className="list-disc list-inside text-[11px] text-text-inverse/70 mt-1">
                            {param.hints.map((hint) => (
                              <li key={hint}>{hint}</li>
                            ))}
                          </ul>
                        )}
                      </li>
                    ))}
                    {selectedRule.normalized.length === 0 && (
                      <li className="text-xs text-text-inverse/70">
                        No normalized data available.
                      </li>
                    )}
                  </ul>
                </div>
                <div className="flex flex-wrap gap-2">
                  <button
                    onClick={() => {
                      void handleAction('approve')
                    }}
                    disabled={isSubmitting}
                    className="px-4 py-2 rounded bg-success-strong text-text-inverse text-sm font-semibold hover:bg-success-strong/85 disabled:opacity-60"
                  >
                    Approve
                  </button>
                  <button
                    onClick={() => {
                      void handleAction('publish')
                    }}
                    disabled={isSubmitting}
                    className="px-4 py-2 rounded bg-brand-primary text-text-inverse text-sm font-semibold hover:bg-brand-primary-emphasis disabled:opacity-60"
                  >
                    Publish
                  </button>
                </div>
              </div>
            ) : (
              <p className="text-sm text-text-inverse/70">
                Select a rule to review its details.
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default RulesReviewPage
