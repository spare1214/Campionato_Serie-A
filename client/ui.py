from typing import Any, List, Optional
from client.api import CampionatoAPI, ApiError
from datetime import date
current_year = date.today().year


def read_nonempty(prompt: str) -> str:
    while True:
        s = input(prompt).strip()
        if s:
            return s
        print("Valore non valido. Riprova.")


def read_int(prompt: str, min_value: Optional[int] = None, max_value: Optional[int] = None) -> int:
    while True:
        s = input(prompt).strip()
        try:
            n = int(s)
        except ValueError:
            print("Inserisci un numero intero valido.")
            continue
        if min_value is not None and n < min_value:
            print(f"Deve essere >= {min_value}.")
            continue
        if max_value is not None and n > max_value:
            print(f"Deve essere <= {max_value}.")
            continue
        return n


def read_float(prompt: str, min_value: Optional[float] = None) -> float:
    while True:
        s = input(prompt).strip().replace(",", ".")
        try:
            x = float(s)
        except ValueError:
            print("Inserisci un numero valido (es. 1234.56).")
            continue
        if min_value is not None and x < min_value:
            print(f"Deve essere >= {min_value}.")
            continue
        return x


def print_teams(rows: List[Any]) -> None:
    if not rows:
        print("(nessuna squadra)")
        return
    print("\nID | Nome Club | Città | Anno | Budget")
    print("-" * 60)
    for r in rows:
        # expected: (id_squadra, nome_club, citta, anno_fondazione, budget)
        print(f"{r[0]} | {r[1]} | {r[2]} | {r[3]} | {r[4]}")
    print("")


def print_players(rows: List[Any]) -> None:
    if not rows:
        print("(nessun giocatore)")
        return
    print("\nID | Nome | Cognome | Ruolo | Maglia")
    print("-" * 60)
    for r in rows:
        # expected: (id_giocatore, nome, cognome, ruolo, numero_maglia)
        print(f"{r[0]} | {r[1]} | {r[2]} | {r[3]} | {r[4]}")
    print("")


def menu_loop(api: CampionatoAPI) -> None:
    while True:
        print(
            "\n=== CAMPIONATO (CLIENT) ===\n"
            "1) Inserisci nuova squadra\n"
            "2) Mostra tutte le squadre\n"
            "3) Cancella squadra (giocatori -> svincolati)\n"
            "4) Tesserare nuovo giocatore\n"
            "5) Mostra giocatori di una squadra\n"
            "6) Modifica dati giocatore\n"
            "7) Trasferisci giocatore\n"
            "8) Cancella giocatore\n"
            "9) Mostra giocatori svincolati\n"
            "0) Esci\n"
        )

        choice = input("Scelta: ").strip()

        try:
            if choice == "1":
                nome = read_nonempty("Nome club: ")
                citta = read_nonempty("Città: ")
                anno = read_int("Anno fondazione: ", min_value=1800, max_value=2100)
                if not (1850 <= anno <= current_year):
                    print(f"Anno non valido. Inserisci tra 1850 e {current_year}.")
                    continue
                budget = read_float("Budget: ", min_value=0.0)
                team_id = api.create_team(nome, citta, anno, budget)
                print(f"Squadra creata. ID = {team_id}")

            elif choice == "2":
                teams = api.list_teams()
                print_teams(teams)

            elif choice == "3":
                id_s = read_int("ID squadra da cancellare: ", min_value=1)
                confirm = input("Confermi cancellazione? (s/N): ").strip().lower()
                if confirm != "s":
                    print("Operazione annullata.")
                    # Stay in the menu instead of exiting entirely
                    continue
                api.delete_team(id_s)
                print("Squadra cancellata. (I giocatori diventano svincolati automaticamente)")

            elif choice == "4":
                nome = read_nonempty("Nome: ")
                cognome = read_nonempty("Cognome: ")
                roles = ["Portiere", "Difensore", "Centrocampista", "Attaccante"]
                print("Seleziona ruolo:")
                for i, r in enumerate(roles, 1):
                    print(f"{i}) {r}")
                choice = input("Scelta (1-4): ").strip()

                if not choice.isdigit() or not (1 <= int(choice) <= len(roles)):
                    print("Scelta non valida.")
                    continue

                ruolo = roles[int(choice) - 1]

                maglia = read_int("Numero maglia (1-99): ", min_value=1, max_value=99)
                print("Assegna a squadra? (premi INVIO per svincolato)")
                raw = input("ID squadra: ").strip()
                id_squadra = int(raw) if raw else None
                pid = api.create_player(nome, cognome, ruolo, maglia, id_squadra)
                print(f"Giocatore creato. ID = {pid}")

            elif choice == "5":
                id_s = read_int("ID squadra: ", min_value=1)
                players = api.list_players_by_team(id_s)
                print_players(players)

            elif choice == "6":
                id_g = read_int("ID giocatore: ", min_value=1)
                nome = read_nonempty("Nuovo nome: ")
                cognome = read_nonempty("Nuovo cognome: ")
                ruolo = read_nonempty("Nuovo ruolo: ")
                maglia = read_int("Nuovo numero maglia (1-99): ", min_value=1, max_value=99)
                api.update_player(id_g, nome, cognome, ruolo, maglia)
                print("Giocatore aggiornato.")

            elif choice == "7":
                id_g = read_int("ID giocatore: ", min_value=1)
                print("Nuova squadra? (premi INVIO per svincolare)")
                raw = input("ID nuova squadra: ").strip()
                new_team = int(raw) if raw else None
                api.transfer_player(id_g, new_team)
                print("Trasferimento completato.")

            elif choice == "8":
                id_g = read_int("ID giocatore da cancellare: ", min_value=1)
                confirm = input("Confermi cancellazione giocatore? (s/N): ").strip().lower()
                if confirm != "s":
                    print("Operazione annullata.")
                    # Skip deletion and continue the loop
                    continue
                api.delete_player(id_g)
                print("Giocatore cancellato.")
            
            elif choice == "9":
                players = api.list_free_agents()
                print_players(players)

            elif choice == "0":
                print("Uscita.")
                return

            else:
                print("Scelta non valida.")

        except ApiError as e:
            print(f"ERRORE (server): {e}")
        except ValueError:
            print("Input non valido.")
