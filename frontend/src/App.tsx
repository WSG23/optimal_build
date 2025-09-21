import { Link } from './router'

function App() {
  return (
    <div className="app-shell">
      <header className="app-shell__header">
        <h1>Optimal Build Studio</h1>
        <p>
          Explore automated compliance insights, land intelligence and feasibility analysis for Singapore
          developments.
        </p>
      </header>

      <nav className="app-shell__nav">
        <Link className="app-shell__nav-link" to="/feasibility">
          Launch feasibility wizard
        </Link>
        <a className="app-shell__nav-link" href="http://localhost:8000/docs" target="_blank" rel="noreferrer">
          View API reference
        </a>
      </nav>

      <section className="app-shell__section">
        <h2>Why start here?</h2>
        <ul>
          <li>Capture project basics once and reuse across compliance workflows.</li>
          <li>Review cross-agency rules synthesised from the knowledge platform.</li>
          <li>Generate buildability insights with clear next steps for the team.</li>
        </ul>
      </section>
    </div>
  )
}

export default App
