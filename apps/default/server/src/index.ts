import { serve } from '@hono/node-server'
import { initTelemetry } from './telemetry.js'
import { createApp } from './app.js'

initTelemetry()

const app = createApp()
const port = Number(process.env.PORT ?? 3001)

serve({ fetch: app.fetch, port }, () => {
  console.log(`Gateway listening on http://localhost:${port}`)
})
