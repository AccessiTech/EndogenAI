/**
 * Browser-side PKCE helpers using the Web Crypto API.
 * These run entirely in the browser — no Node.js crypto required.
 */

/**
 * Generates a cryptographically random code verifier string (RFC 7636).
 * Uses synchronous crypto.getRandomValues — no async needed for generation.
 */
export function generateCodeVerifier(): string {
  const array = new Uint8Array(32)
  crypto.getRandomValues(array)
  return btoa(String.fromCharCode(...array))
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=/g, '')
}

/**
 * Derives the S256 code challenge from the verifier (async due to SubtleCrypto).
 */
export async function generateCodeChallenge(verifier: string): Promise<string> {
  const encoder = new TextEncoder()
  const data = encoder.encode(verifier)
  const digest = await crypto.subtle.digest('SHA-256', data)
  return btoa(String.fromCharCode(...new Uint8Array(digest)))
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=/g, '')
}
