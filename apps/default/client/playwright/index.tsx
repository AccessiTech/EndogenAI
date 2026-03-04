/**
 * Playwright Component Testing entry point for @endogenai/client.
 *
 * This file is loaded by the CT runner before each test.
 * Add global CSS imports, context providers, or other setup here.
 */

// Import global styles so components render with the correct custom properties
import '../src/styles/tokens.css'
import '../src/styles/global.css'
import '../src/styles/app.css'
