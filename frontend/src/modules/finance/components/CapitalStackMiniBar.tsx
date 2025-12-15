import { useMemo } from 'react'
import type { FinanceScenarioSummary } from '../../../api/finance'

interface CapitalStackMiniBarProps {
  stack: NonNullable<FinanceScenarioSummary['capitalStack']>
}

export function CapitalStackMiniBar({ stack }: CapitalStackMiniBarProps) {
  const bars = useMemo(() => {
    const total = Number(stack.total) || 1
    const equityPct = (Number(stack.equityTotal) / total) * 100
    const debtPct = (Number(stack.debtTotal) / total) * 100
    const otherPct = (Number(stack.otherTotal) / total) * 100 // Or calculate remaining gap

    // Safety check for NaN
    return [
      {
        type: 'equity',
        width: isNaN(equityPct) ? 0 : equityPct,
        color: 'var(--ob-color-brand-primary)',
      },
      {
        type: 'debt',
        width: isNaN(debtPct) ? 0 : debtPct,
        color: 'var(--ob-color-brand-secondary)',
      },
      {
        type: 'gap',
        width: isNaN(otherPct) ? 0 : otherPct,
        color: 'var(--ob-color-neutral-300)',
      },
    ]
  }, [stack])

  return (
    <div
      className="capital-stack-mini-bar"
      style={{
        display: 'flex',
        height: '8px',
        width: '100%',
        borderRadius: '4px',
        overflow: 'hidden',
        background: 'var(--ob-color-surface-muted)',
      }}
    >
      {bars.map(
        (bar) =>
          bar.width > 0 && (
            <div
              key={bar.type}
              style={{
                width: `${bar.width}%`,
                background: bar.color,
                height: '100%',
              }}
              title={`${bar.type}: ${bar.width.toFixed(1)}%`}
            />
          ),
      )}
    </div>
  )
}
