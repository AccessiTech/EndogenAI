# Observability Stack

Local observability stack for the brAIn framework, providing structured telemetry collection, metrics scraping, and
dashboarding.

## Components

| Service                     | Port                     | Purpose                                            |
| --------------------------- | ------------------------ | -------------------------------------------------- |
| **OpenTelemetry Collector** | 4317 (gRPC), 4318 (HTTP) | Receives OTLP traces/metrics/logs from all modules |
| **Prometheus**              | 9090                     | Scrapes and stores time-series metrics             |
| **Grafana**                 | 3000                     | Dashboard UI — default login: `admin` / `admin`    |

## Starting the Stack

```bash
docker compose up -d otel-collector prometheus grafana
```

Or start the full local development stack:

```bash
docker compose up -d
```

## Configuration Files

| File                               | Purpose                                                     |
| ---------------------------------- | ----------------------------------------------------------- |
| `otel-collector.yaml`              | OTel Collector pipeline: receivers → processors → exporters |
| `prometheus.yml`                   | Prometheus scrape targets and global config                 |
| `grafana/datasources/default.yaml` | Grafana datasource provisioning (Prometheus)                |

## Instrumenting a Module

All modules emit telemetry via the OpenTelemetry SDK and the shared utilities defined in `shared/utils/`:

- **Logs**: structured JSON, emitted via `structlog` (Python) or `pino` (TypeScript)
- **Traces**: W3C TraceContext propagated across all inter-module boundaries
- **Metrics**: counters, histograms, and gauges for signal throughput, latency, and collection sizes

See [`shared/utils/logging.md`](../shared/utils/logging.md), [`shared/utils/tracing.md`](../shared/utils/tracing.md),
and [`shared/utils/validation.md`](../shared/utils/validation.md) for specifications.

## Adding Dashboards

Place Grafana dashboard JSON files in `grafana/dashboards/` and add a dashboard provisioning config to
`grafana/dashboards/default.yaml`. See the
[Grafana provisioning docs](https://grafana.com/docs/grafana/latest/administration/provisioning/).

**Phase 8.4 dashboards** (to be provisioned):

| File | Panels |
| --- | --- |
| `grafana/dashboards/gateway.json` | Request rate, error rate, active SSE connections, P50/P95/P99 latency (`/api/input`), auth failure rate |
| `grafana/dashboards/signal-flow.json` | Per-module latency histograms (from OTel spans → Prometheus histograms), module health via Blackbox Exporter |

## Blackbox Exporter _(Phase 8.4)_

Prometheus [Blackbox Exporter](https://github.com/prometheus/blackbox_exporter) probes are added in Phase 8.4 to
provide reliable HTTP-level health checks per module. Each module's `/health` endpoint receives an `http_2xx` probe;
`probe_success = 1` is the health signal. Configuration added to `docker-compose.yml` and `prometheus.yml`.

## Distributed Traces — Grafana Tempo _(optional profile)_

[Grafana Tempo](https://grafana.com/oss/tempo/) is available as an optional `observability-full` Docker Compose
profile, added in Phase 8.4:

```bash
# Start full observability stack including Tempo
docker compose --profile observability-full up -d
```

Tempo provides distributed trace waterfall views (TraceQL). Without this profile, only latency histograms are
available (from OTel spans exported as Prometheus metrics). Configuration in `observability/tempo.yaml`.

The `observability-full` profile is non-blocking for Phase 8 Gate 5 — all gate criteria can be met with
Prometheus + Grafana alone.
