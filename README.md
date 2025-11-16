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
- **Analytics:** Python 3 scripts (`get_prom.py`, `get_loki.py`, `prepare_data.py`, `rca_analysis.py`), `pandas`, `scikit-learn` IsolationForest, multi-layered RCA suggestions, JSON reporting.
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
The entire AIOps pipeline is orchestrated by `main.py` and follows these steps:

1. **Data Collection ('get_loki.py' & 'get_prom.py')**:
- `get_loki.py`: Fetches log data from Loki, writing it to `ops/logs/<service>.txt`.
- `get_prom.py`: Fetches metric data from Prometheus-compatible sources, writing it to `ops/metrics/<service>.txt.`
2. **Data Preparation (`prepare_data.py`)** - Reads the collected raw log and metric files, performs time-based correlation to align log entries with their corresponding metric snapshots, and outputs a unified `correlated_data.csv`.
3. **Anomaly detection & RCA (`rca_analysis.py`)** - Reads the `correlated_data.csv` (prepared in the previous step), applies multi-layered feature, trains an `IsolationForest` ML model to detect and rank anomalies. The script then generates suggestion, metric-aware RCA suggestions for each anomaly and emits `aiops_report.json` summarizing counts, top errors, and detailed per-trace context.
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
      "trace_id": "01c84ac0ffdc270cf3ba9c12ba2e9651",
      "root_cause_service": "accounts",
      "timestamp": "2025-11-12 12:06:57.181000+00:00",
      "message": "cardStatus method start | Hibernate: select t1_0.txn_id,t1_0.amount,t1_0.status,t1_0.txn_at from transaction t1_0 where t1_0.account_nbr in (?) | Hibernate: select c1_0.customer_id,c1_0.created_at,c1_0.created_by,c1_0.email,c1_0.mobile_number,c1_0.name,c1_0.updated_at,c1_0.updated_by from customer c1_0 where c1_0.mobile_number=?",
      "anomaly_score": 0.11903998515966818,
      "metric_snapshot": {
        "cpu_usage": 0.95,
        "error_rate": 0.25,
        "hikaricp_active": 2.5,
        "jvm_heap_used_bytes": 1000000000.0,
        "jvm_heap_max_bytes": 1000000000.0,
        "latency_p95_ms": 800.0,
        "throughput_requests_per_second": 1.0
      },
      "suggestions": [
        "accounts: High CPU usage detected (0.95).",
        "accounts: High JVM heap usage detected (1.00).",
        "accounts: Elevated error rate detected (0.250)."
      ],
      "affected_services": [
        "accounts"
      ]
    },
    {
      "trace_id": "17408d946a7c7fa8ffe5b54f511210d4",
      "root_cause_service": "accounts",
      "timestamp": "2025-11-12 12:04:42.197000+00:00",
      "message": "supportCase method start | Hibernate: select a1_0.account_number,a1_0.account_type,a1_0.branch_address,a1_0.created_at,a1_0.created_by,a1_0.customer_id,a1_0.updated_at,a1_0.updated_by from accounts a1_0 where a1_0.customer_id=? | Hibernate: select c1_0.customer_id,c1_0.created_at,c1_0.created_by,c1_0.email,c1_0.mobile_number,c1_0.name,c1_0.updated_at,c1_0.updated_by from customer c1_0 where c1_0.mobile_number=?",
      "anomaly_score": 0.03946812169383174,
      "metric_snapshot": {
        "cpu_usage": 0.11,
        "error_rate": 0.14,
        "hikaricp_active": 9.5,
        "jvm_heap_used_bytes": 508000000.0,
        "jvm_heap_max_bytes": 1000000000.0,
        "latency_p95_ms": 2200.0,
        "throughput_requests_per_second": 10.3
      },
      "suggestions": [
        "accounts: High P95 latency detected (2200ms).",
        "accounts: Elevated error rate detected (0.140).",
        "accounts: Database connection pool is nearing exhaustion (10 active connections)."
      ],
      "affected_services": [
        "accounts"
      ]
    },
  ]
}
```

## How to Run

### 1. Installation
First, install the necessary Python libraries from the `requirements.txt` file. It is recommended to do this in a virtual environment.
```bash
pip install -r requirements.txt
```

### 2. Execution
Run the main orchestrator script. This will execute the entire data preparation and analysis pipeline using the mock data provided in the repository.
```bash
python main.py
```
The script will print its progress for each step and, upon completion, generate two key files:
- `correlated_data.csv`: The intermediate dataset containing logs and their correlated metrics.
- `aiops_report.json`: The final analysis report.