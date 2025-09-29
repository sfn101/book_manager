#!/usr/bin/env python3
"""
Add `role` column to users table if it doesn't exist.
This script uses the same environment variables/config as the app (via config.Config).
"""
import sys
import traceback
from database.connection import get_db
from config import Config

def run_migration():
    try:
        with get_db() as conn:
            with conn.cursor() as cursor:
                # Add column if not exists (Postgres 9.6+ supports IF NOT EXISTS for ALTER TABLE ADD COLUMN)
                add_col = "ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR(10) DEFAULT 'user';"
                cursor.execute(add_col)
                print("✅ Executed: add column role if not exists")

                # Ensure no NULL roles remain
                update_nulls = "UPDATE users SET role = 'user' WHERE role IS NULL;"
                cursor.execute(update_nulls)
                print(f"✅ Updated NULL roles (rows affected: {cursor.rowcount})")

        print("🎉 Migration complete: 'role' column present and defaults set.")
    except Exception as e:
        print("❌ Migration failed:")
        traceback.print_exc()
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(run_migration())
