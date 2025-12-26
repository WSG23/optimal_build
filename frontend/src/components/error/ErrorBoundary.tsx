import { Component, ErrorInfo, ReactNode } from 'react'
import { Box, Typography } from '@mui/material'
import { Refresh, BugReport, Home } from '@mui/icons-material'
import { Button } from '../canonical/Button'

/**
 * Error details structure for logging and display
 */
export interface ErrorDetails {
  message: string
  stack?: string
  componentStack?: string
  timestamp: string
  url: string
  userAgent: string
}

/**
 * Props for the ErrorBoundary component
 */
export interface ErrorBoundaryProps {
  /**
   * Child components to render
   */
  children: ReactNode
  /**
   * Custom fallback UI component
   */
  fallback?: ReactNode | ((error: Error, reset: () => void) => ReactNode)
  /**
   * Callback when an error is caught
   */
  onError?: (error: Error, errorInfo: ErrorInfo, details: ErrorDetails) => void
  /**
   * Show detailed error info (dev mode)
   */
  showDetails?: boolean
  /**
   * Custom error title
   */
  title?: string
  /**
   * Custom error message
   */
  message?: string
}

/**
 * State for the ErrorBoundary component
 */
interface ErrorBoundaryState {
  hasError: boolean
  error: Error | null
  errorInfo: ErrorInfo | null
  errorDetails: ErrorDetails | null
}

/**
 * ErrorBoundary - Global Error Handling Component
 *
 * Catches JavaScript errors anywhere in the child component tree,
 * logs error information, and displays a fallback UI.
 *
 * Features:
 * - Catches all unhandled errors in React component tree
 * - Provides error details for debugging
 * - Offers recovery options (retry, go home)
 * - Supports custom fallback UI
 * - Logs errors for monitoring (can integrate with Sentry, etc.)
 *
 * Usage:
 *   <ErrorBoundary onError={logToSentry}>
 *     <App />
 *   </ErrorBoundary>
 *
 *   // With custom fallback
 *   <ErrorBoundary fallback={<CustomErrorPage />}>
 *     <App />
 *   </ErrorBoundary>
 *
 *   // With render prop fallback
 *   <ErrorBoundary fallback={(error, reset) => (
 *     <div>
 *       <p>Error: {error.message}</p>
 *       <button onClick={reset}>Try Again</button>
 *     </div>
 *   )}>
 *     <App />
 *   </ErrorBoundary>
 */
export class ErrorBoundary extends Component<
  ErrorBoundaryProps,
  ErrorBoundaryState
