import os, time, argparse, requests
from datetime import datetime, timezone

PROM_URL   = "http://localhost:9090"
OUTPUT_DIR = "ops/metrics"
DEFAULT_SERVICES = ["accounts-ms", "loans-ms", "cards-ms", "gatewayserver-ms", "eurekaserver-ms"]

METRICS = {
    "error_rate": r'rate(http_server_requests_seconds_count{{{label}="{svc}",status=~"5.."}}[5m])',
    "latency_p95_ms": r'histogram_quantile(0.95, sum by (le)(rate(http_server_requests_seconds_bucket{{{label}="{svc}"}}[5m]))) * 1000',
    "cpu_seconds_rate": r'rate(process_cpu_seconds_total{{{label}="{svc}"}}[5m])',
    "jvm_heap_used_bytes": r'jvm_memory_used_bytes{{{label}="{svc}",area="heap"}}',
    "hikaricp_active": r'hikaricp_connections_active{{{label}="{svc}"}}',
}

def _iso(s: int) -> str:
    return datetime.fromtimestamp(s, tz=timezone.utc).isoformat()

def _load_services(cli_services: str | None):
    if cli_services:
        return [x.strip() for x in cli_services.split(",") if x.strip()]
    path = "services.txt"
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return [ln.strip() for ln in f if ln.strip() and not ln.strip().startswith("#")]
    return DEFAULT_SERVICES

def query_range(prom_url: str, promql: str, start_s: int, end_s: int, step_s: int):
    url = f"{prom_url.rstrip('/')}/api/v1/query_range"
    params = {"query": promql, "start": start_s, "end": end_s, "step": step_s}
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    data = r.json().get("data", {}).get("result", [])
    series = []
    for item in data:
        metric_labels = item.get("metric", {})
        values = [(int(float(ts)), float(val)) for ts, val in item.get("values", [])]
        series.append((metric_labels, values))
    return series

def main():
    ap = argparse.ArgumentParser(description="Fetch service-based metrics from Prometheus")
    ap.add_argument("--window", type=int, default=900, help="Time window (seconds) - default 900 = 15 min")
    ap.add_argument("--step", type=int, default=60, help="Sampling step (seconds)")
    ap.add_argument("--services", type=str, help="Comma-separated service list (e.g. accounts-ms,loans-ms)")
    ap.add_argument("--label", type=str, default="service", help='Service label name (e.g. "service", "container", "app")')
    ap.add_argument("--outdir", type=str, default=OUTPUT_DIR, help="Output directory")
    ap.add_argument("--prom", type=str, default=PROM_URL, help="Prometheus base URL")
    args = ap.parse_args()

    services = _load_services(args.services)
    os.makedirs(args.outdir, exist_ok=True)

    end_s = int(time.time())
    start_s = end_s - args.window

    print(f"[PROM] base={args.prom} window={_iso(start_s)}..{_iso(end_s)} step={args.step}s")
    print(f"[CFG]  label={args.label} services={services}")

    total_points = 0
    for svc in services:
        out_path = os.path.join(args.outdir, f"{svc}.txt")
        with open(out_path, "w", encoding="utf-8") as out:
            out.write(f"# PROM_URL={args.prom}\n")
            out.write(f"# SERVICE={svc}\n")
            out.write(f"# RANGE={_iso(start_s)}..{_iso(end_s)} UTC STEP={args.step}s\n\n")

            for name, tmpl in METRICS.items():
                promql = tmpl.format(label=args.label, svc=svc)
                try:
                    series = query_range(args.prom, promql, start_s, end_s, args.step)
                    out.write(f"## METRIC: {name}\n")
                    out.write(f"## PROMQL: {promql}\n")
                    if not series:
                        out.write(f"# (no data)\n\n")
                        continue

                    for idx, (labels, values) in enumerate(series, start=1):
                        extra = {k: v for k, v in labels.items() if k != args.label}
                        if extra:
                            out.write(f"# SERIES {idx} LABELS: {extra}\n")
                        for ts, val in values:
                            out.write(f"{_iso(ts)}\t{val}\n")
                        out.write("\n")
                        total_points += len(values)

                except Exception as e:
                    out.write(f"## METRIC: {name}\n")
                    out.write(f"## PROMQL: {promql}\n")
                    out.write(f"## ERROR: {e}\n\n")
                    print(f"[ERR] {svc}/{name}: {e}")

        print(f"[OK] {svc}: written to → {os.path.abspath(out_path)}")

    print(f"\n Done. Total data points: {total_points}. Directory: {os.path.abspath(args.outdir)}")

if __name__ == "__main__":
    main()