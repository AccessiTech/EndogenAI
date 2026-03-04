import { Hono } from 'hono'

const wellknown = new Hono()

wellknown.get('/oauth-authorization-server', (c) => {
  const base = process.env.ISSUER_URL ?? 'http://localhost:3001'
  return c.json({
    issuer: base,
    authorization_endpoint: `${base}/auth/authorize`,
    token_endpoint: `${base}/auth/token`,
    response_types_supported: ['code'],
    grant_types_supported: ['authorization_code'],
    code_challenge_methods_supported: ['S256'],
    token_endpoint_auth_methods_supported: ['none'],
  })
})

export default wellknown