> {
  constructor(props: ErrorBoundaryProps) {
    super(props)
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      errorDetails: null,
    }
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    // Update state so next render shows fallback UI
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    // Build error details for logging
    const errorDetails: ErrorDetails = {
      message: error.message,
      stack: error.stack,
      componentStack: errorInfo.componentStack || undefined,
      timestamp: new Date().toISOString(),
      url: typeof window !== 'undefined' ? window.location.href : '',
      userAgent: typeof navigator !== 'undefined' ? navigator.userAgent : '',
    }

    this.setState({
      errorInfo,
      errorDetails,
    })

    // Log to console in development
    if (process.env.NODE_ENV === 'development') {
      console.group('ErrorBoundary caught an error')
      console.error('Error:', error)
      console.error('Error Info:', errorInfo)
      console.error('Details:', errorDetails)
      console.groupEnd()
    }

    // Call custom error handler if provided
    this.props.onError?.(error, errorInfo, errorDetails)
  }

  /**
   * Reset the error boundary state to try rendering again
   */
  handleReset = (): void => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
      errorDetails: null,
    })
  }

  /**
   * Navigate to home page
   */
  handleGoHome = (): void => {
    if (typeof window !== 'undefined') {
      window.location.href = '/'
    }
  }

  /**
   * Copy error details to clipboard for bug reports
   */
  handleCopyError = async (): Promise<void> => {
    const { error, errorDetails } = this.state
    if (!error || !errorDetails) return

    const errorReport = `
Error Report
============
Timestamp: ${errorDetails.timestamp}
URL: ${errorDetails.url}
Message: ${errorDetails.message}

Stack Trace:
${errorDetails.stack || 'Not available'}

Component Stack:
${errorDetails.componentStack || 'Not available'}

User Agent:
${errorDetails.userAgent}
`.trim()

    try {
      await navigator.clipboard.writeText(errorReport)
      // Could show a toast notification here
    } catch {
      // Fallback for browsers that don't support clipboard API
      console.log('Error report:', errorReport)
    }
  }

  render(): ReactNode {
    const { hasError, error, errorDetails } = this.state
    const {
      children,
      fallback,
      showDetails = process.env.NODE_ENV === 'development',
      title = 'Something went wrong',
      message = 'We apologize for the inconvenience. Please try refreshing the page or return to the home page.',
    } = this.props

    if (!hasError) {
      return children
    }

    // Custom fallback as render prop
    if (typeof fallback === 'function' && error) {
      return fallback(error, this.handleReset)
    }

    // Custom fallback component
    if (fallback) {
      return fallback
    }

    // Default fallback UI
    return (
      <Box
        sx={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: 'var(--ob-color-bg-primary)',
          padding: 'var(--ob-space-200)',
        }}
      >
        <Box
          sx={{
            maxWidth: '600px',
            width: '100%',
            textAlign: 'center',
          }}
        >
          {/* Error Icon */}
          <Box
            sx={{
              width: '80px',
              height: '80px',
              borderRadius: 'var(--ob-radius-lg)',
              background: 'var(--ob-color-error-soft)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto var(--ob-space-200)',
            }}
          >
            <BugReport
              sx={{
                fontSize: 40,
                color: 'var(--ob-color-status-error-text)',
              }}
            />
          </Box>

          {/* Error Title */}
          <Typography
            variant="h4"
            sx={{
              color: 'var(--ob-color-text-primary)',
              fontWeight: 'var(--ob-font-weight-bold)',
              marginBottom: 'var(--ob-space-100)',
            }}
          >
            {title}
          </Typography>

          {/* Error Message */}
          <Typography
            sx={{
              color: 'var(--ob-color-text-secondary)',
              fontSize: 'var(--ob-font-size-md)',
              marginBottom: 'var(--ob-space-200)',
              lineHeight: 1.6,
            }}
          >
            {message}
          </Typography>

          {/* Action Buttons */}
          <Box
            sx={{
              display: 'flex',
              gap: 'var(--ob-space-100)',
              justifyContent: 'center',
              flexWrap: 'wrap',
              marginBottom: 'var(--ob-space-200)',
            }}
          >
            <Button
              variant="primary"
              onClick={this.handleReset}
              startIcon={<Refresh />}
            >
              Try Again
            </Button>
            <Button
              variant="secondary"
              onClick={this.handleGoHome}
              startIcon={<Home />}
            >
              Go Home
            </Button>
          </Box>

          {/* Error Details (Development Mode) */}
          {showDetails && error && errorDetails && (
            <Box
              sx={{
                mt: 'var(--ob-space-200)',
                p: 'var(--ob-space-150)',
                background: 'var(--ob-surface-glass-1)',
                borderRadius: 'var(--ob-radius-sm)',
                border: 'var(--ob-border-fine-subtle)',
                textAlign: 'left',
              }}
            >
              <Box
                sx={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  mb: 'var(--ob-space-100)',
                }}
              >
                <Typography
                  sx={{
                    color: 'var(--ob-color-text-secondary)',
                    fontSize: 'var(--ob-font-size-xs)',
                    fontWeight: 'var(--ob-font-weight-semibold)',
                    textTransform: 'uppercase',
                    letterSpacing: '0.05em',
                  }}
                >
                  Error Details (Development Only)
                </Typography>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={this.handleCopyError}
                >
                  Copy
                </Button>
              </Box>

              {/* Error Message */}
              <Box sx={{ mb: 'var(--ob-space-100)' }}>
                <Typography
                  sx={{
                    color: 'var(--ob-color-status-error-text)',
                    fontSize: 'var(--ob-font-size-sm)',
                    fontFamily: 'monospace',
                    wordBreak: 'break-word',
                  }}
                >
                  {error.message}
                </Typography>
              </Box>

              {/* Stack Trace */}
              {errorDetails.stack && (
                <Box
                  sx={{
                    maxHeight: '200px',
                    overflow: 'auto',
                    p: 'var(--ob-space-100)',
                    background: 'var(--ob-color-bg-secondary)',
                    borderRadius: 'var(--ob-radius-xs)',
                  }}
                >
                  <Typography
                    component="pre"
                    sx={{
                      color: 'var(--ob-color-text-muted)',
                      fontSize: 'var(--ob-font-size-xs)',
                      fontFamily: 'monospace',
                      whiteSpace: 'pre-wrap',
                      wordBreak: 'break-word',
                      margin: 0,
                    }}
                  >
                    {errorDetails.stack}
                  </Typography>
                </Box>
              )}

              {/* Timestamp */}
              <Typography
                sx={{
                  color: 'var(--ob-color-text-muted)',
                  fontSize: 'var(--ob-font-size-xs)',
                  mt: 'var(--ob-space-100)',
                }}
              >
                Occurred at: {errorDetails.timestamp}
              </Typography>
            </Box>
          )}
        </Box>
      </Box>
    )
  }
}

export default ErrorBoundary
