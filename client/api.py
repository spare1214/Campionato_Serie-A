import socket
from typing import Any, Dict, List, Optional

from client.protocol import encode_message, decode_message


class ApiError(Exception):
    pass


class CampionatoAPI:
    def __init__(self, host: str = "127.0.0.1", port: int = 5000):
        self.host = host
        self.port = port

    def _send(self, req: Dict[str, Any]) -> Dict[str, Any]:
        try:
            with socket.create_connection((self.host, self.port), timeout=5) as s:
                s.sendall(encode_message(req))
                line = s.makefile("rb").readline()
                if not line:
                    raise ApiError("Risposta vuota dal server.")
                resp = decode_message(line)
        except OSError as e:
            raise ApiError(f"Connessione al server fallita: {e}") from e
        if not resp.get("ok"):
            err = resp.get("error")
            if isinstance(err, dict):
                raise ApiError(f"{err.get('code')}: {err.get('message')}")
            raise ApiError(str(err) if err else "Errore sconosciuto.")
        return resp


    # ---- Teams ----
    def create_team(self, nome_club: str, citta: str, anno_fondazione: int, budget: float) -> int:
        resp = self._send({
            "action": "create_team",
            "data": {
                "nome_club": nome_club,
                "citta": citta,
                "anno_fondazione": anno_fondazione,
                "budget": budget,
            }
        })
        return int(resp["data"]["id_squadra"])

    def list_teams(self) -> List[Any]:
        resp = self._send({"action": "list_teams", "data": {}})
        return resp["data"]

    def delete_team(self, id_squadra: int) -> None:
        self._send({"action": "delete_team", "data": {"id_squadra": id_squadra}})

    # ---- Players ----
    def create_player(self, nome: str, cognome: str, ruolo: str, numero_maglia: int, id_squadra: Optional[int]) -> int:
        resp = self._send({
            "action": "create_player",
            "data": {
                "nome": nome,
                "cognome": cognome,
                "ruolo": ruolo,
                "numero_maglia": numero_maglia,
                "id_squadra": id_squadra,
            }
        })
        return int(resp["data"]["id_giocatore"])

    def list_players_by_team(self, id_squadra: int) -> List[Any]:
        resp = self._send({"action": "list_players_by_team", "data": {"id_squadra": id_squadra}})
        return resp["data"]

    def update_player(self, id_giocatore: int, nome: str, cognome: str, ruolo: str, numero_maglia: int) -> None:
        self._send({
            "action": "update_player",
            "data": {
                "id_giocatore": id_giocatore,
                "nome": nome,
                "cognome": cognome,
                "ruolo": ruolo,
                "numero_maglia": numero_maglia,
            }
        })

    def transfer_player(self, id_giocatore: int, id_squadra: Optional[int]) -> None:
        self._send({
            "action": "transfer_player",
            "data": {"id_giocatore": id_giocatore, "id_squadra": id_squadra}
        })

    def delete_player(self, id_giocatore: int) -> None:
        self._send({"action": "delete_player", "data": {"id_giocatore": id_giocatore}})

    def list_free_agents(self):
        resp = self._send({"action": "list_free_agents", "data": {}})
        return resp["data"]