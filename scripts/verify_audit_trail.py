#!/usr/bin/env python3
"""
Script de Vérification Audit Trail E2
======================================
Vérifie que l'audit trail fonctionne correctement
"""

import sqlite3
import sys
from pathlib import Path

# Ajouter src au path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from src.config import get_data_dir, get_settings

settings = get_settings()


def verify_audit_trail():
    """Vérifie l'audit trail"""
    db_path = settings.db_path
    if not db_path.startswith("/") and not db_path.startswith("C:"):
        db_path = str(get_data_dir().parent / db_path)

    if not Path(db_path).exists():
        print(f"❌ Database not found at {db_path}")
        print("   Run E1 pipeline first to create the database")
        return False

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Vérifier si la table existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_action_log'")
        if not cursor.fetchone():
            print("❌ Table 'user_action_log' does not exist")
            print("   This table should be created by E1 pipeline")
            return False

        print("✅ Table 'user_action_log' exists")

        # Compter les logs
        cursor.execute("SELECT COUNT(*) FROM user_action_log")
        total_logs = cursor.fetchone()[0]
        print(f"   Total logs: {total_logs}")

        if total_logs == 0:
            print("⚠️  No audit logs found")
            print("   Make some API requests to generate logs")
            return True

        # Statistiques par action_type
        cursor.execute("""
            SELECT action_type, COUNT(*) as count
            FROM user_action_log
            GROUP BY action_type
            ORDER BY count DESC
        """)
        print("\n📊 Actions by type:")
        for row in cursor.fetchall():
            print(f"   {row[0]}: {row[1]}")

        # Statistiques par resource_type
        cursor.execute("""
            SELECT resource_type, COUNT(*) as count
            FROM user_action_log
            GROUP BY resource_type
            ORDER BY count DESC
        """)
        print("\n📊 Actions by resource:")
        for row in cursor.fetchall():
            print(f"   {row[0]}: {row[1]}")

        # Derniers logs (24h)
        cursor.execute("""
            SELECT
                action_date,
                profil_id,
                action_type,
                resource_type,
                resource_id,
                ip_address
            FROM user_action_log
            WHERE action_date >= datetime('now', '-1 day')
            ORDER BY action_date DESC
            LIMIT 10
        """)
        recent_logs = cursor.fetchall()

        if recent_logs:
            print("\n📋 Recent logs (last 24h):")
            for log in recent_logs:
                print(f"   {log[0]} | User {log[1]} | {log[2]} | {log[3]} | IP: {log[5]}")
        else:
            print("\n⚠️  No logs in the last 24h")

        # Vérifier les logs avec IP
        cursor.execute("SELECT COUNT(*) FROM user_action_log WHERE ip_address IS NOT NULL")
        logs_with_ip = cursor.fetchone()[0]
        print(f"\n✅ Logs with IP address: {logs_with_ip}/{total_logs}")

        # Vérifier les logs avec resource_id
        cursor.execute("SELECT COUNT(*) FROM user_action_log WHERE resource_id IS NOT NULL")
        logs_with_resource_id = cursor.fetchone()[0]
        print(f"✅ Logs with resource_id: {logs_with_resource_id}/{total_logs}")

        print("\n✅ Audit trail verification complete")
        return True

    except Exception as e:
        print(f"❌ Error verifying audit trail: {e}")
        return False
    finally:
        conn.close()


if __name__ == "__main__":
    print("=" * 70)
    print("AUDIT TRAIL VERIFICATION - E2 API")
    print("=" * 70)
    print()

    success = verify_audit_trail()

    print()
    print("=" * 70)
    if success:
        print("✅ Verification completed")
    else:
        print("❌ Verification failed")
        sys.exit(1)
