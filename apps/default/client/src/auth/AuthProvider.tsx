import { useCallback, useEffect, useRef, useState, type ReactNode } from 'react'
import { AuthContext, type AuthStatus } from './AuthContext'
import { generateCodeChallenge, generateCodeVerifier } from './pkce'

const VERIFIER_KEY = 'pkce_code_verifier'
const STATE_KEY = 'pkce_state'

interface TokenResponse {
  access_token: string
  expires_in: number
  token_type: string
}

function generateState(): string {
  const array = new Uint8Array(16)
  crypto.getRandomValues(array)
  return btoa(String.fromCharCode(...array))
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=/g, '')
}

export function AuthProvider({ children }: { children: ReactNode }) {
  // Access token stored in ref — never in localStorage or sessionStorage
  const tokenRef = useRef<string | null>(null)
  const refreshTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const [status, setStatus] = useState<AuthStatus>('unauthenticated')
  const [error, setError] = useState<string | null>(null)
  // Mirror token in state purely so consumers re-render when it changes
  const [accessToken, setAccessToken] = useState<string | null>(null)

  const storeToken = useCallback((token: string, expiresIn: number) => {
    tokenRef.current = token
    setAccessToken(token)
    setStatus('authenticated')
    setError(null)

    // Schedule silent refresh at 80% of expiry
    if (refreshTimerRef.current) clearTimeout(refreshTimerRef.current)
    const refreshAt = Math.max((expiresIn * 0.8) * 1000, 0)
    refreshTimerRef.current = setTimeout(async () => {
      try {
        const res = await fetch('/auth/refresh', { method: 'POST', credentials: 'include' })
        if (!res.ok) throw new Error('Refresh failed')
        const data = (await res.json()) as TokenResponse
        storeToken(data.access_token, data.expires_in)
      } catch {
        tokenRef.current = null
        setAccessToken(null)
        setStatus('unauthenticated')
      }
    }, refreshAt)
  }, [])

  const login = useCallback(async () => {
    setStatus('authenticating')
    const verifier = generateCodeVerifier()
    const challenge = await generateCodeChallenge(verifier)
    const state = generateState()
    sessionStorage.setItem(VERIFIER_KEY, verifier)
    sessionStorage.setItem(STATE_KEY, state)

    const params = new URLSearchParams({
      response_type: 'code',
      code_challenge: challenge,
      code_challenge_method: 'S256',
      state,
    })
    window.location.href = `/auth/authorize?${params.toString()}`
  }, [])

  const logout = useCallback(async () => {
    try {
      await fetch('/auth/session', { method: 'DELETE', credentials: 'include' })
    } catch {
      // Best-effort
    }
    tokenRef.current = null
    setAccessToken(null)
    if (refreshTimerRef.current) clearTimeout(refreshTimerRef.current)
    setStatus('unauthenticated')
  }, [])

  const refreshToken = useCallback(async () => {
    try {
      const res = await fetch('/auth/refresh', { method: 'POST', credentials: 'include' })
      if (!res.ok) throw new Error('Refresh failed')
      const data = (await res.json()) as TokenResponse
      storeToken(data.access_token, data.expires_in)
    } catch (err) {
      setStatus('unauthenticated')
      setError(err instanceof Error ? err.message : 'Authentication failed')
    }
  }, [storeToken])

  // On mount: handle callback or attempt silent refresh
  useEffect(() => {
    const url = new URL(window.location.href)
    const code = url.searchParams.get('code')
    const returnedState = url.searchParams.get('state')

    if (code) {
      // Auth callback — exchange code for token
      const verifier = sessionStorage.getItem(VERIFIER_KEY)
      const savedState = sessionStorage.getItem(STATE_KEY)
      sessionStorage.removeItem(VERIFIER_KEY)
      sessionStorage.removeItem(STATE_KEY)

      if (!verifier || returnedState !== savedState) {
        setStatus('error')
        setError('Invalid auth callback state')
        return
      }

      setStatus('authenticating')
      fetch('/auth/token', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code, code_verifier: verifier }),
        credentials: 'include',
      })
        .then(async (res) => {
          if (!res.ok) throw new Error('Token exchange failed')
          return res.json() as Promise<TokenResponse>
        })
        .then((data) => {
          storeToken(data.access_token, data.expires_in)
          // Clean URL
          window.history.replaceState({}, '', '/')
        })
        .catch((err: unknown) => {
          setStatus('error')
          setError(err instanceof Error ? err.message : 'Token exchange failed')
        })
    } else {
      // Attempt silent refresh via HttpOnly refresh cookie
      fetch('/auth/refresh', { method: 'POST', credentials: 'include' })
        .then(async (res) => {
          if (!res.ok) return // Not authenticated — stay unauthenticated
          const data = (await res.json()) as TokenResponse
          storeToken(data.access_token, data.expires_in)
        })
        .catch(() => {
          // Silently ignore — user is unauthenticated
        })
    }

    return () => {
      if (refreshTimerRef.current) clearTimeout(refreshTimerRef.current)
    }
  }, [storeToken])

  return (
    <AuthContext.Provider value={{ status, accessToken, login, logout, refreshToken, error }}>
      {children}
    </AuthContext.Provider>
  )
}
