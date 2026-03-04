import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { TabBar } from '../../src/shell/TabBar'

describe('TabBar', () => {
  it('renders with role="tablist"', () => {
    render(<TabBar activeTab="chat" onTabChange={() => {}} />)
    expect(screen.getByRole('tablist')).toBeInTheDocument()
  })

  it('renders tabs with role="tab"', () => {
    render(<TabBar activeTab="chat" onTabChange={() => {}} />)
    const tabs = screen.getAllByRole('tab')
    expect(tabs.length).toBe(2)
  })

  it('active tab has aria-selected="true"', () => {
    render(<TabBar activeTab="chat" onTabChange={() => {}} />)
    const chatTab = screen.getByRole('tab', { name: /chat/i })
    expect(chatTab).toHaveAttribute('aria-selected', 'true')
  })

  it('inactive tab has aria-selected="false"', () => {
    render(<TabBar activeTab="chat" onTabChange={() => {}} />)
    const internalsTab = screen.getByRole('tab', { name: /internals/i })
    expect(internalsTab).toHaveAttribute('aria-selected', 'false')
  })

  it('clicking a tab calls onTabChange with correct id', async () => {
    const user = userEvent.setup()
    const onTabChange = vi.fn()
    render(<TabBar activeTab="chat" onTabChange={onTabChange} />)

    await user.click(screen.getByRole('tab', { name: /internals/i }))

    expect(onTabChange).toHaveBeenCalledWith('internals')
  })

  it('ArrowRight key moves focus to next tab', async () => {
    const user = userEvent.setup()
    const onTabChange = vi.fn()
    render(<TabBar activeTab="chat" onTabChange={onTabChange} />)

    const chatTab = screen.getByRole('tab', { name: /chat/i })
    chatTab.focus()
    await user.keyboard('{ArrowRight}')

    expect(onTabChange).toHaveBeenCalledWith('internals')
  })

  it('ArrowLeft key wraps to last tab from first', async () => {
    const user = userEvent.setup()
    const onTabChange = vi.fn()
    render(<TabBar activeTab="chat" onTabChange={onTabChange} />)

    const chatTab = screen.getByRole('tab', { name: /chat/i })
    chatTab.focus()
    await user.keyboard('{ArrowLeft}')

    expect(onTabChange).toHaveBeenCalledWith('internals')
  })

  it('tabs have aria-controls pointing to panel ids', () => {
    render(<TabBar activeTab="chat" onTabChange={() => {}} />)
    const chatTab = screen.getByRole('tab', { name: /chat/i })
    expect(chatTab).toHaveAttribute('aria-controls', 'panel-chat')
    const internalsTab = screen.getByRole('tab', { name: /internals/i })
    expect(internalsTab).toHaveAttribute('aria-controls', 'panel-internals')
  })

  it('non-active tabs have tabIndex=-1 (roving tabindex)', () => {
    render(<TabBar activeTab="chat" onTabChange={() => {}} />)
    const internalsTab = screen.getByRole('tab', { name: /internals/i })
    expect(internalsTab).toHaveAttribute('tabindex', '-1')
  })
})
