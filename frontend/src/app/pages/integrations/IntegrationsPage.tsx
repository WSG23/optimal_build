export function IntegrationsPage() {
  return (
    <div className="int-page">
      <section className="int-card">
        <h2>Listing integrations hub (in progress)</h2>
        <p>
          The integration workspace will consolidate PropertyGuru, EdgeProp,
          Zoho CRM, and future portals. Agents will manage account tokens,
          publish listings, monitor automation jobs, and review audit logs here.
        </p>
        <ul>
          <li>Link or refresh integration accounts, monitor token expiry</li>
          <li>Publish/unpublish listings with status tracking and error handling</li>
          <li>Inspect audit history, retry failed jobs, tune automation settings</li>
          <li>View basic analytics once portals expose metrics (leads, impressions)</li>
        </ul>
        <p>
          Refer to <code>docs/ui_delivery_plan.md</code> for the detailed brief.
          The next milestones include API wiring, queue views, and account status
          components.
        </p>
      </section>
    </div>
  )
}

