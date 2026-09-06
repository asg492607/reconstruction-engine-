import sqlite3
import os

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "rre.db"))

TABLES_NEEDING_ANALYSIS_VERSION = [
    "observations",
    "candidate_entities",
    "candidate_entity_links",
    "findings",
    "claims",
    "source_timelines",
    "source_timeline_events",
    "correlated_timeline_events",
    "entity_relationships",
    "hypotheses",
    "gap_conflicts",
    "gaps_conflicts",
    "verifications",
    "reports",
]

def migrate():
    print(f"Connecting to database: {DB_PATH}")
    if not os.path.exists(DB_PATH):
        print("Database does not exist yet.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    for table in TABLES_NEEDING_ANALYSIS_VERSION:
        try:
            cursor.execute(f"PRAGMA table_info({table})")
            columns = [col[1] for col in cursor.fetchall()]
            if not columns:
                print(f"Table {table} does not exist in db, skipping.")
                continue

            if "analysis_version" not in columns:
                print(f"Adding analysis_version column to {table}...")
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN analysis_version INTEGER DEFAULT 1")
                cursor.execute(f"CREATE INDEX IF NOT EXISTS ix_{table}_analysis_version ON {table} (analysis_version)")
                print(f"  --> Updated {table} successfully.")
            else:
                print(f"Table {table} already has analysis_version.")
        except Exception as e:
            print(f"Error checking/updating {table}: {e}")

    conn.commit()
    conn.close()
    print("Migration finished.")

if __name__ == "__main__":
    migrate()
