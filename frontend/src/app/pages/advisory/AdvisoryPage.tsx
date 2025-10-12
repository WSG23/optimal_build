export function AdvisoryPage() {
  return (
    <div className="adv-page">
      <section className="adv-card">
        <h2>Advisory console (in progress)</h2>
        <p>
          This placeholder outlines the upcoming advisory workspace. The final UI
          will surface asset mix strategy, pricing guidance, absorption forecasts,
          and market feedback loops powered by the backend advisory services.
        </p>
        <ul>
          <li>Compare advisory scenarios (base / upside / downside)</li>
          <li>Expose pricing, absorption, and confidence metrics</li>
          <li>Capture market feedback and status for developer handoff</li>
          <li>Export advisory briefs and notify stakeholders</li>
        </ul>
        <p>
          Detailed requirements are tracked in <code>docs/ui_delivery_plan.md</code>.
          Implementation will follow once wireframes and data contracts are finalised.
        </p>
      </section>
    </div>
  )
}

