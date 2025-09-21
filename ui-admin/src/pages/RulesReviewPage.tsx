import { useEffect, useMemo, useState } from 'react';
import Header from '../components/Header';
import { ReviewAPI } from '../api/client';
import type { RuleRecord } from '../types';

const RulesReviewPage = () => {
  const [rules, setRules] = useState<RuleRecord[]>([]);
  const [selectedRuleId, setSelectedRuleId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    setLoading(true);
    ReviewAPI.getRules()
      .then((response) => {
        setRules(response.items);
        setError(null);
        if (response.items.length && selectedRuleId === null) {
          setSelectedRuleId(response.items[0].id);
        }
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
    // We only want to load rules on initial mount.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const selectedRule = useMemo(
    () => rules.find((rule) => rule.id === selectedRuleId) ?? null,
    [rules, selectedRuleId]
  );

  const handleAction = async (action: 'approve' | 'reject' | 'publish') => {
    if (!selectedRule) return;
    setIsSubmitting(true);
    try {
      const { item } = await ReviewAPI.reviewRule(selectedRule.id, action);
      setRules((prev) => prev.map((rule) => (rule.id === item.id ? item : rule)));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update rule');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div>
      <Header title="Rules Review" />
      {loading && <p className="text-sm text-slate-400">Loading rules…</p>}
      {error && <p className="text-sm text-red-400">{error}</p>}
      {!loading && !error && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <div className="overflow-hidden rounded-lg border border-slate-800">
              <table className="min-w-full divide-y divide-slate-800">
                <thead className="bg-slate-900">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium uppercase text-slate-400">Parameter</th>
                    <th className="px-4 py-3 text-left text-xs font-medium uppercase text-slate-400">Requirement</th>
                    <th className="px-4 py-3 text-left text-xs font-medium uppercase text-slate-400">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {rules.map((rule) => (
                    <tr
                      key={rule.id}
                      className={`cursor-pointer hover:bg-slate-900/70 ${
                        selectedRuleId === rule.id ? 'bg-slate-900/80' : ''
                      }`}
                      onClick={() => setSelectedRuleId(rule.id)}
                    >
                      <td className="px-4 py-3 text-sm text-slate-200">
                        <div className="font-semibold">{rule.parameter_key}</div>
                        <div className="text-xs text-slate-400">
                          {rule.jurisdiction} · {rule.authority}
                        </div>
                      </td>
                      <td className="px-4 py-3 text-sm text-slate-300">
                        {rule.operator} {rule.value} {rule.unit || ''}
                      </td>
                      <td className="px-4 py-3 text-sm">
                        <span
                          className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ${
                            rule.review_status === 'approved'
                              ? 'bg-emerald-500/20 text-emerald-300'
                              : rule.review_status === 'rejected'
                              ? 'bg-red-500/20 text-red-300'
                              : 'bg-amber-500/20 text-amber-200'
                          }`}
                        >
                          {rule.review_status.replace('_', ' ')}
                        </span>
                      </td>
                    </tr>
                  ))}
                  {rules.length === 0 && (
                    <tr>
                      <td colSpan={3} className="px-4 py-6 text-center text-sm text-slate-400">
                        No rules awaiting review.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          <div className="border border-slate-800 rounded-lg p-4 bg-slate-900/40">
            {selectedRule ? (
              <div className="space-y-4">
                <div>
                  <h3 className="text-sm font-semibold text-slate-200">Overlays</h3>
                  <div className="flex flex-wrap gap-2 mt-2">
                    {selectedRule.overlays.length ? (
                      selectedRule.overlays.map((overlay) => (
                        <span
                          key={overlay}
                          className="px-3 py-1 text-xs rounded-full bg-indigo-500/20 text-indigo-200"
                        >
                          {overlay}
                        </span>
                      ))
                    ) : (
                      <span className="text-xs text-slate-400">No overlays</span>
                    )}
                  </div>
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-slate-200">Advisory Hints</h3>
                  <ul className="mt-2 space-y-2 text-sm text-slate-300 list-disc list-inside">
                    {selectedRule.advisory_hints.map((hint, index) => (
                      <li key={index}>{hint}</li>
                    ))}
                    {selectedRule.advisory_hints.length === 0 && (
                      <li className="text-xs text-slate-400">No hints available.</li>
                    )}
                  </ul>
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-slate-200">Normalized Parameters</h3>
                  <ul className="mt-2 space-y-2 text-xs text-slate-300">
                    {selectedRule.normalized.map((param) => (
                      <li key={param.parameter_key} className="border border-slate-800 rounded p-2">
                        <div className="font-semibold text-slate-200">{param.parameter_key}</div>
                        <div>
                          {param.operator} {param.value} {param.unit || ''}
                        </div>
                        {param.hints.length > 0 && (
                          <ul className="list-disc list-inside text-[11px] text-slate-400 mt-1">
                            {param.hints.map((hint) => (
                              <li key={hint}>{hint}</li>
                            ))}
                          </ul>
                        )}
                      </li>
                    ))}
                    {selectedRule.normalized.length === 0 && (
                      <li className="text-xs text-slate-400">No normalized data available.</li>
                    )}
                  </ul>
                </div>
                <div className="flex flex-wrap gap-2">
                  <button
                    onClick={() => handleAction('approve')}
                    disabled={isSubmitting}
                    className="px-4 py-2 rounded bg-emerald-500 text-slate-900 text-sm font-semibold hover:bg-emerald-400 disabled:opacity-60"
                  >
                    Approve
                  </button>
                  <button
                    onClick={() => handleAction('publish')}
                    disabled={isSubmitting}
                    className="px-4 py-2 rounded bg-indigo-500 text-slate-900 text-sm font-semibold hover:bg-indigo-400 disabled:opacity-60"
                  >
                    Publish
                  </button>
                </div>
              </div>
            ) : (
              <p className="text-sm text-slate-400">Select a rule to review its details.</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default RulesReviewPage;
