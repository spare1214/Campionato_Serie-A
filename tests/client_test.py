import socket
from typing import Any, Dict, Optional, List

from client.protocol import encode_message, decode_message

HOST = "127.0.0.1"
PORT = 5000


def send(req: Dict[str, Any]) -> Dict[str, Any]:
    with socket.create_connection((HOST, PORT)) as s:
        s.sendall(encode_message(req))
        line = s.makefile("rb").readline()
        return decode_message(line)


def create_team(nome_club: str, citta: str, anno_fondazione: int, budget: float) -> int:
    resp = send({
        "action": "create_team",
        "data": {
            "nome_club": nome_club,
            "citta": citta,
            "anno_fondazione": anno_fondazione,
            "budget": budget
        }
    })
    assert resp["ok"], resp
    return int(resp["data"]["id_squadra"])


def list_teams() -> List[Any]:
    resp = send({"action": "list_teams", "data": {}})
    assert resp["ok"], resp
    return resp["data"]


def create_player(nome: str, cognome: str, ruolo: str, numero_maglia: int, id_squadra: Optional[int]) -> int:
    resp = send({
        "action": "create_player",
        "data": {
            "nome": nome,
            "cognome": cognome,
            "ruolo": ruolo,
            "numero_maglia": numero_maglia,
            "id_squadra": id_squadra
        }
    })
    assert resp["ok"], resp
    return int(resp["data"]["id_giocatore"])


def list_players_by_team(id_squadra: int) -> List[Any]:
    resp = send({
        "action": "list_players_by_team",
        "data": {"id_squadra": id_squadra}
    })
    assert resp["ok"], resp
    return resp["data"]


def update_player(id_giocatore: int, nome: str, cognome: str, ruolo: str, numero_maglia: int) -> None:
    resp = send({
        "action": "update_player",
        "data": {
            "id_giocatore": id_giocatore,
            "nome": nome,
            "cognome": cognome,
            "ruolo": ruolo,
            "numero_maglia": numero_maglia
        }
    })
    assert resp["ok"], resp


def transfer_player(id_giocatore: int, id_squadra: Optional[int]) -> None:
    resp = send({
        "action": "transfer_player",
        "data": {"id_giocatore": id_giocatore, "id_squadra": id_squadra}
    })
    assert resp["ok"], resp


def delete_player(id_giocatore: int) -> None:
    resp = send({
        "action": "delete_player",
        "data": {"id_giocatore": id_giocatore}
    })
    assert resp["ok"], resp


def delete_team(id_squadra: int) -> None:
    resp = send({
        "action": "delete_team",
        "data": {"id_squadra": id_squadra}
    })
    assert resp["ok"], resp


def main():
    # 1) Create two teams
    team_a = create_team("Team A", "Roma", 1900, 1_000_000.0)
    team_b = create_team("Team B", "Milano", 1910, 2_000_000.0)
    print("Created teams:", team_a, team_b)

    # 2) Create a player in Team A
    player_id = create_player("Mario", "Rossi", "Attaccante", 9, team_a)
    print("Created player:", player_id)

    # 3) List players in Team A
    players_a = list_players_by_team(team_a)
    print("Players in Team A:", players_a)

    # 4) Update player data
    update_player(player_id, "Mario", "Rossi", "Centrocampista", 8)
    players_a_after_update = list_players_by_team(team_a)
    print("Players in Team A after update:", players_a_after_update)

    # 5) Transfer player to Team B
    transfer_player(player_id, team_b)
    players_b = list_players_by_team(team_b)
    print("Players in Team B after transfer:", players_b)

    # 6) Delete Team B -> player becomes svincolato (id_squadra NULL)
    delete_team(team_b)
    print("Deleted Team B:", team_b)

    # 7) Player should not appear in Team B anymore
    players_b_after = list_players_by_team(team_b)
    print("Players in Team B after deletion:", players_b_after)

    # 8) Delete player entirely
    delete_player(player_id)
    print("Deleted player:", player_id)

    print("Integration test completed successfully.")

if __name__ == "__main__":
    main()
