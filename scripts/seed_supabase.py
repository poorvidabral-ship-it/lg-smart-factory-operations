"""
Seed Supabase from Excel.
Uses actual table column definitions from the SQL schema.
Run: py scripts/seed_supabase.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import pandas as pd
from modules.database import get_supabase

BASE = "datalg2"

# Actual columns per the CREATE TABLE SQL that was run in Supabase
TABLE_COLUMNS = {
    "production":  ["date","product","target","actual","downtime_min",
                     "prod_line","shift","machine_status"],
    "warehouse":   ["date","material","current_stock","minimum_stock",
                     "supplier","unit_cost"],
    "maintenance": ["date","machine_id","health_score","risk_level",
                     "maintenance_status"],
    "quality":     ["date","product","quality_score","inspection_status",
                     "defective_units"],
    "safety":      ["date","severity","employees_affected","safety_status",
                     "prod_line"],
}

EXCEL_MAP = {
    "production": {
        "file": "production.csv.xlsx",
        "map": {"date":"Date","product":"Product","target":"Target","actual":"Actual",
                "downtime_min":"Downtime_min","prod_line":"Prod_line",
                "shift":"shift","machine_status":"Machine_Status"},
    },
    "warehouse": {
        "file": "warehouse.csv.xlsx",
        "map": {"date":"Date","material":"Item_name","current_stock":"Current_stock",
                "minimum_stock":"Minimum_stock","supplier":"Supplier",
                "unit_cost":"Unit_Cost"},
    },
    "maintenance": {
        "file": "maintenance.csv.xlsx",
        "map": {"date":"Date","machine_id":"Machine_ID","health_score":"Health_Score",
                "risk_level":"Risk_Level","maintenance_status":"Maintenance_Status"},
    },
    "quality": {
        "file": "quality.csv.xlsx",
        "map": {"date":"Date","product":"Product","quality_score":"Quality_Score",
                "inspection_status":"Inspection_Status","defective_units":"Defective_Units"},
    },
    "safety": {
        "file": "safety.csv.xlsx",
        "map": {"date":"Date","severity":"Severity","employees_affected":"Employees_Affected",
                "safety_status":"Safety_Status","prod_line":"Prod_line"},
    },
}


def seed():
    supabase = get_supabase()

    for table, cfg in EXCEL_MAP.items():
        cols = TABLE_COLUMNS[table]
        path = os.path.join(BASE, cfg["file"])
        df = pd.read_excel(path)
        df.columns = df.columns.str.strip()

        records = []
        for _, row in df.iterrows():
            record = {}
            for db_col in cols:
                excel_col = cfg["map"].get(db_col)
                if excel_col is None:
                    continue
                val = row.get(excel_col)
                if pd.isna(val):
                    val = 0 if isinstance(val, (int, float)) else ""
                if excel_col == "Date" and hasattr(val, "strftime"):
                    val = val.strftime("%Y-%m-%d")
                record[db_col] = val
            records.append(record)

        supabase.table(table).delete().neq("id", 0).execute()
        # Batch insert in chunks of 50
        batch_size = 50
        for i in range(0, len(records), batch_size):
            chunk = records[i:i+batch_size]
            supabase.table(table).insert(chunk).execute()
            print(f"  {table}: inserted {min(i+batch_size, len(records))}/{len(records)}", end="\r", flush=True)

        sys.stdout.write(f"\n  {table}: {len(records)} rows seeded OK\n")

    sys.stdout.write("Done - all tables populated.\n")


if __name__ == "__main__":
    seed()
