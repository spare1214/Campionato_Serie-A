from pathlib import Path
from dotenv import load_dotenv
from datetime import date

load_dotenv(Path(__file__).resolve().parents[1] / ".env")
current_year = date.today().year
ALLOWED_ROLES = {"Portiere", "Difensore", "Centrocampista", "Attaccante"}

import socket
import threading
from typing import Dict, Any
from .email import send_delete_team_email
from . import db
from .protocol import encode_message, decode_message

HOST = "127.0.0.1"
PORT = 5000


def handle_request(req: Dict[str, Any]) -> Dict[str, Any]:
    action = req.get("action")
    data = req.get("data", {})

    try:
        if action == "list_teams":
            teams = db.list_teams()
            return {"ok": True, "data": teams}

        if action == "create_team":
            anno = int(data["anno_fondazione"])
            if not (1850 <= anno <= current_year):
                return {
                    "ok": False,
                    "error": {"code": "BAD_REQUEST",
                              "message": f"Anno fondazione non valido (1850..{current_year})"}
                }

            team_id = db.create_team(
                data["nome_club"],
                data["citta"],
                anno,
                float(data["budget"]),
            )
            return {"ok": True, "data": {"id_squadra": team_id}}

        if action == "list_players_by_team":
            players = db.list_players_by_team(int(data["id_squadra"]))
            return {"ok": True, "data": players}
        
        if action == "create_player":
            ruolo = data["ruolo"].strip()
            if ruolo not in ALLOWED_ROLES:
                return {"ok": False, "error": {"code": "BAD_REQUEST", "message": "Ruolo non valido"}}

            pid = db.create_player(
                data["nome"],
                data["cognome"],
                ruolo,
                int(data["numero_maglia"]),
                data.get("id_squadra"),
            )
            return {"ok": True, "data": {"id_giocatore": pid}}


        if action == "update_player":
            ruolo = data["ruolo"].strip()
            if ruolo not in ALLOWED_ROLES:
                return {"ok": False, "error": {"code": "BAD_REQUEST", "message": "Ruolo non valido"}}

            db.update_player(
                int(data["id_giocatore"]),
                data["nome"],
                data["cognome"],
                ruolo,
                int(data["numero_maglia"]),
            )
            return {"ok": True, "data": {}}


        if action == "transfer_player":
            db.transfer_player(int(data["id_giocatore"]), data.get("id_squadra"))
            return {"ok": True, "data": {}}

        if action == "delete_player":
            db.delete_player(int(data["id_giocatore"]))
            return {"ok": True, "data": {}}

        if action == "delete_team":
            team_id = int(data["id_squadra"])

            # get name before deletion
            team = db.get_team_by_id(team_id)
            team_name = team[1]  # nome_club
            # delete (svincolo is inside db.delete_team)
            db.delete_team(team_id)

            # email notification
            try:
                send_delete_team_email(team_name, team_id)
            except Exception:
                pass
            return {"ok": True, "data": {}}

        
        if action == "list_free_agents":
            players = db.list_free_agents()
            return {"ok": True, "data": players}

        return {
            "ok": False,
            "error": {"code": "UNKNOWN_ACTION", "message": f"Unknown action: {action}"}
        }

    except KeyError as e:
        return {
            "ok": False,
            "error": {"code": "BAD_REQUEST", "message": f"Missing field: {e}"}
        }
    except ValueError as e:
        return {
            "ok": False,
            "error": {"code": "BAD_REQUEST", "message": str(e)}
        }
    except Exception as e:
        return {
            "ok": False,
            "error": {"code": "SERVER_ERROR", "message": str(e)}
        }


def client_thread(conn: socket.socket, addr):
    with conn:
        file = conn.makefile("rb")
        for line in file:
            try:
                req = decode_message(line)
            except Exception:
                resp = {"ok": False, "error": {"code": "BAD_JSON", "message": "Invalid JSON"}}
            else:
                resp = handle_request(req)

            conn.sendall(encode_message(resp))


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen()
        print(f"Server listening on {HOST}:{PORT}")

        while True:
            conn, addr = s.accept()
            t = threading.Thread(target=client_thread, args=(conn, addr), daemon=True)
            t.start()

if __name__ == "__main__":
    main()
