import { useAuth } from './useAuth'

/**
 * Minimal login page shown when the user is unauthenticated.
 * The "Log in" button initiates the PKCE redirect — the phase-8A auto-approve
 * stub completes the flow instantly in development.
 */
export function LoginPage() {
  const { login, error } = useAuth()

  return (
    <main className="login-page" aria-label="Sign in">
      <div className="login-card">
        <h1 className="app-title" aria-label="frankenbrAIn — sign in required">
          {import.meta.env['VITE_APP_TITLE'] ?? 'frankenbrAIn'}
        </h1>
        <p style={{ color: 'var(--color-text-muted)', margin: 0 }}>
          Sign in to access the workspace.
        </p>
        {error && (
          <div role="alert" className="error-alert" aria-live="assertive">
            {error}
          </div>
        )}
        <button
          className="login-btn"
          onClick={() => void login()}

        >
          Log in
        </button>
      </div>
    </main>
  )
}
