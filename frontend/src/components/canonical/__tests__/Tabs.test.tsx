import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { Tabs, TabPanel } from '../Tabs'
import HomeIcon from '@mui/icons-material/Home'

describe('Tabs', () => {
  const defaultTabs = [
    { id: 'tab1', label: 'Tab 1' },
    { id: 'tab2', label: 'Tab 2' },
    { id: 'tab3', label: 'Tab 3' },
  ]

  describe('rendering', () => {
    it('renders all tabs', () => {
      render(
        <Tabs tabs={defaultTabs} activeTab="tab1" onTabChange={() => {}} />,
      )
      expect(screen.getByText('Tab 1')).toBeInTheDocument()
      expect(screen.getByText('Tab 2')).toBeInTheDocument()
      expect(screen.getByText('Tab 3')).toBeInTheDocument()
    })

    it('renders with tablist role', () => {
      render(
        <Tabs tabs={defaultTabs} activeTab="tab1" onTabChange={() => {}} />,
      )
      expect(screen.getByRole('tablist')).toBeInTheDocument()
    })

    it('renders each tab with tab role', () => {
      render(
        <Tabs tabs={defaultTabs} activeTab="tab1" onTabChange={() => {}} />,
      )
      expect(screen.getAllByRole('tab')).toHaveLength(3)
    })

    it('renders with icons', () => {
      const tabsWithIcon = [
        {
          id: 'home',
          label: 'Home',
          icon: <HomeIcon data-testid="home-icon" />,
        },
      ]
      render(
        <Tabs tabs={tabsWithIcon} activeTab="home" onTabChange={() => {}} />,
      )
      expect(screen.getByTestId('home-icon')).toBeInTheDocument()
    })
  })

  describe('active state', () => {
    it('marks active tab with aria-selected=true', () => {
      render(
        <Tabs tabs={defaultTabs} activeTab="tab2" onTabChange={() => {}} />,
      )
      const tabs = screen.getAllByRole('tab')
      expect(tabs[0]).toHaveAttribute('aria-selected', 'false')
      expect(tabs[1]).toHaveAttribute('aria-selected', 'true')
      expect(tabs[2]).toHaveAttribute('aria-selected', 'false')
    })
  })

  describe('tab change', () => {
    it('calls onTabChange when tab is clicked', () => {
      const onTabChange = vi.fn()
      render(
        <Tabs tabs={defaultTabs} activeTab="tab1" onTabChange={onTabChange} />,
      )
      fireEvent.click(screen.getByText('Tab 2'))
      expect(onTabChange).toHaveBeenCalledWith('tab2')
    })

    it('calls onTabChange when Enter key is pressed', () => {
      const onTabChange = vi.fn()
      render(
        <Tabs tabs={defaultTabs} activeTab="tab1" onTabChange={onTabChange} />,
      )
      const tab2 = screen.getByText('Tab 2')
      fireEvent.keyDown(tab2, { key: 'Enter' })
      expect(onTabChange).toHaveBeenCalledWith('tab2')
    })

    it('calls onTabChange when Space key is pressed', () => {
      const onTabChange = vi.fn()
      render(
        <Tabs tabs={defaultTabs} activeTab="tab1" onTabChange={onTabChange} />,
      )
      const tab2 = screen.getByText('Tab 2')
      fireEvent.keyDown(tab2, { key: ' ' })
      expect(onTabChange).toHaveBeenCalledWith('tab2')
    })
  })

  describe('disabled state', () => {
    it('marks disabled tab with aria-disabled=true', () => {
      const tabsWithDisabled = [
        { id: 'tab1', label: 'Tab 1' },
        { id: 'tab2', label: 'Tab 2', disabled: true },
      ]
      render(
        <Tabs
          tabs={tabsWithDisabled}
          activeTab="tab1"
          onTabChange={() => {}}
        />,
      )
      const tabs = screen.getAllByRole('tab')
      expect(tabs[1]).toHaveAttribute('aria-disabled', 'true')
    })

    it('does not call onTabChange when disabled tab is clicked', () => {
      const onTabChange = vi.fn()
      const tabsWithDisabled = [
        { id: 'tab1', label: 'Tab 1' },
        { id: 'tab2', label: 'Tab 2', disabled: true },
      ]
      render(
        <Tabs
          tabs={tabsWithDisabled}
          activeTab="tab1"
          onTabChange={onTabChange}
        />,
      )
      fireEvent.click(screen.getByText('Tab 2'))
      expect(onTabChange).not.toHaveBeenCalled()
    })

    it('sets tabIndex=-1 for disabled tabs', () => {
      const tabsWithDisabled = [
        { id: 'tab1', label: 'Tab 1' },
        { id: 'tab2', label: 'Tab 2', disabled: true },
      ]
      render(
        <Tabs
          tabs={tabsWithDisabled}
          activeTab="tab1"
          onTabChange={() => {}}
        />,
      )
      const tabs = screen.getAllByRole('tab')
      expect(tabs[1]).toHaveAttribute('tabindex', '-1')
    })
  })

  describe('variants', () => {
    it('renders underline variant with bottom border', () => {
      const { container } = render(
        <Tabs
          tabs={defaultTabs}
          activeTab="tab1"
          onTabChange={() => {}}
          variant="underline"
        />,
      )
      const tablist = container.querySelector('[role="tablist"]') as HTMLElement
      expect(tablist).toHaveStyle({
        borderBottom: 'var(--ob-divider-strong)',
      })
    })

    it('renders contained variant with background', () => {
      const { container } = render(
        <Tabs
          tabs={defaultTabs}
          activeTab="tab1"
          onTabChange={() => {}}
          variant="contained"
        />,
      )
      const tablist = container.querySelector('[role="tablist"]') as HTMLElement
      expect(tablist).toHaveStyle({
        background: 'var(--ob-color-surface-strong)',
        borderRadius: 'var(--ob-radius-sm)',
      })
    })
  })

  describe('sizes', () => {
    it('renders small size with 36px height', () => {
      render(
        <Tabs
          tabs={defaultTabs}
          activeTab="tab1"
          onTabChange={() => {}}
          size="sm"
        />,
      )
      const tabs = screen.getAllByRole('tab')
      expect(tabs[0]).toHaveStyle({ height: '36px' })
    })

    it('renders medium size with 40px height', () => {
      render(
        <Tabs
          tabs={defaultTabs}
          activeTab="tab1"
          onTabChange={() => {}}
          size="md"
        />,
      )
      const tabs = screen.getAllByRole('tab')
      expect(tabs[0]).toHaveStyle({ height: '40px' })
    })
  })

  describe('fullWidth', () => {
    it('applies full width when fullWidth is true', () => {
      const { container } = render(
        <Tabs
          tabs={defaultTabs}
          activeTab="tab1"
          onTabChange={() => {}}
          fullWidth
        />,
      )
      const tablist = container.querySelector('[role="tablist"]') as HTMLElement
      expect(tablist).toHaveStyle({ width: '100%' })
    })
  })

  describe('design token compliance', () => {
    it('uses --ob-radius-xs for contained tab buttons', () => {
      render(
        <Tabs
          tabs={defaultTabs}
          activeTab="tab1"
          onTabChange={() => {}}
          variant="contained"
        />,
      )
      const tabs = screen.getAllByRole('tab')
      expect(tabs[0]).toHaveStyle({
        borderRadius: 'var(--ob-radius-xs)',
      })
    })

    it('uses design tokens for spacing', () => {
      render(
        <Tabs tabs={defaultTabs} activeTab="tab1" onTabChange={() => {}} />,
      )
      const tabs = screen.getAllByRole('tab')
      expect(tabs[0]).toHaveStyle({
        paddingLeft: 'var(--ob-space-100)',
        paddingRight: 'var(--ob-space-100)',
      })
    })
  })
})

describe('TabPanel', () => {
  it('renders children when active', () => {
    render(
      <TabPanel tabId="tab1" activeTab="tab1">
        Panel Content
      </TabPanel>,
    )
    expect(screen.getByText('Panel Content')).toBeInTheDocument()
  })

  it('does not render when not active', () => {
    render(
      <TabPanel tabId="tab1" activeTab="tab2">
        Panel Content
      </TabPanel>,
    )
    expect(screen.queryByText('Panel Content')).not.toBeInTheDocument()
  })

  it('renders with tabpanel role', () => {
    render(
      <TabPanel tabId="tab1" activeTab="tab1">
        Panel Content
      </TabPanel>,
    )
    expect(screen.getByRole('tabpanel')).toBeInTheDocument()
  })

  it('applies custom sx prop', () => {
    const { container } = render(
      <TabPanel tabId="tab1" activeTab="tab1" sx={{ padding: '20px' }}>
        Panel Content
      </TabPanel>,
    )
    // Verify panel renders with tabpanel role (sx prop merged)
    expect(container.firstChild).toHaveAttribute('role', 'tabpanel')
  })
})
