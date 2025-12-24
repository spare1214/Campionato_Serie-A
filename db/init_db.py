# db/init_db.py
import sqlite3
from pathlib import Path


SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS squadre (
  id_squadra      INTEGER PRIMARY KEY AUTOINCREMENT,
  nome_club       TEXT NOT NULL UNIQUE,
  citta           TEXT NOT NULL,
  anno_fondazione INTEGER NOT NULL,
  budget          REAL NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS giocatori (
  id_giocatore  INTEGER PRIMARY KEY AUTOINCREMENT,
  nome          TEXT NOT NULL,
  cognome       TEXT NOT NULL,
  ruolo         TEXT NOT NULL,
  numero_maglia INTEGER NOT NULL,
  gol_segnati INTEGER NOT NULL DEFAULT 0,
  id_squadra    INTEGER NULL,
  FOREIGN KEY (id_squadra)
    REFERENCES squadre(id_squadra)
    ON UPDATE CASCADE
    ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_giocatori_cognome ON giocatori(cognome);
CREATE INDEX IF NOT EXISTS idx_giocatori_squadra ON giocatori(id_squadra);
"""

def init_db(db_path: str) -> None:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.executescript(SCHEMA_SQL)
        conn.commit()

def ensure_gol_segnati_column(conn: sqlite3.Connection) -> None:
    cur = conn.execute("PRAGMA table_info(giocatori)")
    cols = {row[1] for row in cur.fetchall()}  # row[1] = name
    if "gol_segnati" not in cols:
        conn.execute("ALTER TABLE giocatori ADD COLUMN gol_segnati INTEGER NOT NULL DEFAULT 0")
        conn.commit()


if __name__ == "__main__":
    db_path = str(Path(__file__).resolve().parent / "campionato.db")
    init_db(db_path)

    # optional: ensure migration for existing DBs
    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        ensure_gol_segnati_column(conn)

    print(f"DB initialized at {db_path}")

