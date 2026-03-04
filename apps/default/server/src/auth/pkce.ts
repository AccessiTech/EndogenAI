import { createHash, randomBytes, timingSafeEqual } from 'crypto'

export function generateCodeVerifier(): string {
  return randomBytes(32).toString('base64url')
}

export function generateCodeChallenge(verifier: string): string {
  return createHash('sha256').update(verifier).digest('base64url')
}

function timingSafeStringEqual(a: string, b: string): boolean {
  if (a.length !== b.length) return false
  return timingSafeEqual(Buffer.from(a), Buffer.from(b))
}

export function verifyCodeChallenge(verifier: string, challenge: string): boolean {
  return timingSafeStringEqual(generateCodeChallenge(verifier), challenge)
}
