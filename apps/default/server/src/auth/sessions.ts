export interface AuthCodeEntry {
  clientId: string
  redirectUri: string
  codeChallenge: string
  codeChallengeMethod: 'S256'
  sub: string
  expiresAt: number
}

const codes = new Map<string, AuthCodeEntry>()

// Active refresh tokens (rotation + revocation set)
const activeRefreshTokens = new Set<string>()

export function storeAuthCode(code: string, entry: AuthCodeEntry): void {
  codes.set(code, entry)
}

export function consumeAuthCode(code: string): AuthCodeEntry | undefined {
  const entry = codes.get(code)
  if (!entry || entry.expiresAt < Date.now()) {
    codes.delete(code)
    return undefined
  }
  codes.delete(code)
  return entry
}

export function registerRefreshToken(token: string): void {
  activeRefreshTokens.add(token)
}

/**
 * Rotate: removes old token and registers new one atomically.
 * Returns false if the old token is not active (replay attack).
 */
export function rotateRefreshToken(oldToken: string, newToken: string): boolean {
  if (!activeRefreshTokens.has(oldToken)) return false
  activeRefreshTokens.delete(oldToken)
  activeRefreshTokens.add(newToken)
  return true
}

export function revokeRefreshToken(token: string): void {
  activeRefreshTokens.delete(token)
}

export function isRefreshTokenActive(token: string): boolean {
  return activeRefreshTokens.has(token)
}

// Exported for testing — clears all state
export function clearAllCodes(): void {
  codes.clear()
  activeRefreshTokens.clear()
}
