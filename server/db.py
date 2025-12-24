import sqlite3
import threading
from typing import List, Tuple, Optional
from pathlib import Path

_DB_PATH = str((Path(__file__).resolve().parents[1] / "db" / "campionato.db"))

_write_lock = threading.Lock()

class NotFoundError(Exception):
    pass

class IntegrityError(Exception):
    pass


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(_DB_PATH, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


# -------- SQUADRE --------

def create_team(nome_club: str, citta: str, anno_fondazione: int, budget: float) -> int:
    with _write_lock, _connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO squadre (nome_club, citta, anno_fondazione, budget)
            VALUES (?, ?, ?, ?)
            """,
            (nome_club, citta, anno_fondazione, budget),
        )
        return cur.lastrowid

def team_exists(conn, team_id: int) -> bool:
    """
    Check if a team with the given id exists in the database.

    The ``squadre`` table defines the primary key column as ``id_squadra``.
    Prior versions of this code incorrectly queried the non-existent ``id`` column,
    which always returned ``None`` and caused various operations to fail.  This
    function now uses the correct ``id_squadra`` column.
    """
    cur = conn.execute("SELECT 1 FROM squadre WHERE id_squadra = ?", (team_id,))
    return cur.fetchone() is not None

def list_teams() -> List[Tuple]:
    with _connect() as conn:
        cur = conn.execute(
            """
            SELECT id_squadra, nome_club, citta, anno_fondazione, budget
            FROM squadre
            ORDER BY nome_club
            """
        )
        return cur.fetchall()


def delete_team(id_squadra: int) -> None:
    with _write_lock, _connect() as conn:
        # ensure the team exists before attempting to delete it
        if not team_exists(conn, id_squadra):
            raise NotFoundError("Squadra non trovata")
        # svincola giocatori: set their id_squadra to NULL
        conn.execute(
            "UPDATE giocatori SET id_squadra = NULL WHERE id_squadra = ?",
            (id_squadra,),
        )
        # delete the team itself
        conn.execute(
            "DELETE FROM squadre WHERE id_squadra = ?",
            (id_squadra,),
        )



# -------- GIOCATORI --------

def create_player(
    nome: str,
    cognome: str,
    ruolo: str,
    numero_maglia: int,
    id_squadra: Optional[int],
    gol_segnati: int = 0,
) -> int:
    with _write_lock, _connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO giocatori (nome, cognome, ruolo, numero_maglia, id_squadra, gol_segnati)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (nome, cognome, ruolo, numero_maglia, id_squadra, gol_segnati),
        )
        return cur.lastrowid

def player_exists(conn, player_id: int) -> bool:
    cur = conn.execute(
        "SELECT 1 FROM giocatori WHERE id_giocatore = ?",
        (player_id,),
    )
    return cur.fetchone() is not None


def list_players_by_team(id_squadra: int) -> List[Tuple]:
    with _connect() as conn:
        cur = conn.execute(
            """
            SELECT id_giocatore, nome, cognome, ruolo, numero_maglia
            FROM giocatori
            WHERE id_squadra = ?
            ORDER BY cognome, nome
            """,
            (id_squadra,),
        )
        return cur.fetchall()


def transfer_player(id_giocatore: int, new_id_squadra: Optional[int]) -> None:
    with _write_lock, _connect() as conn:
        if new_id_squadra is not None and not team_exists(conn, new_id_squadra):
            raise NotFoundError("Squadra non trovata")
        if not player_exists(conn, id_giocatore):
            raise NotFoundError("Giocatore non trovato")
        try:
            conn.execute(
                """
                UPDATE giocatori
                SET id_squadra = ?
                WHERE id_giocatore = ?
                """,
                (new_id_squadra, id_giocatore),
            )
        except sqlite3.IntegrityError as e:
            # surface SQLite integrity errors as our own type
            raise IntegrityError(str(e))



def delete_player(id_giocatore: int) -> None:
    with _write_lock, _connect() as conn:
        cur = conn.execute(
            "DELETE FROM giocatori WHERE id_giocatore = ?",
            (id_giocatore,),
        )
        if cur.rowcount == 0:
            raise NotFoundError("Giocatore non trovato")

def update_player(
    id_giocatore: int,
    nome: str,
    cognome: str,
    ruolo: str,
    numero_maglia: int,
    gol_segnati: Optional[int] = None,
) -> None:
    with _write_lock, _connect() as conn:
        if not player_exists(conn, id_giocatore):
            raise NotFoundError("Giocatore non trovato")
        try:
            conn.execute(
                """
                UPDATE giocatori
                SET nome = ?,
                    cognome = ?,
                    ruolo = ?,
                    numero_maglia = ?,
                    gol_segnati = COALESCE(?, gol_segnati)
                WHERE id_giocatore = ?
                """,
                (nome, cognome, ruolo, numero_maglia, gol_segnati, id_giocatore),
            )
        except sqlite3.IntegrityError as e:
            raise IntegrityError(str(e))

def get_team_by_id(id_squadra: int):
    with _connect() as conn:
        cur = conn.execute(
            "SELECT id_squadra, nome_club, citta, anno_fondazione, budget FROM squadre WHERE id_squadra = ?",
            (id_squadra,),
        )
        row = cur.fetchone()
        if row is None:
            raise NotFoundError("Squadra non trovata")
        return row
        
def list_free_agents():
    with _connect() as conn:
        cur = conn.execute(
            """
            SELECT id_giocatore, nome, cognome, ruolo, numero_maglia, gol_segnati
            FROM giocatori
            WHERE id_squadra IS NULL
            ORDER BY cognome, nome
            """
        )
        return cur.fetchall()
