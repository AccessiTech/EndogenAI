import { SignJWT, jwtVerify, type JWTPayload } from 'jose'
import { randomBytes } from 'crypto'

const getSecret = () => new TextEncoder().encode(process.env.JWT_SECRET ?? 'dev-secret-change-me')
const EXPIRY = Number(process.env.JWT_EXPIRY_SECONDS ?? 900)
const CLOCK_SKEW = 30

export interface AccessTokenPayload {
  sub: string
  scope: string
  aud: string
}

export async function signAccessToken(payload: AccessTokenPayload): Promise<string> {
  return new SignJWT({ ...payload })
    .setProtectedHeader({ alg: 'HS256' })
    .setIssuedAt()
    .setExpirationTime(`${EXPIRY}s`)
    .sign(getSecret())
}

export async function verifyAccessToken(token: string): Promise<JWTPayload> {
  const { payload } = await jwtVerify(token, getSecret(), {
    audience: process.env.MCP_SERVER_URI ?? 'http://localhost:8000',
    clockTolerance: CLOCK_SKEW,
  })
  return payload
}

export async function signRefreshToken(sub: string): Promise<string> {
  const jti = randomBytes(16).toString('hex')
  return new SignJWT({ sub, type: 'refresh', jti })
    .setProtectedHeader({ alg: 'HS256' })
    .setIssuedAt()
    .setExpirationTime(`${process.env.REFRESH_TOKEN_EXPIRY_SECONDS ?? 86400}s`)
    .sign(getSecret())
}

export async function verifyRefreshToken(token: string): Promise<JWTPayload> {
  const { payload } = await jwtVerify(token, getSecret())
  if (payload['type'] !== 'refresh') {
    throw new Error('Not a refresh token')
  }
  return payload
}
