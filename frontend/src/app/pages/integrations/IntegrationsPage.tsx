import { useEffect, useState } from 'react'
import type { ListingIntegrationAccount } from '../../../api/listings'
import {
  connectMockAccount,
  disconnectMockAccount,
  fetchListingAccounts,
  publishMockListing,
} from '../../../api/listings'

const PROVIDERS = [
  {
    id: 'propertyguru',
    name: 'PropertyGuru',
    description: "Singapore's leading property portal",
    color: '#00aaff',
  },
  {
    id: 'edgeprop',
    name: 'EdgeProp',
    description: 'The Edge Singapore property platform',
    color: '#ff6b35',
  },
  {
    id: 'zoho_crm',
    name: 'Zoho CRM',
    description: 'CRM and lead management',
    color: '#e42527',
  },
]

export function IntegrationsPage() {
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
      const data = await fetchListingAccounts()
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
      // Mock OAuth: generate a fake auth code
      const mockCode = `mock_${provider}_${Date.now()}`
      const newAccount = await connectMockAccount(provider, mockCode)
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
      await disconnectMockAccount(provider)
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
      const result = await publishMockListing(publishForm.provider, {
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
      (a) => a.provider === providerId && a.status === 'active',
    )
  }

  return (
    <div
      style={{
        padding: '3rem 2rem',
        maxWidth: '1200px',
        margin: '0 auto',
        fontFamily:
          '-apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", system-ui, sans-serif',
        color: '#1d1d1f',
      }}
    >
      {/* Header */}
      <header style={{ marginBottom: '3rem' }}>
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
            color: '#6e6e73',
            fontWeight: 400,
            margin: 0,
            letterSpacing: '-0.01em',
          }}
        >
          Connect and manage property listing portals
        </p>
      </header>

      {/* Integration Cards */}
      <section style={{ marginBottom: '3rem' }}>
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
              padding: '3rem',
              textAlign: 'center',
              background: 'white',
              border: '1px solid #d2d2d7',
              borderRadius: '18px',
              color: '#6e6e73',
            }}
          >
            Loading integrations...
          </div>
        ) : error ? (
          <div
            style={{
              padding: '3rem 2rem',
              textAlign: 'center',
              background: 'white',
              border: '1px solid #d2d2d7',
              borderRadius: '18px',
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
                color: '#1d1d1f',
                marginBottom: '0.5rem',
                letterSpacing: '-0.01em',
              }}
            >
              {error}
            </p>
            <p
              style={{
                fontSize: '0.9375rem',
                color: '#6e6e73',
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
              gap: '1.5rem',
            }}
          >
            {PROVIDERS.map((provider) => {
              const account = getAccountForProvider(provider.id)
              const connected = isConnected(provider.id)
              const connecting = connectingProvider === provider.id

              return (
                <div
                  key={provider.id}
                  style={{
                    background: 'white',
                    border: `2px solid ${connected ? provider.color : '#d2d2d7'}`,
                    borderRadius: '18px',
                    padding: '2rem',
                    transition: 'all 0.2s ease',
                  }}
                >
                  <div
                    style={{
                      width: '48px',
                      height: '48px',
                      borderRadius: '12px',
                      background: provider.color,
                      marginBottom: '1rem',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: 'white',
                      fontSize: '1.5rem',
                      fontWeight: 700,
                    }}
                  >
                    {provider.name[0]}
                  </div>

                  <h3
                    style={{
                      fontSize: '1.25rem',
                      fontWeight: 600,
                      margin: '0 0 0.5rem',
                      letterSpacing: '-0.01em',
                    }}
                  >
                    {provider.name}
                  </h3>

                  <p
                    style={{
                      fontSize: '0.9375rem',
                      color: '#6e6e73',
                      margin: '0 0 1.5rem',
                      letterSpacing: '-0.005em',
                    }}
                  >
                    {provider.description}
                  </p>

                  {connected && account && (
                    <div
                      style={{
                        padding: '0.75rem 1rem',
                        background: '#f5f5f7',
                        borderRadius: '10px',
                        marginBottom: '1rem',
                        fontSize: '0.875rem',
                        color: '#6e6e73',
                      }}
                    >
                      <div style={{ marginBottom: '0.25rem' }}>
                        <strong style={{ color: '#1d1d1f' }}>Status:</strong>{' '}
                        {account.status}
                      </div>
                      <div style={{ fontSize: '0.8125rem' }}>
                        Connected{' '}
                        {new Date(account.created_at).toLocaleDateString()}
                      </div>
                    </div>
                  )}

                  <div style={{ display: 'flex', gap: '0.75rem' }}>
                    {connected ? (
                      <>
                        <button
                          type="button"
                          onClick={() =>
                            setPublishForm({
                              provider: provider.id,
                              propertyId: '',
                              title: '',
                              price: '',
                            })
                          }
                          style={{
                            flex: 1,
                            padding: '0.75rem 1.25rem',
                            fontSize: '0.9375rem',
                            fontWeight: 500,
                            color: 'white',
                            background: provider.color,
                            border: 'none',
                            borderRadius: '10px',
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
                          onClick={() => handleDisconnect(provider.id)}
                          style={{
                            padding: '0.75rem 1.25rem',
                            fontSize: '0.9375rem',
                            fontWeight: 500,
                            color: '#1d1d1f',
                            background: 'transparent',
                            border: '1px solid #d2d2d7',
                            borderRadius: '10px',
                            cursor: 'pointer',
                            transition: 'all 0.2s ease',
                            letterSpacing: '-0.005em',
                          }}
                          onMouseEnter={(e) => {
                            e.currentTarget.style.background = '#f5f5f7'
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
                        onClick={() => handleConnect(provider.id)}
                        disabled={connecting}
                        style={{
                          flex: 1,
                          padding: '0.75rem 1.25rem',
                          fontSize: '0.9375rem',
                          fontWeight: 500,
                          color: connecting ? '#6e6e73' : 'white',
                          background: connecting ? '#f5f5f7' : provider.color,
                          border: 'none',
                          borderRadius: '10px',
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
            })}
          </div>
        )}
      </section>

      {/* Publish Form Modal */}
      {publishForm && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(0, 0, 0, 0.5)',
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
              borderRadius: '18px',
              padding: '2rem',
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
              {PROVIDERS.find((p) => p.id === publishForm.provider)?.name}
            </h3>

            <form onSubmit={handlePublish}>
              <div style={{ marginBottom: '1rem' }}>
                <label
                  style={{
                    display: 'block',
                    fontSize: '0.875rem',
                    fontWeight: 500,
                    color: '#1d1d1f',
                    marginBottom: '0.5rem',
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
                    padding: '0.75rem 1rem',
                    fontSize: '1rem',
                    border: '1px solid #d2d2d7',
                    borderRadius: '12px',
                    outline: 'none',
                    fontFamily:
                      'ui-monospace, SFMono-Regular, Menlo, Monaco, monospace',
                  }}
                />
              </div>

              <div style={{ marginBottom: '1rem' }}>
                <label
                  style={{
                    display: 'block',
                    fontSize: '0.875rem',
                    fontWeight: 500,
                    color: '#1d1d1f',
                    marginBottom: '0.5rem',
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
                    padding: '0.75rem 1rem',
                    fontSize: '1rem',
                    border: '1px solid #d2d2d7',
                    borderRadius: '12px',
                    outline: 'none',
                  }}
                />
              </div>

              <div style={{ marginBottom: '1.5rem' }}>
                <label
                  style={{
                    display: 'block',
                    fontSize: '0.875rem',
                    fontWeight: 500,
                    color: '#1d1d1f',
                    marginBottom: '0.5rem',
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
                    padding: '0.75rem 1rem',
                    fontSize: '1rem',
                    border: '1px solid #d2d2d7',
                    borderRadius: '12px',
                    outline: 'none',
                  }}
                />
              </div>

              <div style={{ display: 'flex', gap: '1rem' }}>
                <button
                  type="button"
                  onClick={() => setPublishForm(null)}
                  style={{
                    flex: 1,
                    padding: '0.875rem',
                    fontSize: '1rem',
                    fontWeight: 500,
                    color: '#1d1d1f',
                    background: 'transparent',
                    border: '1px solid #d2d2d7',
                    borderRadius: '12px',
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
                    padding: '0.875rem',
                    fontSize: '1rem',
                    fontWeight: 500,
                    color: 'white',
                    background:
                      publishingProvider === publishForm.provider
                        ? '#d2d2d7'
                        : PROVIDERS.find((p) => p.id === publishForm.provider)
                            ?.color || '#1d1d1f',
                    border: 'none',
                    borderRadius: '12px',
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
          border: '1px solid #d2d2d7',
          borderRadius: '18px',
          padding: '2rem',
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
            color: '#6e6e73',
            lineHeight: 1.6,
            margin: '0 0 1rem',
            letterSpacing: '-0.005em',
          }}
        >
          Connect your property listing accounts to publish directly from the
          platform. Mock OAuth flow simulates real provider authentication for
          development purposes.
        </p>
        <ul style={{ margin: 0, paddingLeft: '1.25rem' }}>
          <li
            style={{
              fontSize: '0.9375rem',
              color: '#6e6e73',
              lineHeight: 1.6,
              marginBottom: '0.5rem',
              letterSpacing: '-0.005em',
            }}
          >
            <strong style={{ color: '#1d1d1f' }}>PropertyGuru:</strong>{' '}
            Singapore's largest property portal with wide reach
          </li>
          <li
            style={{
              fontSize: '0.9375rem',
              color: '#6e6e73',
              lineHeight: 1.6,
              marginBottom: '0.5rem',
              letterSpacing: '-0.005em',
            }}
          >
            <strong style={{ color: '#1d1d1f' }}>EdgeProp:</strong> Premium
            property insights and listings
          </li>
          <li
            style={{
              fontSize: '0.9375rem',
              color: '#6e6e73',
              lineHeight: 1.6,
              letterSpacing: '-0.005em',
            }}
          >
            <strong style={{ color: '#1d1d1f' }}>Zoho CRM:</strong> Lead
            management and client tracking
          </li>
        </ul>
      </section>
    </div>
  )
}
