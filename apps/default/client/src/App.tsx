import { useState } from 'react'
import { useAuth } from './auth/useAuth'
import { LoginPage } from './auth/LoginPage'
import { AppShell } from './shell/AppShell'
import { TabBar, type TabId } from './shell/TabBar'
import { useSSEStream } from './sse/useSSEStream'
import { ChatTab } from './tabs/Chat'
import { InternalsTab } from './tabs/Internals'

/**
 * App root component.
 *
 * - Guards all content behind auth (shows LoginPage when unauthenticated)
 * - Creates the single shared useSSEStream instance at app root
 * - Renders two-tab shell: Chat + Internals
 */
export function App() {
  const { status, accessToken, logout } = useAuth()
  const [activeTab, setActiveTab] = useState<TabId>('chat')

  // Shared SSE stream — single connection for both tabs (D8B-1)
  const { events, status: sseStatus, reconnectCount } = useSSEStream({
    url: '/api/stream',
    token: accessToken,
    enabled: status === 'authenticated',
  })

  if (status === 'unauthenticated' || status === 'error') {
    return <LoginPage />
  }

  if (status === 'authenticating') {
    return (
      <main
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          height: '100vh',
          color: 'var(--color-text-muted)',
        }}
        aria-label="Signing in"
      >
        <div role="status" aria-live="polite">
          Signing in…
        </div>
      </main>
    )
  }

  return (
    <AppShell
      activeTab={activeTab}
      onTabChange={setActiveTab}
      sseStatus={sseStatus}
      reconnectCount={reconnectCount}
    >
      {/* Logout button — accessible in the shell; positioned via CSS */}
      <button
        onClick={() => void logout()}
        aria-label="Sign out"
        style={{
          position: 'absolute',
          top: 'var(--space-2)',
          right: 'var(--space-4)',
          background: 'transparent',
          border: '1px solid var(--color-border)',
          borderRadius: 'var(--radius-sm)',
          color: 'var(--color-text-muted)',
          padding: 'var(--space-1) var(--space-3)',
          cursor: 'pointer',
          fontSize: 'var(--font-size-sm)',
          minHeight: 'var(--touch-target)',
          zIndex: 10,
        }}
      >
        Sign out
      </button>

      {/* Chat tab panel */}
      <section
        id="panel-chat"
        role="tabpanel"
        aria-labelledby="tab-chat"
        className="tab-panel"
        data-active={activeTab === 'chat' ? 'true' : 'false'}
        hidden={activeTab !== 'chat'}
      >
        {activeTab === 'chat' && (
          <ChatTab
            accessToken={accessToken}
            sseEvents={events}
            sseStatus={sseStatus}
          />
        )}
      </section>

      {/* Internals tab panel */}
      <section
        id="panel-internals"
        role="tabpanel"
        aria-labelledby="tab-internals"
        className="tab-panel"
        data-active={activeTab === 'internals' ? 'true' : 'false'}
        hidden={activeTab !== 'internals'}
      >
        {activeTab === 'internals' && (
          <InternalsTab accessToken={accessToken} sseEvents={events} />
        )}
      </section>
    </AppShell>
  )
}

// Re-export TabBar from here for convenience (used in AppShell via import)
export { TabBar }
