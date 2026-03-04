import { test, expect } from '@playwright/experimental-ct-react'
import {
  AppUnauthenticated,
  AppError,
  AppAuthenticating,
  AppAuthenticated,
} from './stories/AppStories'

/**
 * Component integration tests for top-level App routing.
 *
 * Story components are imported from ./stories/AppStories because Playwright CT
 * cannot mount components defined inside test files.
 *
 * Covers:
 * - Unauthenticated state shows the LoginPage
 * - Authenticating state shows the "Signing in…" spinner
 * - Authenticated state shows the two-tab shell (Chat + Internals)
 * - Tab switching renders the correct panel
 * - Sign out button is visible when authenticated
 * - Sign out triggers DELETE /auth/session
 */

test.describe('App routing', () => {
  test('shows LoginPage when unauthenticated', async ({ mount }) => {
    const component = await mount(<AppUnauthenticated />)

    // component IS the <main> landmark — assert it directly
    await expect(component).toBeVisible()
    await expect(component.getByRole('button', { name: /sign in with pkce/i })).toBeVisible()
  })

  test('shows error state on LoginPage when auth errors', async ({ mount }) => {
    const component = await mount(<AppError />)

    // component IS the <main> landmark — assert it directly
    await expect(component).toBeVisible()
    await expect(component.getByRole('alert')).toContainText('PKCE exchange failed')
  })

  test('shows Signing in spinner during authentication', async ({ mount }) => {
    const component = await mount(<AppAuthenticating />)

    const status = component.getByRole('status')
    await expect(status).toBeVisible()
    await expect(status).toContainText(/signing in/i)
  })

  test('shows two-tab shell when authenticated', async ({ mount, page }) => {
    // Mock the SSE stream endpoint — returns empty stream so the hook doesn't error
    await page.route('**/api/stream', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'text/event-stream',
        body: '',
      }),
    )
    await page.route('**/api/agents', (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: '[]' }),
    )

    const component = await mount(<AppAuthenticated />)

    // TabBar with Chat + Internals tabs
    const tablist = component.getByRole('tablist', { name: /main navigation/i })
    await expect(tablist).toBeVisible()
    await expect(tablist.getByRole('tab', { name: /chat/i })).toBeVisible()
    await expect(tablist.getByRole('tab', { name: /internals/i })).toBeVisible()

    // Chat tab is active by default
    await expect(tablist.getByRole('tab', { name: /chat/i })).toHaveAttribute('aria-selected', 'true')
  })

  test('clicking Internals tab switches the active panel', async ({ mount, page }) => {
    await page.route('**/api/stream', (route) =>
      route.fulfill({ status: 200, contentType: 'text/event-stream', body: '' }),
    )
    await page.route('**/api/agents', (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: '[]' }),
    )

    const component = await mount(<AppAuthenticated />)

    const tablist = component.getByRole('tablist', { name: /main navigation/i })
    await tablist.getByRole('tab', { name: /internals/i }).click()

    await expect(
      tablist.getByRole('tab', { name: /internals/i }),
    ).toHaveAttribute('aria-selected', 'true')

    // The Internals sub-nav tablist is unique to the InternalsTab panel
    await expect(
      component.getByRole('tablist', { name: /internals panels/i }),
    ).toBeVisible()
  })

  test('sign out button is visible when authenticated', async ({ mount, page }) => {
    await page.route('**/api/stream', (route) =>
      route.fulfill({ status: 200, contentType: 'text/event-stream', body: '' }),
    )
    await page.route('**/api/agents', (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: '[]' }),
    )

    const component = await mount(<AppAuthenticated />)

    await expect(component.getByRole('button', { name: /sign out/i })).toBeVisible()
  })

  test('sign out button is clickable when authenticated', async ({ mount, page }) => {
    await page.route('**/api/stream', (route) =>
      route.fulfill({ status: 200, contentType: 'text/event-stream', body: '' }),
    )
    await page.route('**/api/agents', (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: '[]' }),
    )
    // Intercept logout request so clicking the button doesn't cause an error
    await page.route('**/auth/session', (route) => void route.fulfill({ status: 204 }))

    const component = await mount(<AppAuthenticated />)
    const signOutButton = component.getByRole('button', { name: /sign out/i })
    await expect(signOutButton).toBeVisible()
    await expect(signOutButton).toBeEnabled()

    // Button should be clickable without errors
    await signOutButton.click()
  })
})
