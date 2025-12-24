from server import db

team_id = db.create_team("Squadra Test", "Roma", 1900, 1_000_000)
print("Team ID:", team_id)

player_id = db.create_player("Mario", "Rossi", "Attaccante", 9, team_id)
print("Player ID:", player_id)

print("Teams:", db.list_teams())
print("Players in team:", db.list_players_by_team(team_id))

db.delete_team(team_id)
print("Team deleted")

# Check that player is now svincolato
import sqlite3
conn = sqlite3.connect("db/campionato.db")
row = conn.execute(
    "SELECT id_giocatore, id_squadra FROM giocatori WHERE id_giocatore = ?",
    (player_id,),
).fetchone()
conn.close()

print("Player after team deletion:", row)
