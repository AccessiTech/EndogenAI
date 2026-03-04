/**
 * Test story wrappers for App component.
 *
 * Playwright CT cannot mount components defined in test files.
 * Export wrapper components from this file and import them in test files.
 */
import { App } from '../../../src/App'
import { AuthContext, type AuthContextValue } from '../../../src/auth/AuthContext'

const AUTH_DEFAULTS: AuthContextValue = {
  status: 'unauthenticated',
  accessToken: null,
  login: async () => {},
  logout: async () => {},
  refreshToken: async () => {},
  error: null,
}

// --- Unauthenticated ---
export function AppUnauthenticated() {
  return (
    <AuthContext.Provider value={AUTH_DEFAULTS}>
      <App />
    </AuthContext.Provider>
  )
}

// --- Error state ---
export function AppError() {
  return (
    <AuthContext.Provider value={{ ...AUTH_DEFAULTS, status: 'error', error: 'PKCE exchange failed' }}>
      <App />
    </AuthContext.Provider>
  )
}

// --- Authenticating spinner ---
export function AppAuthenticating() {
  return (
    <AuthContext.Provider value={{ ...AUTH_DEFAULTS, status: 'authenticating' }}>
      <App />
    </AuthContext.Provider>
  )
}

// --- Authenticated with real token ---
export function AppAuthenticated() {
  return (
    <AuthContext.Provider value={{ ...AUTH_DEFAULTS, status: 'authenticated', accessToken: 'tok-shell' }}>
      <App />
    </AuthContext.Provider>
  )
}

/** Authenticated with custom logout callback (for interaction testing). */
export function AppAuthenticatedWithLogout({ onLogout }: { onLogout: () => void }) {
  return (
    <AuthContext.Provider
      value={{ ...AUTH_DEFAULTS, status: 'authenticated', accessToken: 'tok-shell', logout: async () => { onLogout() } }}
    >
      <App />
    </AuthContext.Provider>
  )
}
