import { createContext } from 'react'

export type AuthStatus = 'unauthenticated' | 'authenticating' | 'authenticated' | 'error'

export interface AuthContextValue {
  status: AuthStatus
  accessToken: string | null
  login: () => Promise<void>
  logout: () => Promise<void>
  refreshToken: () => Promise<void>
  error: string | null
}

export const AuthContext = createContext<AuthContextValue>({
  status: 'unauthenticated',
  accessToken: null,
  login: async () => {},
  logout: async () => {},
  refreshToken: async () => {},
  error: null,
})
