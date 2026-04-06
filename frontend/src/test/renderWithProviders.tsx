/**
 * Test utility for rendering components with all necessary providers.
 *
 * Usage:
 *   import { renderWithProviders } from '../../test/renderWithProviders'
 *
 *   it('renders component', () => {
 *     const { getByText } = renderWithProviders(<MyComponent />)
 *     expect(getByText('Hello')).toBeInTheDocument()
 *   })
 *
 * Options:
 *   - inBaseLayout: true (default) - Skips HeaderUtilityCluster rendering
 *   - inBaseLayout: false - Full app shell with header cluster
 */
import type { ReactElement, ReactNode } from 'react'
import { render, RenderOptions, RenderResult } from '@testing-library/react'
import { ThemeModeProvider } from '../theme/ThemeContext'
import { TranslationProvider } from '../i18n'
import { BaseLayoutProvider } from '../app/layout/BaseLayoutContext'

export interface ProviderOptions {
  /**
   * When true (default), sets BaseLayout context to skip HeaderUtilityCluster.
   * Set to false if you need to test the full header stack.
   */
  inBaseLayout?: boolean
  /**
   * Top offset for BaseLayout context (default: 0)
   */
  topOffset?: number | string
}

/**
 * Custom render function that wraps components with all necessary providers.
 *
 * @param ui - The React element to render
 * @param options - Provider and render options
 * @returns RTL render result with all queries
 *
 * @example
 * // Basic usage - skips header cluster by default
 * const { getByText } = renderWithProviders(<MyPage />)
 *
 * @example
 * // Full app shell with header
 * const { getByText } = renderWithProviders(<MyPage />, {
 *   providerOptions: { inBaseLayout: false }
 * })
 */
export function renderWithProviders(
  ui: ReactElement,
  {
    providerOptions,
    ...renderOptions
  }: RenderOptions & { providerOptions?: ProviderOptions } = {},
): RenderResult {
  const { inBaseLayout = true, topOffset = 0 } = providerOptions ?? {}

  function Wrapper({ children }: { children: ReactNode }) {
    return (
      <ThemeModeProvider>
        <TranslationProvider>
          <BaseLayoutProvider value={{ inBaseLayout, topOffset }}>
            {children}
          </BaseLayoutProvider>
        </TranslationProvider>
      </ThemeModeProvider>
    )
  }

  return render(ui, { wrapper: Wrapper, ...renderOptions })
}
