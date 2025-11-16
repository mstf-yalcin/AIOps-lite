import re
import pandas as pd
from datetime import datetime

log_file = "mock_logs.txt"
metric_file = "mock_metrics.txt"
output_file = "correlated_data.csv"

def load_logs(file_path):
    log_pattern = re.compile(
        r'(?P<timestamp>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+)Z\s'
        r'(?P<level>[A-Z]+)\s\[(?P<service>[^,]+),(?P<trace_id>[^,]+),(?P<span_id>[^\]]+)\]\s.*?'
        r'(?P<class>[a-zA-Z0-9_.]+)\s*:\s(?P<message>.*)'
    )
    
    log_records = []
    current_log_record = None
    total_lines = 0

    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            total_lines += 1
            line = line.strip()
            if not line:
                continue

            match = log_pattern.search(line)
            
            if match:
                if current_log_record:
                    log_records.append(current_log_record)
                
                current_log_record = match.groupdict()
            else:
                if current_log_record:
                    current_log_record['message'] += f" | {line}"

    if current_log_record:
        log_records.append(current_log_record)

    print(f"Total lines in log file: {total_lines}")
    print(f"Number of main log records after merging multi-line entries: {len(log_records)}")

    df_logs = pd.DataFrame(log_records)
    if not df_logs.empty:
        df_logs["timestamp"] = pd.to_datetime(df_logs["timestamp"], utc=True)
        df_logs.sort_values("timestamp", inplace=True)
    return df_logs

def load_metrics(file_path):
    """Parses the custom metric file format into a pivoted pandas DataFrame."""
    records = []
    current_metric = None
    current_service = None
    service_pattern = re.compile(r'service="([^"]+)"')

    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("## METRIC:"):
                current_metric = line.split(":")[1].strip()
                continue
            if line.startswith("## PROMQL:"):
                service_match = service_pattern.search(line)
                if service_match:
                    current_service = service_match.group(1)
                continue
            
            if not line.strip() or line.startswith("#") or not current_metric or not current_service:
                continue

            parts = line.strip().split('\t')
            if len(parts) == 2:
                timestamp_str, value = parts
                records.append([timestamp_str, current_service, current_metric, float(value)])

    if not records:
        return pd.DataFrame()

    metrics_df = pd.DataFrame(records, columns=["timestamp", "service", "metric", "value"])
    metrics_df["timestamp"] = pd.to_datetime(metrics_df["timestamp"], utc=True)
    
    pivoted_df = metrics_df.pivot_table(index=["timestamp", "service"], columns="metric", values="value").reset_index()
    pivoted_df.sort_values("timestamp", inplace=True)
    return pivoted_df

def merge_data(df_logs, df_metrics):
    """Merges log and metric DataFrames using time-based correlation."""
    if df_metrics.empty:
        print("Warning: Metric data is empty. Returning logs only.")
        return df_logs
    
    merged_df = pd.merge_asof(
        left=df_logs,
        right=df_metrics,
        on="timestamp",
        by="service",
        direction="nearest",
        tolerance=pd.Timedelta("15s")
    )
    
    metric_cols = df_metrics.columns.drop(['timestamp', 'service'], errors='ignore')
    merged_df[metric_cols] = merged_df[metric_cols].fillna(0)
    
    return merged_df

def main():
    print("Loading and parsing log data...")
    df_logs = load_logs(log_file)
    
    if df_logs.empty:
        print("Error: Log file is empty or no lines could be parsed. Data preparation stopped.")
    else:
        print("\nLoading metric data...")
        df_metrics = load_metrics(metric_file)
        
        print("\nMerging data...")
        df_correlated = merge_data(df_logs, df_metrics)
        
        print(f"\nSaving correlated data to '{output_file}'...")
        df_correlated.to_csv(output_file, index=False)
        
        print("\nFirst 5 rows of correlated data:")
        print(df_correlated.head())
        print(f"\nTotal {len(df_correlated)} rows saved to '{output_file}'.")

if __name__ == "__main__":
    main()

