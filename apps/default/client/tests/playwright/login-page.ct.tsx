import { test, expect } from '@playwright/experimental-ct-react'
import { LoginPage } from '../../src/auth/LoginPage'
import { LoginPageWithError, LoginPageWithCallback } from './stories/LoginPageStories'

/**
 * Component integration tests for LoginPage.
 *
 * Covers:
 * - Login page renders heading, subtitle, and Log in button
 * - Error alert is shown when auth context has an error
 * - Log in button triggers login() callback
 */

test.describe('LoginPage', () => {
  test('renders the app title and Log in button', async ({ mount }) => {
    const component = await mount(<LoginPage />)

    // component IS the <main> landmark — assert it directly
    await expect(component).toBeVisible()

    // Assert the PKCE login button
    await expect(component.getByRole('button', { name: /sign in with pkce/i })).toBeVisible()

    // Assert descriptive text
    await expect(component.getByText(/sign in to access the workspace/i)).toBeVisible()
  })

  test('does not render error alert when no error', async ({ mount }) => {
    const component = await mount(<LoginPage />)

    await expect(component.getByRole('alert')).toHaveCount(0)
  })

  test('renders error alert when auth context has an error', async ({ mount }) => {
    const component = await mount(<LoginPageWithError />)

    const alert = component.getByRole('alert')
    await expect(alert).toBeVisible()
    await expect(alert).toContainText('Authentication failed')
  })

  test('calls login() when Log in button is clicked', async ({ mount, page }) => {
    const component = await mount(<LoginPageWithCallback />)

    await component.getByRole('button', { name: /sign in with pkce/i }).click()

    // Story sets document.title to 'login-called' as a signal
    await expect(page).toHaveTitle('login-called')
  })
})
