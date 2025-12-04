#!/usr/bin/env python3
"""
Database repair utility for fixing lock issues
"""
import os
import sqlite3
import time

def fix_database_lock(db_path: str = "english_learning.db"):
    """Fix database lock issues"""
    print(f"🔧 Attempting to fix database: {db_path}")

    # Check if database file exists
    if not os.path.exists(db_path):
        print("✅ Database file doesn't exist, no lock to fix")
        return True

    # Try to check for lock files
    lock_files = [f"{db_path}-wal", f"{db_path}-shm", f"{db_path}-journal"]

    for lock_file in lock_files:
        if os.path.exists(lock_file):
            print(f"🗑️  Removing lock file: {lock_file}")
            try:
                os.remove(lock_file)
                print(f"✅ Removed {lock_file}")
            except Exception as e:
                print(f"❌ Could not remove {lock_file}: {e}")

    # Try to open and close database to verify
    try:
        conn = sqlite3.connect(db_path, timeout=5.0)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        conn.close()
        print(f"✅ Database accessible, found {len(tables)} tables")
        return True
    except Exception as e:
        print(f"❌ Database still locked: {e}")
        return False

def backup_and_recreate():
    """Backup current database and recreate it"""
    db_path = "english_learning.db"
    backup_path = f"english_learning_backup_{int(time.time())}.db"

    print(f"💾 Creating backup: {backup_path}")

    try:
        if os.path.exists(db_path):
            os.rename(db_path, backup_path)
            print("✅ Backup created successfully")
        else:
            print("ℹ️  No existing database to backup")

        # Import and initialize new database
        from simple_database import SimpleDatabase
        db = SimpleDatabase()
        print("✅ New database initialized")
        return True

    except Exception as e:
        print(f"❌ Backup/recreate failed: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Database Lock Fix Tool")
    print("=" * 40)

    if not fix_database_lock():
        print("\n🔄 Attempting to backup and recreate...")
        if backup_and_recreate():
            print("✅ Database fixed successfully!")
        else:
            print("❌ Could not fix database issues")
    else:
        print("✅ Database is working fine!")

    print("\n💡 Try running the tutor again:")
    print("uv run english_tutor.py")