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
