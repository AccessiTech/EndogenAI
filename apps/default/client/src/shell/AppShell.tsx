import type { ReactNode } from 'react'
import { TabBar, type TabId } from './TabBar'
import { StatusBar } from './StatusBar'
import type { SSEStatus } from '../sse/useSSEStream'

interface AppShellProps {
  activeTab: TabId
  onTabChange: (tab: TabId) => void
  sseStatus: SSEStatus
  reconnectCount: number
  children: ReactNode
}

/**
 * Top-level layout shell.
 *
 * HTML landmarks:
 * - <header role="banner"> — app title, tab nav, status
 * - <main> — tab panel content
 */
export function AppShell({
  activeTab,
  onTabChange,
  sseStatus,
  reconnectCount,
  children,
}: AppShellProps) {
  return (
    <div className="app-shell">
      <header role="banner" className="app-header">
        <h1 className="app-title">
          {import.meta.env['VITE_APP_TITLE'] ?? 'frankenbrAIn'}
        </h1>
        <TabBar activeTab={activeTab} onTabChange={onTabChange} />
        <StatusBar sseStatus={sseStatus} reconnectCount={reconnectCount} />
      </header>
      <main className="app-main" id="main-content">
        {children}
      </main>
    </div>
  )
}
