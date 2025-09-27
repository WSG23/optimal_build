import { useMemo } from 'react';
import { diffLines } from 'diff';

interface DiffViewerProps {
  baseline: string;
  updated: string;
}

type DiffLine = {
  type: 'added' | 'removed' | 'context';
  oldNumber: number | null;
  newNumber: number | null;
  text: string;
};

function normaliseLines(text: string): string[] {
  const lines = text.split('\n');
  if (lines.length && lines[lines.length - 1] === '') {
    lines.pop();
  }
  return lines;
}

const DiffViewer = ({ baseline, updated }: DiffViewerProps) => {
  const rows = useMemo<DiffLine[]>(() => {
    const segments = diffLines(baseline, updated);
    let oldPointer = 1;
    let newPointer = 1;

    const diffRows: DiffLine[] = [];

    for (const segment of segments) {
      const type: DiffLine['type'] = segment.added
        ? 'added'
        : segment.removed
        ? 'removed'
        : 'context';

      const lines = normaliseLines(segment.value);
      if (lines.length === 0) {
        lines.push('');
      }

      for (const line of lines) {
        diffRows.push({
          type,
          oldNumber: segment.added ? null : oldPointer++,
          newNumber: segment.removed ? null : newPointer++,
          text: line,
        });
      }
    }

    return diffRows;
  }, [baseline, updated]);

  if (rows.length === 0) {
    return (
      <div className="rounded border border-slate-800 bg-slate-950 p-4 text-sm text-slate-300">
        No differences detected.
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded border border-slate-800 bg-slate-950 text-xs font-mono text-slate-200 shadow-inner">
      <div className="grid grid-cols-[60px_60px_1fr] bg-slate-900/60 px-3 py-2 text-[0.7rem] uppercase tracking-wide text-slate-400">
        <span className="text-right">Old</span>
        <span className="text-right">New</span>
        <span>Change</span>
      </div>
      <div>
        {rows.map((row, index) => {
          const baseClasses = 'grid grid-cols-[60px_60px_1fr] px-3 py-1 whitespace-pre-wrap';
          const tone =
            row.type === 'added'
              ? 'bg-emerald-900/30 text-emerald-200'
              : row.type === 'removed'
              ? 'bg-rose-900/30 text-rose-200'
              : 'bg-slate-950 text-slate-200';

          return (
            <div className={`${baseClasses} ${tone}`} key={`${row.type}-${index}-${row.oldNumber}-${row.newNumber}`}>
              <span className="text-right text-slate-400">
                {row.oldNumber !== null ? row.oldNumber : ''}
              </span>
              <span className="text-right text-slate-400">
                {row.newNumber !== null ? row.newNumber : ''}
              </span>
              <span>{`${row.type === 'added' ? '+' : row.type === 'removed' ? '-' : ' '} ${row.text || '\u00a0'}`}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default DiffViewer;
