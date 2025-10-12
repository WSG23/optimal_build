import { useMemo } from 'react'

export function GpsCapturePage() {
  const today = useMemo(
    () => new Date().toLocaleString(undefined, { dateStyle: 'medium' }),
    [],
  )

  return (
    <div className="gps-page">
      <section className="gps-page__summary">
        <div className="gps-card">
          <h2>Capture a property</h2>
          <p>
            Enter GPS coordinates or drop a pin on the map to capture a site.
            Add photos and field notes before sending to developers.
          </p>
          <form className="gps-form">
            <div className="gps-form__group">
              <label htmlFor="latitude">Latitude</label>
              <input id="latitude" name="latitude" placeholder="1.3000" />
            </div>
            <div className="gps-form__group">
              <label htmlFor="longitude">Longitude</label>
              <input id="longitude" name="longitude" placeholder="103.8500" />
            </div>
            <div className="gps-form__group">
              <label htmlFor="scenario">Development scenarios</label>
              <select id="scenario" name="scenario">
                <option>Raw land</option>
                <option>Existing building</option>
                <option>Heritage property</option>
                <option>Underused asset</option>
              </select>
            </div>
            <button type="button" className="gps-form__submit">
              Capture site
            </button>
          </form>
        </div>
        <div className="gps-card gps-card--map">
          <h2>Site preview</h2>
          <p>
            Map (Mapbox) preview placeholder. The production implementation will
            show coordinates, reverse-geocoded address, and draw radius overlays.
          </p>
        </div>
      </section>

      <section className="gps-page__panels">
        <div className="gps-panel">
          <h3>Quick analysis scenarios</h3>
          <p className="gps-panel__timestamp">Generated {today}</p>
          <ul className="gps-panel__list">
            <li>
              <strong>Raw land</strong>
              <span>
                Estimated max GFA ≈ <em>—</em>, plot ratio from URA zoning, nearby
                development count.
              </span>
            </li>
            <li>
              <strong>Existing building</strong>
              <span>
                Approved vs. potential GFA, uplift opportunities, transaction
                comparables.
              </span>
            </li>
            <li>
              <strong>Heritage property</strong>
              <span>
                Heritage risk level and notes on conservation requirements.
              </span>
            </li>
            <li>
              <strong>Underused asset</strong>
              <span>
                Transit access summary, rental benchmarks, repositioning hints.
              </span>
            </li>
          </ul>
        </div>
        <div className="gps-panel">
          <h3>Market intelligence</h3>
          <p>
            This panel will display comparables, supply dynamics, yield
            benchmarks, and absorption trends returned by the market intelligence
            service.
          </p>
          <dl className="gps-panel__metrics">
            <div>
              <dt>Property type</dt>
              <dd>—</dd>
            </div>
            <div>
              <dt>Location</dt>
              <dd>—</dd>
            </div>
            <div>
              <dt>Period analysed</dt>
              <dd>—</dd>
            </div>
            <div>
              <dt>Transactions</dt>
              <dd>—</dd>
            </div>
          </dl>
        </div>
        <div className="gps-panel">
          <h3>Marketing packs</h3>
          <p>
            Generate professional packs for developers and investors. The UI will
            integrate with the pack generator once APIs are finalised.
          </p>
          <div className="gps-pack-options">
            <button type="button">Universal pack</button>
            <button type="button">Investment memo</button>
            <button type="button">Sales brief</button>
            <button type="button">Lease brochure</button>
          </div>
          <div className="gps-pack-history">
            <p>No packs generated yet.</p>
          </div>
        </div>
      </section>

      <section className="gps-page__captures">
        <div className="gps-panel">
          <h3>Recent captures</h3>
          <table>
            <thead>
              <tr>
                <th>Property</th>
                <th>District</th>
                <th>Primary scenario</th>
                <th>Captured</th>
                <th>Pack status</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td colSpan={5}>Once capture API is wired, recent sites appear here.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </div>
  )
}

