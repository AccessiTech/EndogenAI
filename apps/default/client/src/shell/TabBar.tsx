import type { KeyboardEvent } from 'react'

export type TabId = 'chat' | 'internals'

interface Tab {
  id: TabId
  label: string
}

const TABS: Tab[] = [
  { id: 'chat', label: 'Chat' },
  { id: 'internals', label: 'Internals' },
]

interface TabBarProps {
  activeTab: TabId
  onTabChange: (tab: TabId) => void
}

/**
 * Accessible tab bar.
 *
 * WCAG 2.1 AA:
 * - role="tablist" on container
 * - role="tab" + aria-selected on each button
 * - aria-controls pointing to panel id
 * - ArrowLeft/ArrowRight keyboard navigation
 * - Enter/Space activation (handled natively by button)
 */
export function TabBar({ activeTab, onTabChange }: TabBarProps) {
  const handleKeyDown = (e: KeyboardEvent<HTMLElement>, index: number) => {
    let next = index
    if (e.key === 'ArrowRight') {
      e.preventDefault()
      next = (index + 1) % TABS.length
    } else if (e.key === 'ArrowLeft') {
      e.preventDefault()
      next = (index - 1 + TABS.length) % TABS.length
    } else {
      return
    }
    const nextTab = TABS[next]
    if (nextTab) {
      onTabChange(nextTab.id)
      // Move focus to the newly selected tab
      const el = document.getElementById(`tab-${nextTab.id}`)
      el?.focus()
    }
  }

  return (
    <div role="tablist" aria-label="Main navigation" className="tab-bar">
      {TABS.map((tab, index) => (
        <button
          key={tab.id}
          id={`tab-${tab.id}`}
          role="tab"
          aria-selected={activeTab === tab.id}
          aria-controls={`panel-${tab.id}`}
          tabIndex={activeTab === tab.id ? 0 : -1}
          onClick={() => onTabChange(tab.id)}
          onKeyDown={(e) => handleKeyDown(e, index)}
        >
          {tab.label}
        </button>
      ))}
    </div>
  )
}
