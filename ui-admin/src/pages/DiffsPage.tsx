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
      {error && <p className="text-sm text-red-400">{error}</p>}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        <aside className="lg:col-span-1 border border-slate-800 rounded p-3 bg-slate-900/40">
          <h3 className="text-sm font-semibold text-slate-200 mb-2">Rules</h3>
          <ul className="space-y-1">
            {diffs.map((diff) => (
              <li key={diff.rule_id}>
                <button
                  onClick={() => setSelected(diff.rule_id)}
                  className={`w-full text-left px-3 py-2 rounded text-sm transition-colors ${
                    selected === diff.rule_id
                      ? 'bg-slate-800 text-white'
                      : 'text-slate-300 hover:bg-slate-800'
                  }`}
                >
                  Rule #{diff.rule_id}
                </button>
              </li>
            ))}
            {diffs.length === 0 && (
              <li className="text-sm text-slate-400">No diffs available.</li>
            )}
          </ul>
        </aside>
        <section className="lg:col-span-3 border border-slate-800 rounded p-4 bg-slate-900/40">
          {activeDiff ? (
            <div>
              <h3 className="text-sm font-semibold text-slate-200 mb-4">Clause Change</h3>
              <DiffViewer baseline={activeDiff.baseline} updated={activeDiff.updated} />
            </div>
          ) : (
            <p className="text-sm text-slate-400">Select a rule to inspect its diff.</p>
          )}
        </section>
      </div>
    </div>
  );
};

export default DiffsPage;
