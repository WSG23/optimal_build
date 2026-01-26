import { FormEvent, useEffect, useMemo, useState } from 'react'

import { AppLayout } from '../App'
import {
  ListingIntegrationAccount,
  fetchListingAccounts,
  fetchListingProviders,
  connectListingAccount,
  disconnectListingAccount,
  publishListing,
  type ListingProviderOption,
} from '../api/listings'

type ProviderKey = string

type ProviderState = Record<ProviderKey, string>

type PublishState = Record<
  ProviderKey,
  { propertyId: string; externalId: string; title: string }
>

export function AgentIntegrationsPage() {
  const [providers, setProviders] = useState<ListingProviderOption[]>([])
  const [accounts, setAccounts] = useState<ListingIntegrationAccount[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [message, setMessage] = useState<string | null>(null)
  const [codes, setCodes] = useState<ProviderState>({})
  const [publishState, setPublishState] = useState<PublishState>({})

  useEffect(() => {
    const controller = new AbortController()
    setLoading(true)
    Promise.all([
      fetchListingProviders(controller.signal),
      fetchListingAccounts(controller.signal),
    ])
      .then(([providerOptions, records]) => {
        setProviders(providerOptions)
        setAccounts(records)
        setCodes((current) => {
          const next = { ...current }
          providerOptions.forEach((provider) => {
            if (!(provider.provider in next)) {
              next[provider.provider] = ''
            }
          })
          return next
        })
        setPublishState((current) => {
          const next = { ...current }
          providerOptions.forEach((provider) => {
            if (!(provider.provider in next)) {
              next[provider.provider] = {
                propertyId: '',
                externalId: '',
                title: '',
              }
            }
          })
          return next
        })
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
    const code = codes[provider]?.trim()
    if (!code) {
      setError('Enter an authorization code before linking the account.')
      return
    }
    try {
      const account = await connectListingAccount(provider, code)
      setAccounts((current) => {
        const filtered = current.filter((row) => row.id !== account.id)
        return [...filtered, account]
      })
      const label =
        providers.find((entry) => entry.provider === provider)?.label ||
        provider
      setMessage(`${label} account linked.`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to connect account')
    }
  }

  const handlePublish = async (
    event: FormEvent<HTMLFormElement>,
    provider: ProviderKey,
  ) => {
    event.preventDefault()
    const publishValues = publishState[provider] ?? {
      propertyId: '',
      externalId: '',
      title: '',
    }
    const { propertyId, externalId, title } = publishValues
    if (!propertyId.trim()) {
      setError('Enter a property ID before publishing.')
      return
    }
    setError(null)
    try {
      const result = await publishListing(provider, {
        property_id: propertyId.trim(),
        external_id: externalId.trim() || `${provider}-listing`,
        title: title.trim() || propertyId.trim(),
      })
      const label =
        providers.find((entry) => entry.provider === provider)?.label ||
        provider
      setMessage(`${label} published ${result.listing_id}.`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to publish listing')
    }
  }

  const handleDisconnect = async (provider: ProviderKey) => {
    setError(null)
    try {
      await disconnectListingAccount(provider)
      setAccounts((existing) =>
        existing.filter((account) => account.provider !== provider),
      )
      const label =
        providers.find((entry) => entry.provider === provider)?.label ||
        provider
      setMessage(`${label} account disconnected.`)
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Failed to disconnect account',
      )
    }
  }

  return (
    <AppLayout
      title="Listing integrations"
      subtitle="Link listing platforms to publish and manage inventory."
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

        {providers.length === 0 ? (
          <section className="integrations__panel">
            <p className="integrations__empty">No providers configured yet.</p>
          </section>
        ) : (
          providers.map((provider) => {
            const account = accountByProvider.get(provider.provider)
            const connected = account?.status === 'connected'
            const publishValues = publishState[provider.provider] ?? {
              propertyId: '',
              externalId: '',
              title: '',
            }
            return (
              <section key={provider.provider} className="integrations__panel">
                <h2>{provider.label}</h2>
                {provider.description && (
                  <p className="integrations__subtitle">
                    {provider.description}
                  </p>
                )}
                <form
                  className="integrations__form"
                  onSubmit={(event) => handleConnect(event, provider.provider)}
                >
                  <label>
                    Authorization code
                    <input
                      value={codes[provider.provider] ?? ''}
                      onChange={(event) =>
                        setCodes((current) => ({
                          ...current,
                          [provider.provider]: event.target.value,
                        }))
                      }
                      placeholder="Paste OAuth authorization code"
                    />
                  </label>
                  <button type="submit">Link account</button>
                </form>
                <button
                  type="button"
                  className="integrations__disconnect"
                  onClick={() => handleDisconnect(provider.provider)}
                  disabled={!connected}
                >
                  Disconnect account
                </button>

                <form
                  className="integrations__form"
                  onSubmit={(event) => handlePublish(event, provider.provider)}
                >
                  <label>
                    Property ID
                    <input
                      value={publishValues.propertyId}
                      onChange={(event) =>
                        setPublishState((current) => ({
                          ...current,
                          [provider.provider]: {
                            ...current[provider.provider],
                            propertyId: event.target.value,
                          },
                        }))
                      }
                      placeholder="e.g. 4271b4aa-f33c-4fd7-ad23-d128a262842b"
                    />
                  </label>
                  <label>
                    Listing title
                    <input
                      value={publishValues.title}
                      onChange={(event) =>
                        setPublishState((current) => ({
                          ...current,
                          [provider.provider]: {
                            ...current[provider.provider],
                            title: event.target.value,
                          },
                        }))
                      }
                      placeholder="e.g. Grade A Office Tower"
                    />
                  </label>
                  <label>
                    External listing ID
                    <input
                      value={publishValues.externalId}
                      onChange={(event) =>
                        setPublishState((current) => ({
                          ...current,
                          [provider.provider]: {
                            ...current[provider.provider],
                            externalId: event.target.value,
                          },
                        }))
                      }
                      placeholder={`${provider.provider}-listing-1`}
                    />
                  </label>
                  <button type="submit">Publish listing</button>
                </form>
              </section>
            )
          })
        )}
      </div>
    </AppLayout>
  )
}

export default AgentIntegrationsPage
