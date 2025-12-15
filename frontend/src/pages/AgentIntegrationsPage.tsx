import { FormEvent, useEffect, useMemo, useState } from 'react'

import { AppLayout } from '../App'
import {
  ListingIntegrationAccount,
  connectMockAccount,
  disconnectMockAccount,
  fetchListingAccounts,
  publishMockListing,
} from '../api/listings'

const PROVIDERS = [
  { key: 'propertyguru', label: 'PropertyGuru (mock)' },
  { key: 'edgeprop', label: 'EdgeProp (mock)' },
  { key: 'zoho_crm', label: 'Zoho CRM (mock)' },
] as const

type ProviderKey = (typeof PROVIDERS)[number]['key']

type ProviderState = Record<ProviderKey, string>

type PublishState = Record<
  ProviderKey,
  { propertyId: string; externalId: string }
>

const PROVIDER_LABEL: Record<ProviderKey, string> = PROVIDERS.reduce(
  (acc, provider) => ({
    ...acc,
    [provider.key]: provider.label,
  }),
  {} as Record<ProviderKey, string>,
)

function createDefaultCodes(): ProviderState {
  return PROVIDERS.reduce<ProviderState>((acc, provider) => {
    acc[provider.key] = 'mock-code'
    return acc
  }, {} as ProviderState)
}

function createDefaultPublishState(): PublishState {
  return PROVIDERS.reduce<PublishState>((acc, provider) => {
    acc[provider.key] = {
      propertyId: '',
      externalId: `${provider.key}-listing-1`,
    }
    return acc
  }, {} as PublishState)
}

export function AgentIntegrationsPage() {
  const [accounts, setAccounts] = useState<ListingIntegrationAccount[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [message, setMessage] = useState<string | null>(null)
  const [codes, setCodes] = useState<ProviderState>(() => createDefaultCodes())
  const [publishState, setPublishState] = useState<PublishState>(() =>
    createDefaultPublishState(),
  )

  useEffect(() => {
    const controller = new AbortController()
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
  }, [])

  const accountByProvider = useMemo(() => {
    const map = new Map<string, ListingIntegrationAccount>()
    accounts.forEach((account) => map.set(account.provider, account))
    return map
  }, [accounts])

  const handleConnect = async (
    event: FormEvent<HTMLFormElement>,
    provider: ProviderKey,
  ) => {
    event.preventDefault()
    setError(null)
    try {
      const account = await connectMockAccount(
        provider,
        codes[provider] || 'mock-code',
      )
      setAccounts((current) => {
        const filtered = current.filter((row) => row.id !== account.id)
        return [...filtered, account]
      })
      setMessage(`${PROVIDER_LABEL[provider]} account linked.`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to connect account')
    }
  }

  const handlePublish = async (
    event: FormEvent<HTMLFormElement>,
    provider: ProviderKey,
  ) => {
    event.preventDefault()
    const { propertyId, externalId } = publishState[provider]
    if (!propertyId.trim()) {
      setError('Enter a property ID before publishing.')
      return
    }
    setError(null)
    try {
      const result = await publishMockListing(provider, {
        property_id: propertyId.trim(),
        external_id: externalId.trim() || `${provider}-listing`,
        title: `Mock listing (${provider})`,
      })
      setMessage(`${PROVIDER_LABEL[provider]} published ${result.listing_id}.`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to publish listing')
    }
  }

  const handleDisconnect = async (provider: ProviderKey) => {
    setError(null)
    try {
      await disconnectMockAccount(provider)
      setAccounts((existing) =>
        existing.filter((account) => account.provider !== provider),
      )
      setMessage(`${PROVIDER_LABEL[provider]} account disconnected.`)
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Failed to disconnect account',
      )
    }
  }

  return (
    <AppLayout
      title="Listing integrations"
      subtitle="Link mock PropertyGuru and EdgeProp accounts while we wait for production credentials."
    >
      <div className="integrations">
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
                    <td>
                      {account.created_at
                        ? new Date(account.created_at).toLocaleString()
                        : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>

        {PROVIDERS.map((provider) => {
          const account = accountByProvider.get(provider.key)
          const connected = account?.status === 'connected'
          const publishValues = publishState[provider.key]
          return (
            <section key={provider.key} className="integrations__panel">
              <h2>{provider.label}</h2>
              <form
                className="integrations__form"
                onSubmit={(event) => handleConnect(event, provider.key)}
              >
                <label>
                  Authorization code
                  <input
                    value={codes[provider.key]}
                    onChange={(event) =>
                      setCodes((current) => ({
                        ...current,
                        [provider.key]: event.target.value,
                      }))
                    }
                    placeholder="mock-code"
                  />
                </label>
                <button type="submit">Link account</button>
              </form>
              <button
                type="button"
                className="integrations__disconnect"
                onClick={() => handleDisconnect(provider.key)}
                disabled={!connected}
              >
                Disconnect account
              </button>

              <form
                className="integrations__form"
                onSubmit={(event) => handlePublish(event, provider.key)}
              >
                <label>
                  Property ID
                  <input
                    value={publishValues.propertyId}
                    onChange={(event) =>
                      setPublishState((current) => ({
                        ...current,
                        [provider.key]: {
                          ...current[provider.key],
                          propertyId: event.target.value,
                        },
                      }))
                    }
                    placeholder="e.g. 4271b4aa-f33c-4fd7-ad23-d128a262842b"
                  />
                </label>
                <label>
                  External listing ID
                  <input
                    value={publishValues.externalId}
                    onChange={(event) =>
                      setPublishState((current) => ({
                        ...current,
                        [provider.key]: {
                          ...current[provider.key],
                          externalId: event.target.value,
                        },
                      }))
                    }
                    placeholder={`${provider.key}-listing-1`}
                  />
                </label>
                <button type="submit">Publish mock listing</button>
              </form>
            </section>
          )
        })}
      </div>
    </AppLayout>
  )
}

export default AgentIntegrationsPage
