#!/usr/bin/env python3
"""
## Gravitron Plugin: Context TTL Cleaner
name: context-ttl
description: Expire and purge stale context.db entries older than 4 hours
version: 1.0
commands: [gravitron context-ttl [--dry-run]]
"""
import os
import sys
import sqlite3
import datetime

STATE_DIR = os.environ.get("GRAVITRON_STATE", os.path.expanduser("~/.gemini/antigravity"))
DB_PATH = os.path.join(STATE_DIR, "context.db")
TTL_HOURS = 4

def run_cleanup(dry_run=False):
    if not os.path.exists(DB_PATH):
        print(f"  No context.db found at {DB_PATH}")
        return

    cutoff = datetime.datetime.now() - datetime.timedelta(hours=TTL_HOURS)
    cutoff_str = cutoff.strftime("%Y-%m-%d %H:%M:%S")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Count stale entries
    cursor.execute("SELECT COUNT(*) FROM context WHERE created_at < ?", (cutoff_str,))
    stale_count = cursor.fetchone()[0]

    # Count audit log entries older than TTL
    cursor.execute("SELECT COUNT(*) FROM audit WHERE timestamp < ?", (cutoff_str,))
    stale_audit = cursor.fetchone()[0]

    if dry_run:
        print(f"  [Dry Run] Would expire {stale_count} context entries and {stale_audit} audit log entries older than {TTL_HOURS}h")
        cursor.execute("SELECT id, created_at FROM context WHERE created_at < ? LIMIT 5", (cutoff_str,))
        rows = cursor.fetchall()
        for row in rows:
            print(f"    → ctx:{row[0]} (created: {row[1]})")
        conn.close()
        return

    # Purge
    cursor.execute("DELETE FROM context WHERE created_at < ?", (cutoff_str,))
    cursor.execute("DELETE FROM audit WHERE timestamp < ?", (cutoff_str,))
    conn.commit()

    # Get current size
    conn.execute("VACUUM")
    conn.close()

    db_size = os.path.getsize(DB_PATH) / 1024
    print(f"  ✓ Expired {stale_count} context entries and {stale_audit} audit entries")
    print(f"  ✓ DB size after vacuum: {db_size:.1f} KB")

if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    print(f"=== [Context TTL] Purging entries older than {TTL_HOURS}h ===")
    run_cleanup(dry_run=dry_run)
