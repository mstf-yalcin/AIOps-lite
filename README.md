# AIOps-Lite

## Overview
AIOps-Lite is a proof-of-concept that demonstrates how production-style observability signals combined with lightweight machine learning can deliver anomaly detection and root cause analysis (RCA) for microservice-based systems. The repository demonstrates the full path from telemetry collection to automated AIOps reporting so reliability engineers can experiment with practical workflows.

## Architecture
```
[Clients]
   |
[API Gateway] --routes--> Spring Boot services (accounts, loans, cards)
   |                               |
   |                        emits metrics/logs/traces
   v                               v
[Eureka] <--> [Config Server]   [Alloy Collector]
                                    |
            -------------------------------------------------
            | Prometheus | Loki (read/write/backend) | Tempo |
            -------------------------------------------------
                                    |
                              [Grafana Dashboards]
                                    |
                             [ops Python analytics]
                                    |
                       aiops_report.json (RCA summary)
```

## Technology Stack
- **Service layer:** Spring Boot microservices, Spring Cloud Config Server, Eureka service discovery, API Gateway.
- **Observability:** Prometheus for metrics, Loki (read/write/backend) for logs, Tempo for traces, Grafana for visualization, Alloy as the unified collector/exporter.
- **Analytics:** Python 3 scripts (`get_prom.py`, `get_loki.py`, `rca_analysis.py`), `pandas`, `scikit-learn` IsolationForest, rule-based RCA suggestions, JSON reporting.
- **Repository layout:** `services/` (Java services), `ops/logs` and `ops/metrics` (captured telemetry), `docs/` (dashboards, diagrams), `aiops_report.json` (latest report artifact).

## Setting Up Monitoring Infrastructure
Ensure Docker Desktop is running, then bring up the monitoring stack plus microservices:
```bash
docker-compose up
```

## Service & Observability Endpoints
- Accounts Swagger UI -> http://localhost:8080/swagger-ui.html
- Cards Swagger UI -> http://localhost:9000/swagger-ui.html
- Eureka dashboard -> http://localhost:8070
- Gateway edge entrypoint -> http://localhost:8072/
- Prometheus query UI -> http://localhost:9090
- Grafana dashboards -> http://localhost:3000

## Workflow
1. **Metric collection (`get_prom.py`)** - Calls the Prometheus HTTP API with service-specific PromQL templates (error rate, P95 latency, CPU, JVM heap, HikariCP activity). Results are written to `ops/metrics/<service>.txt`, preserving query metadata and sampled datapoints.
2. **Log collection (`get_loki.py`)** - Streams Loki results per service with pagination, writes normalized log text files under `ops/logs/`, and records the query window, selector, and tenant headers for traceability.
3. **Anomaly detection & RCA (`rca_analysis.py`)** - Parses structured logs (defaults to `mock_logs.txt` but can ingest merged Loki exports), removes noise, encodes features, and runs an `IsolationForest(contamination=0.08)` to flag anomalies. The script enriches each anomaly with heuristic suggestions and emits `aiops_report.json` summarizing counts, top errors, and per-trace context.
4. **Visualization** - Grafana dashboards (referenced in `/docs`) overlay the same Prometheus/Loki/Tempo signals for human validation next to the generated JSON report.

## Example Output
```json
{
  "summary": {
    "anomaly_count": 51,
    "top_errors": [
      {
        "message": "Could not locate PropertySource: I/O error on GET request for \"http://localhost:8071/accounts/default\": Connection refused",
        "count": 25
      },
      {
        "message": "HHH90000025: H2Dialect does not need to be specified explicitly",
        "count": 13
      },
      {
        "message": "OOM killer invoked for java PID 1 reason=oom_kill",
        "count": 13
      }
    ]
  },
  "anomalies": [
    {
      "timestamp": "2025-11-12 12:03:52.545000",
      "service": "accounts",
      "level": "ERROR",
      "message": "OOM killer invoked for java PID 1 reason=oom_kill",
      "trace_id": "7e8e80e952eb9d8e96cf37cb990c801f",
      "suggestion": "accounts: Review logs for deeper context"
    },
    {
      "timestamp": "2025-11-12 12:04:11.918000",
      "service": "accounts",
      "level": "WARN",
      "message": "Could not locate PropertySource: I/O error on GET request for \"http://localhost:8071/accounts/default\": Connection refused",
      "trace_id": "eb0d1cb7c2b70a3a4419f4fe020864d3",
      "suggestion": "accounts: Investigate DB or network connection stability"
    }
  ]
}
```

## How to Run
```bash
# 1) collect metrics (outputs to ops/metrics)
python get_prom.py

# 2) collect logs from Loki (outputs to ops/logs)
python get_loki.py

# 3) run anomaly detection + RCA (reads mock_logs.txt, writes aiops_report.json)
python rca_analysis.py
```