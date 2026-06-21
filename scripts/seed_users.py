"""
Seed default users for Phase 5.2 RBAC.
Run this AFTER creating the users table in Supabase SQL Editor.

SQL to run in Supabase SQL Editor first:
-----------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT NOT NULL,
    display_name TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
-----------------------------------------

Run: py scripts/seed_users.py
"""
import sys, os, hashlib
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from modules.database import get_supabase

DEFAULT_USERS = [
    ("manager",   "factory@2024", "Factory Manager",       "Factory Manager"),
    ("production","prod@2024",    "Production Supervisor",  "Production Supervisor"),
    ("maintenance","maint@2024",  "Maintenance Engineer",   "Maintenance Engineer"),
    ("warehouse", "wh@2024",      "Warehouse Executive",    "Warehouse Executive"),
    ("quality",   "qual@2024",    "Quality Inspector",      "Quality Inspector"),
    ("safety",    "safety@2024",  "Safety Officer",          "Safety Officer"),
    ("admin",     "admin@2024",   "Admin",                  "Admin"),
]


def seed_users():
    supabase = get_supabase()

    # Check if users table exists
    try:
        supabase.table("users").select("*").limit(0).execute()
    except Exception as e:
        print("ERROR: users table does not exist or is not accessible.")
        print("Please run this SQL in Supabase SQL Editor first:")
        print()
        print("CREATE TABLE IF NOT EXISTS users (")
        print("    id BIGSERIAL PRIMARY KEY,")
        print("    username TEXT UNIQUE NOT NULL,")
        print("    password TEXT NOT NULL,")
        print("    role TEXT NOT NULL,")
        print("    display_name TEXT NOT NULL,")
        print("    created_at TIMESTAMPTZ DEFAULT NOW()")
        print(");")
        return

    # Clear existing users
    supabase.table("users").delete().neq("id", 0).execute()

    for username, password, display_name, role in DEFAULT_USERS:
        pw_hash = hashlib.sha256(password.encode()).hexdigest()
        supabase.table("users").insert({
            "username": username,
            "password": pw_hash,
            "role": role,
            "display_name": display_name,
        }).execute()
        print(f"  {username} ({role}) — created")

    print()
    print("Users seeded. Login credentials:")
    print("  manager      / factory@2024  → Factory Manager")
    print("  production   / prod@2024     → Production Supervisor")
    print("  maintenance  / maint@2024    → Maintenance Engineer")
    print("  warehouse    / wh@2024       → Warehouse Executive")
    print("  quality      / qual@2024     → Quality Inspector")
    print("  safety       / safety@2024   → Safety Officer")
    print("  admin        / admin@2024    → Admin")


if __name__ == "__main__":
    seed_users()
