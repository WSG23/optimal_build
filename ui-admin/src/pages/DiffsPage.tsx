import { useEffect, useState } from 'react';
import Header from '../components/Header';
import { ReviewAPI } from '../api/client';
import type { DiffRecord } from '../types';
import DiffViewer from '../components/DiffViewer';

const DiffsPage = () => {
  const [diffs, setDiffs] = useState<DiffRecord[]>([]);
  const [selected, setSelected] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    ReviewAPI.getDiffs()
      .then((response) => {
        setDiffs(response.items);
        if (response.items.length) {
          setSelected(response.items[0].rule_id);
        }
        setError(null);
      })
      .catch((err) => setError(err.message));
  }, []);

  const activeDiff = diffs.find((diff) => diff.rule_id === selected) ?? null;

  return (
    <div>
      <Header title="Diffs" />
      {error && <p className="text-sm text-error-strong/85">{error}</p>}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        <aside className="lg:col-span-1 border border-border-neutral/40 rounded-lg p-3 bg-surface-inverse/40">
          <h3 className="text-sm font-semibold text-text-inverse mb-2">Rules</h3>
          <ul className="space-y-1">
            {diffs.map((diff) => (
              <li key={diff.rule_id}>
                <button
                  onClick={() => setSelected(diff.rule_id)}
                  className={`w-full text-left px-3 py-2 rounded-md text-sm transition-colors ${
                    selected === diff.rule_id
                      ? 'bg-surface-inverse/70 text-text-inverse'
                      : 'text-text-inverse/80 hover:bg-surface-inverse/50'
                  }`}
                >
                  Rule #{diff.rule_id}
                </button>
              </li>
            ))}
            {diffs.length === 0 && (
              <li className="text-sm text-text-inverse/70">No diffs available.</li>
            )}
          </ul>
        </aside>
        <section className="lg:col-span-3 border border-border-neutral/40 rounded-lg p-4 bg-surface-inverse/40">
          {activeDiff ? (
            <div>
              <h3 className="text-sm font-semibold text-text-inverse mb-4">Clause Change</h3>
              <DiffViewer baseline={activeDiff.baseline} updated={activeDiff.updated} />
            </div>
          ) : (
            <p className="text-sm text-text-inverse/70">Select a rule to inspect its diff.</p>
          )}
        </section>
      </div>
    </div>
  );
};

export default DiffsPage;
