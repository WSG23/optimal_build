import React from 'react'
import { Box, Typography, Button } from '@mui/material'

interface ErrorBoundaryProps {
  children: React.ReactNode
  fallback?: React.ReactNode
}

interface ErrorBoundaryState {
  hasError: boolean
  error: Error | null
}

export class ErrorBoundary extends React.Component<
  ErrorBoundaryProps,
  ErrorBoundaryState
> {
  constructor(props: ErrorBoundaryProps) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error }
  }

  private handleReload = () => {
    window.location.reload()
  }

  render() {
    if (!this.state.hasError) {
      return this.props.children
    }

    if (this.props.fallback) {
      return this.props.fallback
    }

    return (
      <Box
        role="alert"
        aria-live="assertive"
        sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '100vh',
          gap: 'var(--ob-space-150)',
          p: 'var(--ob-space-200)',
          textAlign: 'center',
        }}
      >
        <Typography
          variant="h4"
          sx={{ fontSize: 'var(--ob-font-size-xl)', fontWeight: 600 }}
        >
          Something went wrong
        </Typography>

        {this.state.error && (
          <Typography
            variant="body2"
            sx={{
              fontSize: 'var(--ob-font-size-sm)',
              color: 'text.secondary',
              maxWidth: '480px',
              wordBreak: 'break-word',
            }}
          >
            {this.state.error.message}
          </Typography>
        )}

        <Button
          variant="outlined"
          onClick={this.handleReload}
          sx={{
            borderRadius: 'var(--ob-radius-xs)',
            mt: 'var(--ob-space-100)',
          }}
        >
          Reload page
        </Button>
      </Box>
    )
  }
}
