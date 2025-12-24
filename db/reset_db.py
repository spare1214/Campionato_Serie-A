import sqlite3

DB_PATH = "db/campionato.db"

def reset_db() -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA foreign_keys = ON;")

        # Delete child table first, then parent table
        conn.execute("DELETE FROM giocatori;")
        conn.execute("DELETE FROM squadre;")

        # Reset AUTOINCREMENT counters (sqlite_sequence exists because of AUTOINCREMENT)
        conn.execute("DELETE FROM sqlite_sequence WHERE name IN ('giocatori', 'squadre');")

        conn.commit()

    print("Database reset completed (tables cleared, IDs reset).")

if __name__ == "__main__":
    reset_db()
