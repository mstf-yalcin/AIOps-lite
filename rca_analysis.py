import re
import json
import pandas as pd
from datetime import datetime
from sklearn.ensemble import IsolationForest

log_file = "mock_logs.txt"

pattern = re.compile(
    r'(?P<timestamp>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+)Z\s'
    r'(?P<level>[A-Z]+)\s\[(?P<service>[^,]+),(?P<trace_id>[^,]+),(?P<span_id>[^\]]+)\]\s.*?'
    r'(?P<class>[a-zA-Z0-9_.]+)\s*:\s(?P<message>.*)'
)

records = []
with open(log_file, "r", encoding="utf-8") as f:
    for line in f:
        m = pattern.search(line)
        if not m:
            continue
        d = m.groupdict()
        d["timestamp"] = datetime.fromisoformat(d["timestamp"].replace("Z", "+00:00"))
        records.append(d)

df = pd.DataFrame(records)
df.sort_values("timestamp", inplace=True)

if df.empty:
    raise ValueError("No valid log entries parsed — check your log format!")

ignore_patterns = [
    "completed initialization",
    "application started",
    "service ready",
    "server started",
    "started successfully",
]
df = df[~df["message"].str.lower().apply(lambda msg: any(pat in msg for pat in ignore_patterns))]
df = df[df["level"] != "INFO"]

if df.empty:
    print("All logs are informational — nothing suspicious found.")
    exit()

df["message_len"] = df["message"].apply(len)
df["service_encoded"] = df["service"].astype("category").cat.codes
df["level_score"] = df["level"].map({
    "DEBUG": 1, "INFO": 2, "WARN": 3, "WARNING": 3, "ERROR": 4, "CRITICAL": 5
}).fillna(0)

model = IsolationForest(contamination=0.08, random_state=42)
df["anomaly_flag"] = model.fit_predict(df[["message_len", "level_score", "service_encoded"]])
df["is_anomaly"] = df["anomaly_flag"].apply(lambda x: "Anomaly" if x == -1 else "Normal")


rca_records = []
for trace_id, group in df.groupby("trace_id"):
    anomalies = group[group["anomaly_flag"] == -1]
    if len(anomalies) > 0:
        root_cause_service = anomalies.iloc[0]["service"]
        rca_records.append({
            "trace_id": trace_id,
            "root_cause_service": root_cause_service,
            "affected_services": list(group["service"].unique())
        })
rca_df = pd.DataFrame(rca_records)
 
def suggest_fix(service, message):
    msg = message.lower()
    if "failed to retrieve customer details" in msg:
        return f"{service}: Check DB connection or downstream customer API"
    if "timeout" in msg:
        return f"{service}: Increase timeout or inspect slow dependencies"
    if "nomapping" in msg or "page not found" in msg:
        return f"{service}: Verify controller endpoint or routing config"
    if "emailbatch" in msg:
        return f"{service}: Check notification queue or mail server"
    if "jta" in msg or "transaction" in msg:
        return f"{service}: Review transaction boundaries or DB locks"
    if "connection" in msg:
        return f"{service}: Investigate DB or network connection stability"
    if "exception" in msg:
        return f"{service}: Check stack trace and root exception"
    if "database" in msg or "query" in msg:
        return f"{service}: Review DB performance or slow queries"
    return f"{service}: Review logs for deeper context"

df["suggestion"] = df.apply(lambda x: suggest_fix(x["service"], x["message"]), axis=1)

anomalies = df[df["is_anomaly"] == "Anomaly"]

if anomalies.empty:
    print("No anomalies detected.")
    report = {
        "summary": {"anomaly_count": 0},
        "anomalies": []
    }
else:
    top_errors = (
        anomalies.groupby("message")["trace_id"]
        .count()
        .sort_values(ascending=False)
        .reset_index()
        .rename(columns={"trace_id": "count"})
    )

    anomaly_list = [
        {
            "timestamp": str(row.timestamp),
            "service": row.service,
            "level": row.level,
            "message": row.message,
            "trace_id": row.trace_id,
            "suggestion": row.suggestion
        }
        for _, row in anomalies.iterrows()
    ]

    report = {
        "summary": {
            "anomaly_count": len(anomalies),
            "top_errors": top_errors.head(10).to_dict(orient="records")
        },
        "anomalies": anomaly_list
    }

with open("aiops_report.json", "w", encoding="utf-8") as f:
    json.dump(report, f, indent=4, ensure_ascii=False)

print("\nAIOps JSON report created: aiops_report.json")
print(f"Total anomalies detected: {report['summary'].get('anomaly_count', 0)}")