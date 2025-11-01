import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'

import { PageMiniNav } from './PageMiniNav'

describe('PageMiniNav', () => {
  it('renders the provided navigation items in order', () => {
    const items = [
      { label: 'Overview', to: '/overview' },
      { label: 'Pipeline', to: '/pipeline' },
      { label: 'Insights', to: '/insights' },
    ]

    render(<PageMiniNav items={items} />)

    const links = screen.getAllByRole('link')
    expect(links).toHaveLength(3)
    expect(links[0]).toHaveAttribute('href', '/overview')
    expect(links[0]).toHaveTextContent('Overview')
    expect(links[1]).toHaveAttribute('href', '/pipeline')
    expect(links[2]).toHaveAttribute('href', '/insights')
  })

  it('handles an empty list without crashing', () => {
    render(<PageMiniNav items={[]} />)

    const navigation = screen.getByRole('navigation')
    expect(navigation).toBeInTheDocument()
    expect(screen.queryAllByRole('link')).toHaveLength(0)
  })
})
