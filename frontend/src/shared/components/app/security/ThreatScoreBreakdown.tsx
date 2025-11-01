import type { FC } from 'react';
import type { ThreatData } from './types';

export interface ThreatScoreBreakdownProps {
  threatData: ThreatData;
  compact?: boolean;
}

export const ThreatScoreBreakdown: FC<ThreatScoreBreakdownProps> = ({ threatData, compact }) => {
  return (
    <div className={`flex h-full flex-col ${compact ? 'gap-4' : 'gap-6'}`}>
      <div className="flex items-end gap-4">
        <div className="text-5xl font-semibold text-white">{threatData.headline_score}</div>
        <div className="text-xs uppercase tracking-wide text-white/60">Headline Score</div>
      </div>
      <p className="text-sm text-white/60">
        Entity <span className="text-white/90">{threatData.entity_id}</span> currently trends above
        baseline threat potential.
      </p>
    </div>
  );
};

export default ThreatScoreBreakdown;
