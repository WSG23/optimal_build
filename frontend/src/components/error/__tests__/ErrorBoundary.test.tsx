import { render, screen, fireEvent } from '@testing-library/react'
import { ErrorBoundary } from '../ErrorBoundary'
import type { ErrorDetails } from '../ErrorBoundary'

// Component that throws an error
function ThrowError({ shouldThrow }: { shouldThrow: boolean }) {
  if (shouldThrow) {
    throw new Error('Test error message')
  }
  return <div>No error</div>
}

// Suppress console.error for expected errors in tests
const originalError = console.error
beforeAll(() => {
  console.error = (...args: unknown[]) => {
    if (
      typeof args[0] === 'string' &&
      args[0].includes('The above error occurred')
    ) {
      return
    }
    originalError.call(console, ...args)
  }
})

afterAll(() => {
  console.error = originalError
})

describe('ErrorBoundary', () => {
  beforeEach(() => {
    // Reset any mocks
    jest.clearAllMocks()
  })

  describe('when no error occurs', () => {
    it('renders children normally', () => {
      render(
        <ErrorBoundary>
          <div>Child content</div>
        </ErrorBoundary>,
      )

      expect(screen.getByText('Child content')).toBeInTheDocument()
    })

    it('does not show error UI', () => {
      render(
        <ErrorBoundary>
          <div>Child content</div>
        </ErrorBoundary>,
      )

      expect(screen.queryByText('Something went wrong')).not.toBeInTheDocument()
    })
  })

  describe('when an error occurs', () => {
    it('renders fallback UI', () => {
      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>,
      )

      expect(screen.getByText('Something went wrong')).toBeInTheDocument()
    })

    it('shows default error message', () => {
      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>,
      )

      expect(
        screen.getByText(/We apologize for the inconvenience/),
      ).toBeInTheDocument()
    })

    it('shows Try Again button', () => {
      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>,
      )

      expect(
        screen.getByRole('button', { name: /Try Again/i }),
      ).toBeInTheDocument()
    })

    it('shows Go Home button', () => {
      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>,
      )

      expect(
        screen.getByRole('button', { name: /Go Home/i }),
      ).toBeInTheDocument()
    })
  })

  describe('custom props', () => {
    it('uses custom title', () => {
      render(
        <ErrorBoundary title="Custom Error Title">
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>,
      )

      expect(screen.getByText('Custom Error Title')).toBeInTheDocument()
    })

    it('uses custom message', () => {
      render(
        <ErrorBoundary message="Custom error message here">
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>,
      )

      expect(screen.getByText('Custom error message here')).toBeInTheDocument()
    })

    it('renders custom fallback component', () => {
      render(
        <ErrorBoundary fallback={<div>Custom Fallback</div>}>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>,
      )

      expect(screen.getByText('Custom Fallback')).toBeInTheDocument()
    })

    it('renders custom fallback function with error and reset', () => {
      const customFallback = (error: Error, reset: () => void) => (
        <div>
          <span>Error: {error.message}</span>
          <button onClick={reset}>Custom Reset</button>
        </div>
      )

      render(
        <ErrorBoundary fallback={customFallback}>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>,
      )

      expect(screen.getByText('Error: Test error message')).toBeInTheDocument()
      expect(
        screen.getByRole('button', { name: /Custom Reset/i }),
      ).toBeInTheDocument()
    })
  })

  describe('error callback', () => {
    it('calls onError when an error is caught', () => {
      const onError = jest.fn()

      render(
        <ErrorBoundary onError={onError}>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>,
      )

      expect(onError).toHaveBeenCalledTimes(1)
      expect(onError).toHaveBeenCalledWith(
        expect.any(Error),
        expect.objectContaining({
          componentStack: expect.any(String),
        }),
        expect.objectContaining({
          message: 'Test error message',
          timestamp: expect.any(String),
          url: expect.any(String),
        }),
      )
    })

    it('provides error details with correct structure', () => {
      let capturedDetails: ErrorDetails | null = null

      const onError = (
        _error: Error,
        _errorInfo: React.ErrorInfo,
        details: ErrorDetails,
      ) => {
        capturedDetails = details
      }

      render(
        <ErrorBoundary onError={onError}>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>,
      )

      expect(capturedDetails).not.toBeNull()
      expect(capturedDetails!.message).toBe('Test error message')
      expect(capturedDetails!.timestamp).toMatch(/^\d{4}-\d{2}-\d{2}T/)
      expect(typeof capturedDetails!.url).toBe('string')
      expect(typeof capturedDetails!.userAgent).toBe('string')
    })
  })

  describe('reset functionality', () => {
    it('resets error state when Try Again is clicked', () => {
      let shouldThrow = true

      const TestComponent = () => {
        if (shouldThrow) {
          throw new Error('Test error')
        }
        return <div>Success!</div>
      }

      const { rerender } = render(
        <ErrorBoundary>
          <TestComponent />
        </ErrorBoundary>,
      )

      // Error should be shown
      expect(screen.getByText('Something went wrong')).toBeInTheDocument()

      // Fix the error condition
      shouldThrow = false

      // Click Try Again
      fireEvent.click(screen.getByRole('button', { name: /Try Again/i }))

      // Should re-render children
      rerender(
        <ErrorBoundary>
          <TestComponent />
        </ErrorBoundary>,
      )

      expect(screen.getByText('Success!')).toBeInTheDocument()
    })
  })

  describe('error details display', () => {
    it('shows error details in development mode', () => {
      const originalEnv = process.env.NODE_ENV
      Object.defineProperty(process.env, 'NODE_ENV', {
        value: 'development',
        writable: true,
      })

      render(
        <ErrorBoundary showDetails={true}>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>,
      )

      expect(screen.getByText(/Error Details/)).toBeInTheDocument()
      expect(screen.getByText('Test error message')).toBeInTheDocument()

      Object.defineProperty(process.env, 'NODE_ENV', {
        value: originalEnv,
        writable: true,
      })
    })

    it('hides error details when showDetails is false', () => {
      render(
        <ErrorBoundary showDetails={false}>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>,
      )

      expect(screen.queryByText(/Error Details/)).not.toBeInTheDocument()
    })
  })
})
