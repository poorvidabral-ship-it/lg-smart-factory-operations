"""
LG Smart Factory — Live Simulator (Phase 2.2 — CSV Safe Version)
Writes to a CSV file instead of xlsx to avoid Windows file lock / zip corruption.
"""

import pandas as pd
import random
import time
import os
import sys

XLSX_PATH = "datalg2/production.csv.xlsx"   # original — read ONCE at start
CSV_PATH  = "datalg2/production_live.csv"   # live file — dashboard reads this

MACHINE_STATUSES = [
    "Running", "Running", "Running",
    "Maintenance",
    "Breakdown Risk"
]

def simulate_tick(df):
    n_changes = random.randint(1, 3)
    indices   = random.sample(range(len(df)), min(n_changes, len(df)))

    for idx in indices:
        spike = random.random() < 0.15
        df.loc[idx, "Downtime_min"] = (
            random.randint(35, 60) if spike else random.randint(3, 22)
        )
        dip    = random.random() < 0.12
        target = df.loc[idx, "Target"]
        df.loc[idx, "Actual"] = int(
            target * random.uniform(0.58, 0.76) if dip
            else target * random.uniform(0.88, 1.08)
        )
        df.loc[idx, "Machine_Status"] = random.choice(MACHINE_STATUSES)
    return df

def safe_csv_write(df, path):
    """Write to temp then rename — atomic on Windows."""
    tmp = path + ".tmp"
    df.to_csv(tmp, index=False)
    if os.path.exists(path):
        os.remove(path)
    os.rename(tmp, path)

def main():
    if not os.path.exists(XLSX_PATH):
        print(f"[ERROR] Cannot find {XLSX_PATH}")
        print('Run from: "C:\\Users\\poorv\\New folder (2)"')
        sys.exit(1)

    print("=" * 58)
    print("  LG Smart Factory — Live Simulator")
    print("=" * 58)
    print(f"  Source : {XLSX_PATH}")
    print(f"  Live   : {CSV_PATH}")
    print(f"  Tick   : every 30 seconds")
    print(f"  Stop   : Ctrl+C")
    print("=" * 58)

    # Load original xlsx ONCE as base
    base_df = pd.read_excel(XLSX_PATH)
    base_df.columns = base_df.columns.str.strip()
    df = base_df.copy()

    # Write initial live file
    safe_csv_write(df, CSV_PATH)
    print("  Initial live file created.")

    tick = 0
    while True:
        try:
            tick += 1
            df = simulate_tick(df)
            safe_csv_write(df, CSV_PATH)

            health        = round((df["Actual"].sum() / df["Target"].sum()) * 100, 1)
            avg_dt        = round(df["Downtime_min"].mean(), 1)
            breakdown_cnt = (df["Machine_Status"] == "Breakdown Risk").sum()

            icon = "🟢" if health >= 90 else ("🟡" if health >= 75 else "🔴")
            print(f"  #{tick:04d} | {icon} Health {health:6.1f}% | "
                  f"DT {avg_dt:5.1f} min | Breakdown {breakdown_cnt}")

            time.sleep(30)

        except KeyboardInterrupt:
            print("\n  Simulator stopped.")
            break
        except Exception as e:
            print(f"  [WARN] Tick #{tick} — {e}")
            time.sleep(30)

if __name__ == "__main__":
    main()