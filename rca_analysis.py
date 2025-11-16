import re
import json
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

def generate_suggestions(row):
    suggestions = []
    msg_lower = row.get("message", "").lower()
    service = row.get("service", "unknown")

    # 1. Specific Log Message Analysis (OOM)
    if "oom" in msg_lower or "outofmemory" in msg_lower:
        heap_ratio = row.get("jvm_heap_usage_ratio", 0)
        if heap_ratio > 0.85:
            suggestions.append(
                f"{service}: OOM detected in log and JVM heap usage is high ({heap_ratio:.2f}). Investigate for memory leaks or consider increasing heap size (-Xmx)."
            )
        else:
            suggestions.append(
                f"{service}: OOM detected in log, but JVM heap usage ({heap_ratio:.2f}) is not critical. This could be a container-level OOM or native memory issue. Check container memory limits and process RSS."
            )

    # 2. Generic Metric Threshold Heuristics (based on exceedance features)
    if row.get("latency_p95_ms_exceedance", 0) > 0:
        suggestions.append(
            f"{service}: High P95 latency detected ({row.get('latency_p95_ms'):.0f}ms)."
        )
    if row.get("cpu_usage_exceedance", 0) > 0:
        suggestions.append(
            f"{service}: High CPU usage detected ({row.get('cpu_usage'):.2f})."
        )
    if row.get("jvm_heap_usage_ratio_exceedance", 0) > 0 and "oom" not in msg_lower:
        suggestions.append(
            f"{service}: High JVM heap usage detected ({row.get('jvm_heap_usage_ratio'):.2f})."
        )
    if row.get("error_rate_exceedance", 0) > 0:
        suggestions.append(
            f"{service}: Elevated error rate detected ({row.get('error_rate'):.3f})."
        )
    if row.get("hikaricp_active_exceedance", 0) > 0:
        suggestions.append(
            f"{service}: Database connection pool is nearing exhaustion ({row.get('hikaricp_active'):.0f} active connections)."
        )

    if not suggestions:
        if "timeout" in msg_lower:
            suggestions.append(f"{service}: A timeout was reported. Investigate slow dependencies or increase timeout settings.")
        elif "connection" in msg_lower and "refused" in msg_lower:
            suggestions.append(f"{service}: Connection was refused. Check if the downstream service is running and accessible, and verify firewall rules.")
        elif "exception" in msg_lower:
            suggestions.append(f"{service}: An unhandled exception occurred. Review the full stack trace for details.")
        else:
            suggestions.append(f"{service}: Review logs and correlated metrics for deeper context.")

    return suggestions

