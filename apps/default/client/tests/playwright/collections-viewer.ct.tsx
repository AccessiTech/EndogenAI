import { test, expect } from '@playwright/experimental-ct-react'
import { CollectionsViewer } from '../../src/tabs/Internals/CollectionsViewer'

/**
 * Component integration tests for CollectionsViewer.
 *
 * All network calls are intercepted at the fetch boundary.
 *
 * Covers:
 * - Renders resource collections grouped by 'group' field
 * - Shows placeholder when no resources are returned
 * - Shows error alert when /api/resources fetch fails
 * - Collection items display URI, name, and record count
 */

const MOCK_RESOURCES = [
  {
    uri: 'chroma://brain.knowledge',
    mimeType: 'application/x-chroma-collection',
    name: 'brain.knowledge',
    description: 'Morphogenetic seed documents',
    group: 'knowledge',
    backend: 'chromadb',
    recordCount: 142,
    lastUpdated: '2026-03-01T00:00:00Z',
  },
  {
    uri: 'chroma://brain.episodic',
    mimeType: 'application/x-chroma-collection',
    name: 'brain.episodic',
    description: 'Episodic memory store',
    group: 'memory',
    backend: 'chromadb',
    recordCount: 38,
    lastUpdated: '2026-03-02T00:00:00Z',
  },
  {
    uri: 'chroma://brain.ltm',
    mimeType: 'application/x-chroma-collection',
    name: 'brain.ltm',
    description: 'Long-term memory store',
    group: 'memory',
    backend: 'chromadb',
    recordCount: 507,
    lastUpdated: '2026-03-03T00:00:00Z',
  },
]

test.describe('CollectionsViewer', () => {
  test('renders collection entries when /api/resources returns data', async ({ mount, page }) => {
    await page.route('**/api/resources', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ resources: MOCK_RESOURCES, total: MOCK_RESOURCES.length }),
      }),
    )

    const component = await mount(<CollectionsViewer accessToken="tok-test" />)

    // Should render 3 collection items; use exact match to avoid substring conflicts
    await expect(component.getByText('brain.knowledge', { exact: true })).toBeVisible({ timeout: 5000 })
    await expect(component.getByText('brain.episodic', { exact: true })).toBeVisible()
    await expect(component.getByText('brain.ltm', { exact: true })).toBeVisible()
  })

  test('groups resources by their group field', async ({ mount, page }) => {
    await page.route('**/api/resources', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ resources: MOCK_RESOURCES, total: MOCK_RESOURCES.length }),
      }),
    )

    const component = await mount(<CollectionsViewer accessToken="tok-test" />)

    // Group headings should be present — use heading role to avoid matching URI/name substrings
    await expect(component.getByRole('heading', { name: 'knowledge' })).toBeVisible({ timeout: 5000 })
    await expect(component.getByRole('heading', { name: 'memory' })).toBeVisible()
  })

  test('displays record counts for each collection', async ({ mount, page }) => {
    await page.route('**/api/resources', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ resources: MOCK_RESOURCES, total: MOCK_RESOURCES.length }),
      }),
    )

    const component = await mount(<CollectionsViewer accessToken="tok-test" />)

    await expect(component.getByText(/142/)).toBeVisible({ timeout: 5000 })
    await expect(component.getByText(/38/)).toBeVisible()
    await expect(component.getByText(/507/)).toBeVisible()
  })

  test('shows placeholder when resource list is empty', async ({ mount, page }) => {
    await page.route('**/api/resources', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ resources: [], total: 0 }),
      }),
    )

    const component = await mount(<CollectionsViewer accessToken="tok-test" />)

    await expect(
      component.getByText(/no resource collections found/i),
    ).toBeVisible({ timeout: 5000 })
  })

  test('shows error alert when /api/resources fetch fails', async ({ mount, page }) => {
    await page.route('**/api/resources', (route) =>
      route.fulfill({
        status: 503,
        contentType: 'application/json',
        body: '{"error":"service unavailable"}',
      }),
    )

    const component = await mount(<CollectionsViewer accessToken="tok-test" />)

    // In error state, component root IS the alert — assert role and message directly
    await expect(component).toHaveAttribute('role', 'alert')
    await expect(component).toContainText('API error: 503')
  })
})
