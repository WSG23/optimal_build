import { useEffect, useState } from 'react'
import type {
  ListingIntegrationAccount,
  ListingProviderOption,
} from '../../../api/listings'
import {
  fetchListingAccounts,
  fetchListingProviders,
  connectListingAccount,
  disconnectListingAccount,
  publishListing,
} from '../../../api/listings'

export function IntegrationsPage() {
  const [providers, setProviders] = useState<ListingProviderOption[]>([])
  const [accounts, setAccounts] = useState<ListingIntegrationAccount[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [connectingProvider, setConnectingProvider] = useState<string | null>(
    null,
  )
  const [publishingProvider, setPublishingProvider] = useState<string | null>(
    null,
  )
  const [publishForm, setPublishForm] = useState<{
    provider: string
    propertyId: string
    title: string
    price: string
  } | null>(null)

  useEffect(() => {
    loadAccounts()
  }, [])

  async function loadAccounts() {
    setLoading(true)
    setError(null)
    try {
      const [providerOptions, data] = await Promise.all([
        fetchListingProviders(),
        fetchListingAccounts(),
      ])
      setProviders(providerOptions)
      setAccounts(data)
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to load accounts'
      // Handle 401 gracefully - user not logged in
      if (
        errorMessage.includes('401') ||
        errorMessage.includes('Unauthorized')
      ) {
        setError('Login required to view integrations')
      } else {
        setError(errorMessage)
      }
    } finally {
      setLoading(false)
    }
  }

  async function handleConnect(provider: string) {
    setConnectingProvider(provider)
    try {
      const code = window.prompt(
        'Enter the OAuth authorization code for this provider',
      )
      if (!code) {
        setConnectingProvider(null)
        return
      }
      const newAccount = await connectListingAccount(provider, code)
      setAccounts([
        ...accounts.filter((a) => a.provider !== provider),
        newAccount,
      ])
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Connection failed')
    } finally {
      setConnectingProvider(null)
    }
  }

  async function handleDisconnect(provider: string) {
    if (!confirm(`Disconnect from ${provider}?`)) return

    try {
      await disconnectListingAccount(provider)
      setAccounts(accounts.filter((a) => a.provider !== provider))
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Disconnection failed')
    }
  }

  async function handlePublish(e: React.FormEvent) {
    e.preventDefault()
    if (!publishForm) return

    setPublishingProvider(publishForm.provider)
    try {
      const result = await publishListing(publishForm.provider, {
        property_id: publishForm.propertyId,
        title: publishForm.title,
        price: parseFloat(publishForm.price) || 0,
      })
      alert(`Published! Listing ID: ${result.listing_id}`)
      setPublishForm(null)
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Publishing failed')
    } finally {
      setPublishingProvider(null)
    }
  }

  function getAccountForProvider(providerId: string) {
    return accounts.find((a) => a.provider === providerId)
  }

  function isConnected(providerId: string) {
    return accounts.some(
      (a) => a.provider === providerId && a.status === 'connected',
    )
  }

  return (
    <div
      style={{
        padding: 'var(--ob-space-600) 2rem',
        maxWidth: '1200px',
        margin: '0 auto',
        fontFamily:
          '-apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", system-ui, sans-serif',
        color: 'var(--ob-color-bg-inverse)',
      }}
    >
      {/* Header */}
      <header style={{ marginBottom: 'var(--ob-space-600)' }}>
        <h1
          style={{
            fontSize: '3rem',
            fontWeight: 700,
            letterSpacing: '-0.015em',
            margin: '0 0 0.5rem',
            lineHeight: 1.1,
          }}
        >
          Listing Integrations
        </h1>
        <p
          style={{
            fontSize: '1.25rem',
            color: 'var(--ob-color-text-secondary)',
            fontWeight: 400,
            margin: 0,
            letterSpacing: '-0.01em',
          }}
        >
          Connect and manage property listing portals
        </p>
      </header>

      {/* Integration Cards */}
      <section style={{ marginBottom: 'var(--ob-space-600)' }}>
        <h2
          style={{
            fontSize: '1.75rem',
            fontWeight: 600,
            letterSpacing: '-0.01em',
            margin: '0 0 1.5rem',
          }}
        >
          Connected Platforms
        </h2>

        {loading ? (
          <div
            style={{
              padding: 'var(--ob-space-600)',
              textAlign: 'center',
              background: 'white',
              border: '1px solid var(--ob-color-border-default)',
              borderRadius: 'var(--ob-radius-sm)',
              color: 'var(--ob-color-text-secondary)',
            }}
          >
            Loading integrations...
          </div>
        ) : error ? (
          <div
            style={{
              padding: 'var(--ob-space-600) 2rem',
              textAlign: 'center',
              background: 'white',
              border: '1px solid var(--ob-color-border-default)',
              borderRadius: 'var(--ob-radius-sm)',
            }}
          >
            <div
              style={{
                width: '60px',
                height: '60px',
                margin: '0 auto 1.5rem',
                background: '#fff5f5',
                borderRadius: '50%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '1.5rem',
              }}
            >
              🔒
            </div>
            <p
              style={{
                fontSize: '1.125rem',
                fontWeight: 500,
                color: 'var(--ob-color-bg-inverse)',
                marginBottom: 'var(--ob-space-100)',
                letterSpacing: '-0.01em',
              }}
            >
              {error}
            </p>
            <p
              style={{
                fontSize: '0.9375rem',
                color: 'var(--ob-color-text-secondary)',
                margin: 0,
                letterSpacing: '-0.005em',
              }}
            >
              Authentication is required to manage listing integrations
            </p>
          </div>
        ) : (
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
              gap: 'var(--ob-space-300)',
            }}
          >
            {providers.length === 0 ? (
              <div
                style={{
                  padding: 'var(--ob-space-600)',
                  textAlign: 'center',
                  background: 'white',
                  border: '1px solid var(--ob-color-border-default)',
                  borderRadius: 'var(--ob-radius-sm)',
                  color: 'var(--ob-color-text-secondary)',
                }}
              >
                No listing providers configured yet.
              </div>
            ) : (
              providers.map((provider) => {
                const account = getAccountForProvider(provider.provider)
                const connected = isConnected(provider.provider)
                const connecting = connectingProvider === provider.provider
                const accent = provider.brandColor || '#1f2937'
                const label = provider.label || provider.provider
                const description =
                  provider.description || 'Listing integration provider'

                return (
                  <div
                    key={provider.provider}
                    style={{
                      background: 'white',
                      border: `2px solid ${connected ? accent : 'var(--ob-color-border-default)'}`,
                      borderRadius: 'var(--ob-radius-sm)',
                      padding: 'var(--ob-space-400)',
                      transition: 'all 0.2s ease',
                    }}
                  >
                    <div
                      style={{
                        width: '48px',
                        height: '48px',
                        borderRadius: 'var(--ob-radius-sm)',
                        background: accent,
                        marginBottom: 'var(--ob-space-200)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: 'white',
                        fontSize: '1.5rem',
                        fontWeight: 700,
                      }}
                    >
                      {label[0]}
                    </div>

                    <h3
                      style={{
                        fontSize: '1.25rem',
                        fontWeight: 600,
                        margin: '0 0 0.5rem',
                        letterSpacing: '-0.01em',
                      }}
                    >
                      {label}
                    </h3>

                    <p
                      style={{
                        fontSize: '0.9375rem',
                        color: 'var(--ob-color-text-secondary)',
                        margin: '0 0 1.5rem',
                        letterSpacing: '-0.005em',
                      }}
                    >
                      {description}
                    </p>

                    {connected && account && (
                      <div
                        style={{
                          padding: 'var(--ob-space-150) 1rem',
                          background: 'var(--ob-color-bg-muted)',
                          borderRadius: 'var(--ob-radius-sm)',
                          marginBottom: 'var(--ob-space-200)',
                          fontSize: '0.875rem',
                          color: 'var(--ob-color-text-secondary)',
                        }}
                      >
                        <div style={{ marginBottom: 'var(--ob-space-50)' }}>
                          <strong
                            style={{ color: 'var(--ob-color-bg-inverse)' }}
                          >
                            Status:
                          </strong>{' '}
                          {account.status}
                        </div>
                        <div style={{ fontSize: '0.8125rem' }}>
                          Connected{' '}
                          {new Date(account.created_at).toLocaleDateString()}
                        </div>
                      </div>
                    )}

                    <div
                      style={{ display: 'flex', gap: 'var(--ob-space-150)' }}
                    >
                      {connected ? (
                        <>
                          <button
                            type="button"
                            onClick={() =>
                              setPublishForm({
                                provider: provider.provider,
                                propertyId: '',
                                title: '',
                                price: '',
                              })
                            }
                            style={{
                              flex: 1,
                              padding: 'var(--ob-space-150) 1rem',
                              fontSize: '0.9375rem',
                              fontWeight: 500,
                              color: 'white',
                              background: accent,
                              border: 'none',
                              borderRadius: 'var(--ob-radius-sm)',
                              cursor: 'pointer',
                              transition: 'opacity 0.2s ease',
                              letterSpacing: '-0.005em',
                            }}
                            onMouseEnter={(e) => {
                              e.currentTarget.style.opacity = '0.85'
                            }}
                            onMouseLeave={(e) => {
                              e.currentTarget.style.opacity = '1'
                            }}
                          >
                            Publish
                          </button>
                          <button
                            type="button"
                            onClick={() => handleDisconnect(provider.provider)}
                            style={{
                              padding: 'var(--ob-space-150) 1rem',
                              fontSize: '0.9375rem',
                              fontWeight: 500,
                              color: 'var(--ob-color-bg-inverse)',
                              background: 'transparent',
                              border:
                                '1px solid var(--ob-color-border-default)',
                              borderRadius: 'var(--ob-radius-sm)',
                              cursor: 'pointer',
                              transition: 'all 0.2s ease',
                              letterSpacing: '-0.005em',
                            }}
                            onMouseEnter={(e) => {
                              e.currentTarget.style.background =
                                'var(--ob-color-bg-muted)'
                            }}
                            onMouseLeave={(e) => {
                              e.currentTarget.style.background = 'transparent'
                            }}
                          >
                            Disconnect
                          </button>
                        </>
                      ) : (
                        <button
                          type="button"
                          onClick={() => handleConnect(provider.provider)}
                          disabled={connecting}
                          style={{
                            flex: 1,
                            padding: 'var(--ob-space-150) 1rem',
                            fontSize: '0.9375rem',
                            fontWeight: 500,
                            color: connecting ? '#6e6e73' : 'white',
                            background: connecting ? '#f5f5f7' : accent,
                            border: 'none',
                            borderRadius: 'var(--ob-radius-sm)',
                            cursor: connecting ? 'not-allowed' : 'pointer',
                            transition: 'opacity 0.2s ease',
                            letterSpacing: '-0.005em',
                          }}
                          onMouseEnter={(e) => {
                            if (!connecting)
                              e.currentTarget.style.opacity = '0.85'
                          }}
                          onMouseLeave={(e) => {
                            if (!connecting) e.currentTarget.style.opacity = '1'
                          }}
                        >
                          {connecting ? 'Connecting...' : 'Connect'}
                        </button>
                      )}
                    </div>
                  </div>
                )
              })
            )}
          </div>
        )}
      </section>

      {/* Publish Form Modal */}
      {publishForm && (
        <div
          style={{
            position: 'fixed',
            top: '0',
            left: 0,
            right: 0,
            bottom: '0',
            background: 'var(--ob-color-overlay-backdrop)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
          }}
          onClick={() => setPublishForm(null)}
        >
          <div
            style={{
              background: 'white',
              borderRadius: 'var(--ob-radius-sm)',
              padding: 'var(--ob-space-400)',
              maxWidth: '500px',
              width: '90%',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <h3
              style={{
                fontSize: '1.5rem',
                fontWeight: 600,
                margin: '0 0 1.5rem',
                letterSpacing: '-0.01em',
              }}
            >
              Publish to{' '}
              {providers.find((p) => p.provider === publishForm.provider)
                ?.label || publishForm.provider}
            </h3>

            <form onSubmit={handlePublish}>
              <div style={{ marginBottom: 'var(--ob-space-200)' }}>
                <label
                  style={{
                    display: 'block',
                    fontSize: '0.875rem',
                    fontWeight: 500,
                    color: 'var(--ob-color-bg-inverse)',
                    marginBottom: 'var(--ob-space-100)',
                    letterSpacing: '-0.005em',
                  }}
                >
                  Property ID
                </label>
                <input
                  type="text"
                  value={publishForm.propertyId}
                  onChange={(e) =>
                    setPublishForm({
                      ...publishForm,
                      propertyId: e.target.value,
                    })
                  }
                  placeholder="e.g. d47174ee-bb6f-4f3f-8baa-141d7c5d9051"
                  required
                  style={{
                    width: '100%',
                    padding: 'var(--ob-space-150) 1rem',
                    fontSize: '1rem',
                    border: '1px solid var(--ob-color-border-default)',
                    borderRadius: 'var(--ob-radius-sm)',
                    outline: 'none',
                    fontFamily:
                      'ui-monospace, SFMono-Regular, Menlo, Monaco, monospace',
                  }}
                />
              </div>

              <div style={{ marginBottom: 'var(--ob-space-200)' }}>
                <label
                  style={{
                    display: 'block',
                    fontSize: '0.875rem',
                    fontWeight: 500,
                    color: 'var(--ob-color-bg-inverse)',
                    marginBottom: 'var(--ob-space-100)',
                    letterSpacing: '-0.005em',
                  }}
                >
                  Listing Title
                </label>
                <input
                  type="text"
                  value={publishForm.title}
                  onChange={(e) =>
                    setPublishForm({ ...publishForm, title: e.target.value })
                  }
                  placeholder="e.g. Prime CBD Office Tower"
                  required
                  style={{
                    width: '100%',
                    padding: 'var(--ob-space-150) 1rem',
                    fontSize: '1rem',
                    border: '1px solid var(--ob-color-border-default)',
                    borderRadius: 'var(--ob-radius-sm)',
                    outline: 'none',
                  }}
                />
              </div>

              <div style={{ marginBottom: 'var(--ob-space-300)' }}>
                <label
                  style={{
                    display: 'block',
                    fontSize: '0.875rem',
                    fontWeight: 500,
                    color: 'var(--ob-color-bg-inverse)',
                    marginBottom: 'var(--ob-space-100)',
                    letterSpacing: '-0.005em',
                  }}
                >
                  Price (SGD)
                </label>
                <input
                  type="number"
                  value={publishForm.price}
                  onChange={(e) =>
                    setPublishForm({ ...publishForm, price: e.target.value })
                  }
                  placeholder="e.g. 5000000"
                  required
                  style={{
                    width: '100%',
                    padding: 'var(--ob-space-150) 1rem',
                    fontSize: '1rem',
                    border: '1px solid var(--ob-color-border-default)',
                    borderRadius: 'var(--ob-radius-sm)',
                    outline: 'none',
                  }}
                />
              </div>

              <div style={{ display: 'flex', gap: 'var(--ob-space-200)' }}>
                <button
                  type="button"
                  onClick={() => setPublishForm(null)}
                  style={{
                    flex: 1,
                    padding: 'var(--ob-space-150)',
                    fontSize: '1rem',
                    fontWeight: 500,
                    color: 'var(--ob-color-bg-inverse)',
                    background: 'transparent',
                    border: '1px solid var(--ob-color-border-default)',
                    borderRadius: 'var(--ob-radius-sm)',
                    cursor: 'pointer',
                  }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={publishingProvider === publishForm.provider}
                  style={{
                    flex: 1,
                    padding: 'var(--ob-space-150)',
                    fontSize: '1rem',
                    fontWeight: 500,
                    color: 'white',
                    background:
                      publishingProvider === publishForm.provider
                        ? '#d2d2d7'
                        : providers.find(
                            (p) => p.provider === publishForm.provider,
                          )?.brandColor || '#1d1d1f',
                    border: 'none',
                    borderRadius: 'var(--ob-radius-sm)',
                    cursor:
                      publishingProvider === publishForm.provider
                        ? 'not-allowed'
                        : 'pointer',
                  }}
                >
                  {publishingProvider === publishForm.provider
                    ? 'Publishing...'
                    : 'Publish Listing'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Info Section */}
      <section
        style={{
          background: 'white',
          border: '1px solid var(--ob-color-border-default)',
          borderRadius: 'var(--ob-radius-sm)',
          padding: 'var(--ob-space-400)',
        }}
      >
        <h2
          style={{
            fontSize: '1.75rem',
            fontWeight: 600,
            letterSpacing: '-0.01em',
            margin: '0 0 1.5rem',
          }}
        >
          About Integrations
        </h2>
        <p
          style={{
            fontSize: '0.9375rem',
            color: 'var(--ob-color-text-secondary)',
            lineHeight: 1.6,
            margin: '0 0 1rem',
            letterSpacing: '-0.005em',
          }}
        >
          Connect your property listing accounts to publish directly from the
          platform. Provider capabilities are loaded from your configured
          integrations.
        </p>
        {providers.length > 0 ? (
          <ul style={{ margin: 0, paddingLeft: 'var(--ob-space-200)' }}>
            {providers.map((provider) => (
              <li
                key={provider.provider}
                style={{
                  fontSize: '0.9375rem',
                  color: 'var(--ob-color-text-secondary)',
                  lineHeight: 1.6,
                  marginBottom: 'var(--ob-space-100)',
                  letterSpacing: '-0.005em',
                }}
              >
                <strong style={{ color: 'var(--ob-color-bg-inverse)' }}>
                  {provider.label ?? provider.provider}:
                </strong>{' '}
                {provider.description ?? 'Listing integration provider'}
              </li>
            ))}
          </ul>
        ) : (
          <p
            style={{
              fontSize: '0.9375rem',
              color: 'var(--ob-color-text-secondary)',
              lineHeight: 1.6,
              margin: 0,
              letterSpacing: '-0.005em',
            }}
          >
            No listing providers configured yet.
          </p>
        )}
      </section>
    </div>
  )
}