def main():
    input_file = "correlated_data.csv"
    try:
        df = pd.read_csv(input_file, parse_dates=["timestamp"])
        df.sort_values("timestamp", inplace=True)
    except FileNotFoundError:
        print(f"Error: Input file '{input_file}' not found. Please run prepare_data.py first.")
        return

    if df.empty:
        raise ValueError("No valid log entries parsed — check your log format!")

    df['message'] = df['message'].fillna('').astype(str)

    ignore_patterns = [
        "completed initialization",
        "application started",
        "service ready",
        "server started",
        "started successfully",
    ]
    df = df[~df["message"].str.lower().str.contains('|'.join(ignore_patterns))]
    df = df[df["level"] != "INFO"]

    if df.empty:
        print("All logs are informational — nothing suspicious found.")
        report = {
            "summary": {"anomaly_count": 0, "top_errors": []},
            "anomalies": []
        }
        with open("aiops_report.json", "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print("\nAIOps JSON report created: aiops_report.json")
        print("Total anomalies detected: 0")
        return

    # thresholds for key metrics.
    THRESHOLDS = {
        "latency_p95_ms": 1000,
        "cpu_usage": 0.85,
        "error_rate": 0.10,
        "jvm_heap_usage_ratio": 0.85,
        "hikaricp_active": 9,
    }

    # Define features for the model
    log_features = ["message_len", "level_score", "service_encoded"]
    metric_features = [
        "cpu_usage", "error_rate", "hikaricp_active",
        "jvm_heap_used_bytes", "jvm_heap_max_bytes", "latency_p95_ms", "throughput_requests_per_second"
    ]

    # Create log-based features
    df["message_len"] = df["message"].str.len()
    df["service_encoded"] = df["service"].astype("category").cat.codes
    df["level_score"] = df["level"].map({
        "DEBUG": 1, "INFO": 2, "WARN": 3, "WARNING": 3, "ERROR": 4, "CRITICAL": 5
    }).fillna(0)

    exceedance_features = []
    df["jvm_heap_usage_ratio"] = df["jvm_heap_used_bytes"] / (df["jvm_heap_max_bytes"] + 1e-9)
    df["jvm_heap_usage_ratio"] = df["jvm_heap_usage_ratio"].fillna(0)
    for metric, threshold in THRESHOLDS.items():
        exceedance_col = f"{metric}_exceedance"
        df[exceedance_col] = (df[metric] - threshold).clip(lower=0)
        exceedance_features.append(exceedance_col)

    behavioral_features = []
    epsilon = 1e-6 
    throughput = df["throughput_requests_per_second"] + epsilon
    df["cpu_per_request"] = df["cpu_usage"] / throughput
    df["latency_per_request"] = df["latency_p95_ms"] / throughput
    df["jvm_heap_per_request"] = df["jvm_heap_used_bytes"] / throughput
    behavioral_features.extend(["cpu_per_request", "latency_per_request", "jvm_heap_per_request"])

    # Combine all features for the model
    features = log_features + metric_features + exceedance_features + behavioral_features
    for col in features:
        if col not in df.columns:
            df[col] = 0
    df[features] = df[features].fillna(0)

    # --- Model Training ---
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(df[features])
    model = IsolationForest(contamination=0.08, random_state=42)
    model.fit(X_scaled)
    df["anomaly_score"] = -model.decision_function(X_scaled)
    df["anomaly_flag"] = model.predict(X_scaled)
    df["is_anomaly"] = df["anomaly_flag"].apply(lambda x: "Anomaly" if x == -1 else "Normal")

    # --- Report Generation ---
    rca_records = []
    anomalies = df[df["is_anomaly"] == "Anomaly"].copy()

    if not anomalies.empty:
        for trace_id, group in anomalies.groupby("trace_id"):
            worst = group.sort_values("anomaly_score", ascending=False).iloc[0]
            svc = worst.get("service", "unknown")
            all_services_in_trace = list(df[df['trace_id'] == trace_id]["service"].unique())
            suggestions = generate_suggestions(worst)
            snapshot = {c: worst[c] for c in metric_features if c in worst.index and pd.notna(worst[c])}
            
            rca_records.append({
                "trace_id": trace_id,
                "root_cause_service": svc,
                "timestamp": str(worst["timestamp"]),
                "message": worst.get("message", ""),
                "anomaly_score": float(worst.get("anomaly_score", 0.0)),
                "metric_snapshot": snapshot,
                "suggestions": suggestions,
                "affected_services": all_services_in_trace
            })

    # --- Build and write the final JSON report ---
    if not anomalies.empty:
        top_errors = (
            anomalies.groupby("message")["trace_id"]
            .count()
            .sort_values(ascending=False)
            .reset_index()
            .rename(columns={"trace_id": "count"})
        )
    else:
        top_errors = pd.DataFrame(columns=["message", "count"])

    report = {
        "summary": {
            "anomaly_count": int(len(anomalies)),
            "top_errors": top_errors.head(10).to_dict(orient="records")
        },
        "anomalies": rca_records
    }

    with open("aiops_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print("\nAIOps JSON report created: aiops_report.json")
    print(f"Total anomalies detected: {report['summary'].get('anomaly_count', 0)}")

if __name__ == "__main__":
    main()