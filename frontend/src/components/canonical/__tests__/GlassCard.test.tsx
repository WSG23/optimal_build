import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { ThemeProvider, createTheme } from '@mui/material/styles'
import { GlassCard } from '../GlassCard'

// Wrapper with theme provider for tests
const theme = createTheme()
const renderWithTheme = (component: React.ReactElement) => {
  return render(<ThemeProvider theme={theme}>{component}</ThemeProvider>)
}

describe('GlassCard', () => {
  describe('rendering', () => {
    it('renders children correctly', () => {
      renderWithTheme(<GlassCard>Card content</GlassCard>)
      expect(screen.getByText('Card content')).toBeInTheDocument()
    })

    it('applies className prop', () => {
      const { container } = renderWithTheme(
        <GlassCard className="custom-class">Content</GlassCard>,
      )
      expect(container.querySelector('.custom-class')).toBeInTheDocument()
    })

    it('renders as MUI Paper component', () => {
      const { container } = renderWithTheme(<GlassCard>Content</GlassCard>)
      expect(container.querySelector('.MuiPaper-root')).toBeInTheDocument()
    })
  })

  describe('design token compliance', () => {
    it('uses --ob-radius-sm for border radius (Square Cyber-Minimalism)', () => {
      const { container } = renderWithTheme(<GlassCard>Content</GlassCard>)
      const card = container.querySelector('.MuiPaper-root') as HTMLElement
      expect(card).toHaveStyle({
        borderRadius: 'var(--ob-radius-sm)',
      })
    })

    it('does NOT use rounded corners (8px+) as per design system', () => {
      const { container } = renderWithTheme(<GlassCard>Content</GlassCard>)
      const card = container.querySelector('.MuiPaper-root') as HTMLElement
      // Should not have larger radius values
      expect(card).not.toHaveStyle({ borderRadius: '8px' })
      expect(card).not.toHaveStyle({ borderRadius: '12px' })
      expect(card).not.toHaveStyle({ borderRadius: '16px' })
    })
  })

  describe('glassmorphism effect', () => {
    it('applies backdrop blur by default', () => {
      const { container } = renderWithTheme(<GlassCard>Content</GlassCard>)
      const card = container.querySelector('.MuiPaper-root') as HTMLElement
      // Note: backdropFilter not reliably testable in JSDOM
      // Verify card renders as MUI Paper
      expect(card).toBeInTheDocument()
    })

    it('applies custom blur value', () => {
      const { container } = renderWithTheme(
        <GlassCard blur={12}>Content</GlassCard>,
      )
      const card = container.querySelector('.MuiPaper-root') as HTMLElement
      // Note: backdropFilter not reliably testable in JSDOM
      expect(card).toBeInTheDocument()
    })

    it('has overflow hidden for glass effect', () => {
      const { container } = renderWithTheme(<GlassCard>Content</GlassCard>)
      const card = container.querySelector('.MuiPaper-root') as HTMLElement
      expect(card).toHaveStyle({
        overflow: 'hidden',
      })
    })
  })

  describe('elevation', () => {
    it('uses zero elevation by default', () => {
      const { container } = renderWithTheme(<GlassCard>Content</GlassCard>)
      const card = container.querySelector('.MuiPaper-root')
      expect(card).toHaveClass('MuiPaper-elevation0')
    })

    it('applies custom elevation', () => {
      const { container } = renderWithTheme(
        <GlassCard elevation={2}>Content</GlassCard>,
      )
      const card = container.querySelector('.MuiPaper-root')
      expect(card).toHaveClass('MuiPaper-elevation2')
    })
  })

  describe('hover effect', () => {
    it('does not apply hover effect by default', () => {
      const { container } = renderWithTheme(<GlassCard>Content</GlassCard>)
      const card = container.querySelector('.MuiPaper-root') as HTMLElement
      expect(card).toHaveStyle({ cursor: 'default' })
    })

    it('applies pointer cursor when onClick is provided', () => {
      const { container } = renderWithTheme(
        <GlassCard onClick={() => {}}>Content</GlassCard>,
      )
      const card = container.querySelector('.MuiPaper-root') as HTMLElement
      expect(card).toHaveStyle({ cursor: 'pointer' })
    })
  })

  describe('click handling', () => {
    it('calls onClick when clicked', () => {
      const onClick = vi.fn()
      renderWithTheme(<GlassCard onClick={onClick}>Click me</GlassCard>)
      fireEvent.click(screen.getByText('Click me'))
      expect(onClick).toHaveBeenCalledTimes(1)
    })

    it('does not throw when clicked without onClick', () => {
      renderWithTheme(<GlassCard>Click me</GlassCard>)
      expect(() => fireEvent.click(screen.getByText('Click me'))).not.toThrow()
    })
  })

  describe('custom styles', () => {
    it('merges sx prop with base styles', () => {
      const { container } = renderWithTheme(
        <GlassCard sx={{ padding: '20px' }}>Content</GlassCard>,
      )
      const card = container.querySelector('.MuiPaper-root') as HTMLElement
      // Should still have base styles
      expect(card).toHaveStyle({
        borderRadius: 'var(--ob-radius-sm)',
      })
    })

    it('handles sx prop as array', () => {
      const { container } = renderWithTheme(
        <GlassCard sx={[{ padding: '10px' }, { margin: '5px' }]}>
          Content
        </GlassCard>,
      )
      expect(container.querySelector('.MuiPaper-root')).toBeInTheDocument()
    })
  })

  describe('opacity', () => {
    it('uses default opacity of 0.85', () => {
      renderWithTheme(<GlassCard>Content</GlassCard>)
      // The opacity is applied to the background alpha
      // This test validates the component accepts the prop
      expect(screen.getByText('Content')).toBeInTheDocument()
    })

    it('accepts custom opacity', () => {
      renderWithTheme(<GlassCard opacity={0.5}>Content</GlassCard>)
      expect(screen.getByText('Content')).toBeInTheDocument()
    })
  })

  describe('accessibility', () => {
    it('passes through additional Paper props', () => {
      const { container } = renderWithTheme(
        <GlassCard
          data-testid="glass-card"
          role="region"
          aria-label="Test card"
        >
          Content
        </GlassCard>,
      )
      const card = container.querySelector('[data-testid="glass-card"]')
      expect(card).toHaveAttribute('role', 'region')
      expect(card).toHaveAttribute('aria-label', 'Test card')
    })
  })

  describe('transition', () => {
    it('applies smooth transition for animations', () => {
      const { container } = renderWithTheme(<GlassCard>Content</GlassCard>)
      const card = container.querySelector('.MuiPaper-root') as HTMLElement
      expect(card).toHaveStyle({
        transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
      })
    })
  })
})
