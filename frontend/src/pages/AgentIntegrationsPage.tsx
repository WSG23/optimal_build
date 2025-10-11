import { FormEvent, useEffect, useMemo, useState } from 'react'

import { AppLayout } from '../App'
import {
  ListingIntegrationAccount,
  connectMockPropertyGuru,
  disconnectMockPropertyGuru,
  fetchListingAccounts,
  publishMockPropertyGuru,
} from '../api/listings'

function useAbortController() {
  return useMemo(() => new AbortController(), [])
}

export function AgentIntegrationsPage() {
  const controller = useAbortController()
  const [accounts, setAccounts] = useState<ListingIntegrationAccount[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [code, setCode] = useState('mock-code')
  const [propertyId, setPropertyId] = useState('')
  const [externalId, setExternalId] = useState('mock-listing-1')
  const [message, setMessage] = useState<string | null>(null)

  useEffect(() => {
    setLoading(true)
    fetchListingAccounts(controller.signal)
      .then((records) => {
        setAccounts(records)
      })
      .catch((err) => {
        if (err instanceof Error && err.name === 'AbortError') {
          return
        }
        setError(err instanceof Error ? err.message : 'Failed to load accounts')
      })
      .finally(() => setLoading(false))

    return () => controller.abort()
  }, [controller])

  const handleConnect = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setError(null)
    try {
      const account = await connectMockPropertyGuru(code.trim() || 'mock-code')
      setAccounts((existing) => {
        const filtered = existing.filter((row) => row.id !== account.id)
        return [...filtered, account]
      })
      setMessage('Mock PropertyGuru account linked.')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to connect account')
    }
  }

  const handlePublish = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!propertyId.trim()) {
      setError('Enter a property ID before publishing.')
      return
    }
    setError(null)
    try {
      const result = await publishMockPropertyGuru({
        property_id: propertyId.trim(),
        external_id: externalId.trim() || 'mock-listing',
        title: 'Mock listing from integration page',
      })
      setMessage(`Published mock listing ${result.listing_id}.`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to publish listing')
    }
  }

  const handleDisconnect = async () => {
    setError(null)
    try {
      await disconnectMockPropertyGuru()
      setAccounts((existing) =>
        existing.filter((account) => account.provider !== 'propertyguru'),
      )
      setMessage('Mock PropertyGuru account disconnected.')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to disconnect account')
    }
  }

  return (
    <AppLayout
      title="Listing integrations"
      subtitle="Connect PropertyGuru using mock credentials while we wait for production access."
    >
      {error && <div className="integrations__error">{error}</div>}
      {message && <div className="integrations__message">{message}</div>}

      <section className="integrations__panel">
        <h2>Linked accounts</h2>
        {loading ? (
          <p>Loading accounts…</p>
        ) : accounts.length === 0 ? (
          <p className="integrations__empty">No accounts linked yet.</p>
        ) : (
          <table className="integrations__table">
            <thead>
              <tr>
                <th>Provider</th>
                <th>Status</th>
                <th>Connected</th>
              </tr>
            </thead>
            <tbody>
              {accounts.map((account) => (
                <tr key={account.id}>
                  <td>{account.provider}</td>
                  <td>{account.status}</td>
                  <td>{new Date(account.created_at).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      <section className="integrations__panel">
        <h2>Link PropertyGuru (mock)</h2>
        <form className="integrations__form" onSubmit={handleConnect}>
          <label>
            Authorization code
            <input
              value={code}
              onChange={(event) => setCode(event.target.value)}
              placeholder="mock-code"
            />
          </label>
          <button type="submit">Link account</button>
        </form>
        <button
          type="button"
          className="integrations__disconnect"
          onClick={handleDisconnect}
          disabled={accounts.every((account) => account.provider !== 'propertyguru')}
        >
          Disconnect account
        </button>
      </section>

      <section className="integrations__panel">
        <h2>Publish mock listing</h2>
        <form className="integrations__form" onSubmit={handlePublish}>
          <label>
            Property ID
            <input
              value={propertyId}
              onChange={(event) => setPropertyId(event.target.value)}
              placeholder="e.g. 4271b4aa-f33c-4fd7-ad23-d128a262842b"
            />
          </label>
          <label>
            External listing ID
            <input
              value={externalId}
              onChange={(event) => setExternalId(event.target.value)}
              placeholder="mock-listing-1"
            />
          </label>
          <button type="submit">Publish mock listing</button>
        </form>
        <p className="integrations__hint">
          Tip: use the property ID from the advisory page (e.g. Market Demo Tower) to
          simulate the full flow.
        </p>
      </section>
    </AppLayout>
  )
}

export default AgentIntegrationsPage
