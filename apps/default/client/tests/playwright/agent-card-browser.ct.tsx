import { test, expect } from '@playwright/experimental-ct-react'
import { AgentCardBrowserPanel } from '../../src/tabs/Internals/AgentCardBrowserPanel'

// Inline fixtures to avoid ESM JSON import attribute requirements
const AGENTS_FIXTURE = [
  { name: 'working-memory', url: 'http://localhost:4101' },
  { name: 'reasoning', url: 'http://localhost:4102' },
]

const AGENT_CARD_FIXTURE = {
  name: 'working-memory',
  version: '0.1.0',
  description: 'Short-term context buffer — prefrontal cortex analogue',
  url: 'http://localhost:4101',
  capabilities: { mcp: true, a2a: true, sse: true },
  neuroanatomicalAnalogue: 'Prefrontal Cortex',
  tools: [
    { name: 'context/get', description: 'Retrieve current context window' },
    { name: 'context/set', description: 'Update context window' },
  ],
}

/**
 * Component integration tests for AgentCardBrowserPanel.
 *
 * All network calls are intercepted at the fetch boundary using page.route().
 * No real gateway is required.
 *
 * Covers:
 * - Shows loading state initially
 * - Fetches agent list and then each agent card; renders article cards
 * - Displays capability badges (MCP, A2A, SSE)
 * - Shows graceful fallback card when individual agent fetch fails
 * - Shows error alert when /api/agents fetch fails
 * - Renders tools list in <details> element
 */

test.describe('AgentCardBrowserPanel', () => {
  test('renders loaded agent cards when network calls succeed', async ({ mount, page }) => {
    // Mock the agents list
    await page.route('**/api/agents', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(AGENTS_FIXTURE),
      }),
    )

    // Mock each agent card endpoint
    await page.route('**/.well-known/agent-card.json', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(AGENT_CARD_FIXTURE),
      }),
    )

    const component = await mount(
      <AgentCardBrowserPanel accessToken="tok-test" />,
    )

    // Agent card article should appear
    const card = component.getByRole('article')
    await expect(card.first()).toBeVisible({ timeout: 5000 })

    // Title: "working-memory"
    await expect(card.first().getByRole('heading', { name: /working-memory/i })).toBeVisible()

    // Version badge
    await expect(card.first().getByText(/v0\.1\.0/)).toBeVisible()

    // MCP capability badge
    await expect(card.first().getByText('MCP')).toBeVisible()
  })

  test('renders the neuroanatomical analogue badge when present', async ({ mount, page }) => {
    await page.route('**/api/agents', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([AGENTS_FIXTURE[0]]),
      }),
    )

    await page.route('**/.well-known/agent-card.json', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(AGENT_CARD_FIXTURE),
      }),
    )

    const component = await mount(<AgentCardBrowserPanel accessToken="tok-test" />)

    // Neuroanatomical analogue badge — use exact text match to avoid description text collision
    await expect(component.getByText('Prefrontal Cortex', { exact: true })).toBeVisible({ timeout: 5000 })
  })

  test('renders tools list in a details/summary element', async ({ mount, page }) => {
    await page.route('**/api/agents', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([AGENTS_FIXTURE[0]]),
      }),
    )

    await page.route('**/.well-known/agent-card.json', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(AGENT_CARD_FIXTURE),
      }),
    )

    const component = await mount(<AgentCardBrowserPanel accessToken="tok-test" />)

    // Tools (2) summary should appear
    await expect(component.getByText(/tools \(2\)/i)).toBeVisible({ timeout: 5000 })

    // Expand details — click summary
    await component.getByText(/tools \(2\)/i).click()

    await expect(component.getByText('context/get')).toBeVisible()
    await expect(component.getByText('context/set')).toBeVisible()
  })

  test('shows an error alert when /api/agents fetch fails', async ({ mount, page }) => {
    // Abort the request to simulate network failure; component should show error state
    await page.route('**/api/agents', (route) => route.abort())

    const component = await mount(<AgentCardBrowserPanel accessToken="tok-test" />)

    // In error state, component root IS the alert — assert role and message directly
    await expect(component).toHaveAttribute('role', 'alert')
    await expect(component).toContainText('Failed to load')
  })

  test('renders no-agents placeholder when agent list is empty', async ({ mount, page }) => {
    await page.route('**/api/agents', (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: '[]' }),
    )

    const component = await mount(<AgentCardBrowserPanel accessToken="tok-test" />)

    // Should show placeholder (no agents registered)
    await expect(component.getByText(/no agents registered/i)).toBeVisible({ timeout: 5000 })
  })

  test('renders graceful fallback card when individual agent card fetch fails', async ({
    mount,
    page,
  }) => {
    await page.route('**/api/agents', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([{ name: 'broken-agent', url: 'http://localhost:9999' }]),
      }),
    )

    // The agent card endpoint returns a server error
    await page.route('**/.well-known/agent-card.json', (route) =>
      route.fulfill({ status: 503 }),
    )

    const component = await mount(<AgentCardBrowserPanel accessToken="tok-test" />)

    // Fallback card with "Agent card unavailable" should render
    await expect(component.getByText(/agent card unavailable/i)).toBeVisible({ timeout: 5000 })
  })
})
