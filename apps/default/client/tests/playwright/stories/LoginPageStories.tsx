/**
 * Test story wrappers for LoginPage component.
 *
 * Playwright CT cannot mount components defined in test files.
 * Export wrapper components from this file and import them in test files.
 */
import { LoginPage } from '../../../src/auth/LoginPage'
import { AuthContext, type AuthContextValue } from '../../../src/auth/AuthContext'

const AUTH_DEFAULTS: AuthContextValue = {
  status: 'unauthenticated',
  accessToken: null,
  login: async () => {},
  logout: async () => {},
  refreshToken: async () => {},
  error: null,
}

/** LoginPage rendered with an authentication error visible. */
export function LoginPageWithError() {
  return (
    <AuthContext.Provider
      value={{ ...AUTH_DEFAULTS, error: 'Authentication failed — please try again.' }}
    >
      <LoginPage />
    </AuthContext.Provider>
  )
}

/** LoginPage where we can observe whether login() is called via a data attribute. */
export function LoginPageWithCallback() {
  return (
    <AuthContext.Provider
      value={{
        ...AUTH_DEFAULTS,
        login: async () => {
          // Signal to the test that login was called by updating the document title
          document.title = 'login-called'
        },
      }}
    >
      <LoginPage />
    </AuthContext.Provider>
  )
}
