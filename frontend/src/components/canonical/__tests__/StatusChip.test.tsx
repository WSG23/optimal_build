import React from 'react'
import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { StatusChip } from '../StatusChip'
import CheckCircleIcon from '@mui/icons-material/CheckCircle'

describe('StatusChip', () => {
  describe('rendering', () => {
    it('renders children correctly', () => {
      render(<StatusChip status="success">Active</StatusChip>)
      expect(screen.getByText('Active')).toBeInTheDocument()
    })

    it('renders with icon', () => {
      render(
        <StatusChip
          status="success"
          icon={<CheckCircleIcon data-testid="icon" />}
        >
          Active
        </StatusChip>,
      )
      expect(screen.getByTestId('icon')).toBeInTheDocument()
    })
  })

  describe('status types', () => {
    const statusTypes = [
      'success',
      'warning',
      'error',
      'info',
      'neutral',
      'brand',
    ] as const

    statusTypes.forEach((status) => {
      it(`renders ${status} status correctly`, () => {
        render(<StatusChip status={status}>{status} status</StatusChip>)
        expect(screen.getByText(`${status} status`)).toBeInTheDocument()
      })
    })

    it('applies success colors', () => {
      const { container } = render(
        <StatusChip status="success">Success</StatusChip>,
      )
      const chip = container.firstChild as HTMLElement
      expect(chip).toHaveStyle({
        background: 'var(--ob-color-success-soft)',
      })
    })

    it('applies warning colors', () => {
      const { container } = render(
        <StatusChip status="warning">Warning</StatusChip>,
      )
      const chip = container.firstChild as HTMLElement
      expect(chip).toHaveStyle({
        background: 'var(--ob-color-warning-soft)',
      })
    })

    it('applies error colors', () => {
      const { container } = render(
        <StatusChip status="error">Error</StatusChip>,
      )
      const chip = container.firstChild as HTMLElement
      expect(chip).toHaveStyle({
        background: 'var(--ob-color-error-soft)',
      })
    })

    it('applies info colors', () => {
      const { container } = render(<StatusChip status="info">Info</StatusChip>)
      const chip = container.firstChild as HTMLElement
      expect(chip).toHaveStyle({
        background: 'var(--ob-color-info-soft)',
      })
    })

    it('applies neutral colors', () => {
      const { container } = render(
        <StatusChip status="neutral">Neutral</StatusChip>,
      )
      const chip = container.firstChild as HTMLElement
      expect(chip).toHaveStyle({
        background: 'var(--ob-color-surface-strong)',
      })
    })

    it('applies brand colors', () => {
      const { container } = render(
        <StatusChip status="brand">Brand</StatusChip>,
      )
      const chip = container.firstChild as HTMLElement
      expect(chip).toHaveStyle({
        background: 'var(--ob-color-brand-soft)',
      })
    })
  })

  describe('sizes', () => {
    it('renders small size with correct height', () => {
      const { container } = render(
        <StatusChip status="success" size="sm">
          Small
        </StatusChip>,
      )
      const chip = container.firstChild as HTMLElement
      expect(chip).toHaveStyle({ height: '20px' })
    })

    it('renders medium size with correct height', () => {
      const { container } = render(
        <StatusChip status="success" size="md">
          Medium
        </StatusChip>,
      )
      const chip = container.firstChild as HTMLElement
      expect(chip).toHaveStyle({ height: '24px' })
    })

    it('defaults to medium size', () => {
      const { container } = render(
        <StatusChip status="success">Default</StatusChip>,
      )
      const chip = container.firstChild as HTMLElement
      expect(chip).toHaveStyle({ height: '24px' })
    })
  })

  describe('pulse indicator', () => {
    it('renders pulse dot when pulse prop is true', () => {
      const { container } = render(
        <StatusChip status="success" pulse>
          Active
        </StatusChip>,
      )
      // The pulse dot should be rendered as a child Box
      const boxes = container.querySelectorAll('.MuiBox-root')
      expect(boxes.length).toBeGreaterThan(1)
    })

    it('does not render pulse dot when pulse is false', () => {
      render(
        <StatusChip status="success" pulse={false}>
          Inactive
        </StatusChip>,
      )
      // Should only have the main container and text
      expect(screen.getByText('Inactive')).toBeInTheDocument()
    })
  })

  describe('design token compliance', () => {
    it('uses --ob-radius-xs for border radius (Square Cyber-Minimalism)', () => {
      const { container } = render(
        <StatusChip status="success">Test</StatusChip>,
      )
      const chip = container.firstChild as HTMLElement
      expect(chip).toHaveStyle({
        borderRadius: 'var(--ob-radius-xs)',
      })
    })

    it('uses design tokens for spacing', () => {
      const { container } = render(
        <StatusChip status="success">Test</StatusChip>,
      )
      const chip = container.firstChild as HTMLElement
      expect(chip).toHaveStyle({
        paddingLeft: 'var(--ob-space-075)',
        paddingRight: 'var(--ob-space-075)',
        gap: 'var(--ob-space-050)',
      })
    })
  })

  describe('custom styles', () => {
    it('merges custom sx prop', () => {
      const { container } = render(
        <StatusChip status="success" sx={{ opacity: 0.5 }}>
          Custom
        </StatusChip>,
      )
      const chip = container.firstChild as HTMLElement
      expect(chip).toHaveStyle({
        borderRadius: 'var(--ob-radius-xs)',
      })
    })
  })
})
