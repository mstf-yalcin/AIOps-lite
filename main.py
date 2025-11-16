# main.py
"""
Main orchestrator script for the AIOps RCA pipeline.

This script runs all four main stages of the pipeline in sequence:
1. Data Fetching (Logs): Fetches logs from the data source (Loki).
2. Data Fetching (Metrics): Fetches metrics from the data source (Prometheus).
3. Data Preparation: Loads, parses, and correlates log and metric data.
4. RCA Analysis: Analyzes the correlated data to find anomalies and generate a report.
"""

import sys
import time

try:
    import get_loki
except ImportError:
    print("Error: 'get_loki.py' could not be imported. Make sure it exists and required libraries (e.g., requests) are installed.")
    sys.exit(1)

try:
    import get_prom
except ImportError:
    print("Error: 'get_prom.py' could not be imported. Make sure it exists and required libraries (e.g., requests) are installed.")
    sys.exit(1)

try:
    import prepare_data
except ImportError:
    print("Error: 'prepare_data.py' could not be imported. Make sure it exists and required libraries (e.g., pandas) are installed.")
    sys.exit(1)

try:
    import rca_analysis
except ImportError:
    print("Error: 'rca_analysis.py' could not be imported. Make sure it exists and required libraries (e.g., pandas, scikit-learn) are installed.")
    sys.exit(1)


def run_pipeline():
    print("=========================================")
    print("  AIOps Anomaly Detection Pipeline Start ")
    print("=========================================\n")
    
    # --- Step 1: Fetch Logs ---
    start_time = time.time()
    print("--- Step 1: Fetching logs ---")
    try:
        get_loki.main() 
        duration = time.time() - start_time
        print(f"--- Step 1 finished in {duration:.2f} seconds. ---\n")
    except Exception as e:
        print(f"!!! ERROR in Step 1 (get_loki): {e} !!!")
        print("Pipeline stopped. Please ensure data source is running or mock data is available.")
        return

    # --- Step 2: Fetch Metrics ---
    start_time = time.time()
    print("--- Step 2: Fetching metrics ---")
    try:
        get_prom.main()
        duration = time.time() - start_time
        print(f"--- Step 2 finished in {duration:.2f} seconds. ---\n")
    except Exception as e:
        print(f"!!! ERROR in Step 2 (get_prom): {e} !!!")
        print("Pipeline stopped. Please ensure data source is running or mock data is available.")
        return

    # --- Step 3: Data Preparation ---
    start_time = time.time()
    print("--- Step 3: Preparing and correlating data ---")
    try:
        prepare_data.main()
        duration = time.time() - start_time
        print(f"--- Step 3 finished in {duration:.2f} seconds. ---\n")
    except Exception as e:
        print(f"!!! ERROR in Step 3 (prepare_data): {e} !!!")
        print("Pipeline stopped.")
        return

    # --- Step 4: RCA Analysis ---
    start_time = time.time()
    print("--- Step 4: Running RCA analysis ---")
    try:
        rca_analysis.main()
        duration = time.time() - start_time
        print(f"--- Step 4 finished in {duration:.2f} seconds. ---\n")
    except Exception as e:
        print(f"!!! ERROR in Step 4 (rca_analysis): {e} !!!")
        print("Pipeline stopped.")
        return

    print("===========================================")
    print("  Report is ready at aiops_report.json   ")
    print("===========================================")

if __name__ == "__main__":
    run_pipeline()
