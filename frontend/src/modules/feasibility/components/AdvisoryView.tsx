interface AdvisoryViewProps {
  hints: string[]
  t: (key: string) => string
}

export function AdvisoryView({ hints, t }: AdvisoryViewProps) {
  if (hints.length === 0) {
    return null
  }

  return (
    <section className="feasibility-advisory" data-testid="advisory-hints">
      <h3>{t('wizard.results.advisory.title')}</h3>
      <ul>
        {hints.map((hint, index) => (
          <li key={`${hint}-${index}`}>{hint}</li>
        ))}
      </ul>
    </section>
  )
}
