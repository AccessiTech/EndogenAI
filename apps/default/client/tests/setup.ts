import '@testing-library/jest-dom'

// jsdom does not implement scrollIntoView — mock it globally
Object.defineProperty(HTMLElement.prototype, 'scrollIntoView', {
  writable: true,
  value: vi.fn(),
})
