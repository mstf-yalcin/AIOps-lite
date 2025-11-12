import argparse
import os
import time
from datetime import datetime, timezone
import requests

TENANT_ID = "tenant1"
API_PREFIX = "/loki/api/v1"
DEFAULT_SERVICES = ["accounts-ms", "loans-ms", "cards-ms", "gatewayserver-ms", "eurekaserver-ms"]
MAX_LIMIT = 5000

LOKI_ENDPOINTS = ["http://localhost:3100"]


def _session():
    session = requests.Session()
    session.headers.update({"X-Scope-OrgID": TENANT_ID, "Accept": "application/json"})
    return session


def _api(base, path):
    return f"{base.rstrip('/')}{API_PREFIX}{path}"


def _iso_ns(ns):
    return datetime.fromtimestamp(ns / 1e9, tz=timezone.utc).isoformat()


def _load_services(cli_services: str | None):
    if cli_services:
        return [value.strip() for value in cli_services.split(",") if value.strip()]
    if os.path.exists("services.txt"):
        with open("services.txt", "r", encoding="utf-8") as file:
            return [line.strip() for line in file if line.strip() and not line.strip().startswith("#")]
    return DEFAULT_SERVICES


def _fetch_batch(base, selector, start_ns, end_ns, limit=MAX_LIMIT, direction="forward"):
    session = _session()
    url = _api(base, "/query_range")
    params = {
        "query": selector,
        "start": start_ns,
        "end": end_ns,
        "limit": limit,
        "direction": direction,
    }
    response = session.get(url, params=params, timeout=30)
    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        print(f"[ERR] {selector} -> HTTP {response.status_code} body[:300]: {response.text[:300]}")
        raise exc

    data = response.json().get("data", {}).get("result", [])
    rows = []
    last_ts = None
    for stream in data:
        for ts, line in stream.get("values", []):
            ts_int = int(ts)
            rows.append((ts_int, line))
            if last_ts is None or ts_int > last_ts:
                last_ts = ts_int
    return rows, last_ts


def fetch_all_with_pagination(base, selector, start_ns, end_ns, out_path):
    total = 0
    current_start = start_ns

    with open(out_path, "w", encoding="utf-8") as out_file:
        out_file.write(f"# LOKI_BASE={base} TENANT={TENANT_ID}\n")
        out_file.write(f"# SELECTOR={selector}\n")
        out_file.write(f"# RANGE={_iso_ns(start_ns)}..{_iso_ns(end_ns)} UTC\n\n")

        while True:
            rows, last_ts = _fetch_batch(base, selector, current_start, end_ns, limit=MAX_LIMIT)
            if not rows:
                break

            rows.sort(key=lambda item: item[0])
            for ts, line in rows:
                out_file.write(f"{_iso_ns(ts)}\t{line}\n")
            total += len(rows)

            if last_ts is None:
                break
            next_start = last_ts + 1
            if next_start <= current_start:
                break
            if next_start >= end_ns:
                break
            current_start = next_start

    return total


def main():
    parser = argparse.ArgumentParser(description="Fetch Loki logs per service into paginated text files.")
    parser.add_argument("--window", type=int, default=900, help="Window size in seconds (default 900 = 15 minutes).")
    parser.add_argument("--services", type=str, help="Comma separated service list (e.g. accounts-ms,loans-ms).")
    parser.add_argument("--label", type=str, default="container", help='Loki label name (e.g. "container" or "app").')
    parser.add_argument("--outdir", type=str, default=os.path.join("ops", "logs"), help="Output directory.")
    parser.add_argument("--filter", type=str, default="", help='Optional LogQL pipeline (e.g. |~ "(WARN|ERROR)").')
    args = parser.parse_args()

    services = _load_services(args.services)
    os.makedirs(args.outdir, exist_ok=True)

    base = LOKI_ENDPOINTS[0]
    print(f"[LOKI] using base: {base}")
    end_ns = int(time.time() * 1e9)
    start_ns = end_ns - args.window * 1_000_000_000

    print(f"[WIN] range: {_iso_ns(start_ns)} .. {_iso_ns(end_ns)} (UTC), window={args.window}s")
    print(f"[CFG] label={args.label} services={services} filter={args.filter!r}")

    total_lines_all = 0
    for svc in services:
        selector = f'{{{args.label}="{svc}"}}'
        if args.filter.strip():
            selector = f"{selector} {args.filter.strip()}"
        out_path = os.path.join(args.outdir, f"{svc}.txt")
        try:
            count = fetch_all_with_pagination(base, selector, start_ns, end_ns, out_path)
            total_lines_all += count
            print(f"[OK] {svc}: {count} lines -> {os.path.abspath(out_path)}")
        except Exception as exc:
            with open(out_path, "w", encoding="utf-8") as out_file:
                out_file.write(f"# ERROR fetching logs for {svc}\n# {exc}\n")
            print(f"[ERR] {svc}: {exc} (see {out_path})")

    print(f"\n[FIN] Completed. Total lines: {total_lines_all}. Directory: {os.path.abspath(args.outdir)}")


if __name__ == "__main__":
    main()
