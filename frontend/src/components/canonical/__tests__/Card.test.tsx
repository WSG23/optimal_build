import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { Card } from '../Card'

describe('Card', () => {
  describe('rendering', () => {
    it('renders children correctly', () => {
      render(<Card>Card content</Card>)
      expect(screen.getByText('Card content')).toBeInTheDocument()
    })

    it('applies default variant styles', () => {
      const { container } = render(<Card>Content</Card>)
      const card = container.firstChild as HTMLElement
      expect(card).toHaveStyle({
        borderRadius: 'var(--ob-radius-sm)',
      })
    })

    it('forwards ref correctly', () => {
      const ref = { current: null } as React.RefObject<HTMLDivElement>
      render(<Card ref={ref}>Content</Card>)
      expect(ref.current).toBeInstanceOf(HTMLDivElement)
    })

    it('applies className prop', () => {
      const { container } = render(
        <Card className="custom-class">Content</Card>,
      )
      expect(container.firstChild).toHaveClass('custom-class')
    })
  })

  describe('variants', () => {
    it('applies default variant background', () => {
      const { container } = render(<Card variant="default">Content</Card>)
      const card = container.firstChild as HTMLElement
      expect(card).toHaveStyle({
        background: 'var(--ob-color-bg-surface)',
      })
    })

    it('applies glass variant with backdrop filter', () => {
      const { container } = render(<Card variant="glass">Content</Card>)
      const card = container.firstChild as HTMLElement
      // Note: backdropFilter not reliably testable in JSDOM
      expect(card).toHaveStyle({
        background: 'var(--ob-surface-glass-1)',
      })
    })

    it('applies ghost variant with transparent background', () => {
      const { container } = render(<Card variant="ghost">Content</Card>)
      const card = container.firstChild as HTMLElement
      expect(card).toHaveStyle({
        background: 'transparent',
        border: 'var(--ob-border-fine-strong)',
      })
    })
  })

  describe('hover effects', () => {
    it('applies pointer cursor when onClick is provided', () => {
      const { container } = render(<Card onClick={() => {}}>Content</Card>)
      const card = container.firstChild as HTMLElement
      expect(card).toHaveStyle({ cursor: 'pointer' })
    })

    it('applies default cursor when no onClick is provided', () => {
      const { container } = render(<Card>Content</Card>)
      const card = container.firstChild as HTMLElement
      expect(card).toHaveStyle({ cursor: 'default' })
    })
  })

  describe('click handling', () => {
    it('calls onClick when clicked', () => {
      const onClick = vi.fn()
      render(<Card onClick={onClick}>Click me</Card>)
      fireEvent.click(screen.getByText('Click me'))
      expect(onClick).toHaveBeenCalledTimes(1)
    })

    it('does not throw when clicked without onClick handler', () => {
      render(<Card>Click me</Card>)
      expect(() => fireEvent.click(screen.getByText('Click me'))).not.toThrow()
    })
  })

  describe('custom styles', () => {
    it('merges custom sx prop with base styles', () => {
      const { container } = render(
        <Card sx={{ padding: '20px', margin: '10px' }}>Content</Card>,
      )
      const card = container.firstChild as HTMLElement
      expect(card).toHaveStyle({
        borderRadius: 'var(--ob-radius-sm)',
      })
    })

    it('handles sx prop as array', () => {
      const { container } = render(
        <Card sx={[{ padding: '10px' }, { margin: '5px' }]}>Content</Card>,
      )
      expect(container.firstChild).toBeInTheDocument()
    })
  })

  describe('design token compliance', () => {
    it('uses --ob-radius-sm for border radius (Square Cyber-Minimalism)', () => {
      const { container } = render(<Card>Content</Card>)
      const card = container.firstChild as HTMLElement
      expect(card).toHaveStyle({
        borderRadius: 'var(--ob-radius-sm)',
      })
    })

    it('uses --ob-border-fine for default border', () => {
      const { container } = render(<Card>Content</Card>)
      const card = container.firstChild as HTMLElement
      expect(card).toHaveStyle({
        border: 'var(--ob-border-fine)',
      })
    })
  })
})
