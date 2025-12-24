import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date
CURRENT_YEAR = date.today().year

from client.api import CampionatoAPI, ApiError

PASSWORD = "mypass"


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Campionato - GUI")
        self.geometry("900x550")

        self.api = CampionatoAPI("127.0.0.1", 5000)

        self._build_login()

    def _build_login(self):
        self.login_frame = ttk.Frame(self, padding=20)
        self.login_frame.pack(fill="both", expand=True)

        ttk.Label(self.login_frame, text="Password:").pack(anchor="w")
        self.pwd_var = tk.StringVar()
        pwd_entry = ttk.Entry(self.login_frame, textvariable=self.pwd_var, show="*")
        pwd_entry.pack(anchor="w", fill="x")
        pwd_entry.focus()

        ttk.Button(self.login_frame, text="Entra", command=self._login).pack(anchor="w", pady=10)

    def _login(self):
        if self.pwd_var.get().strip() != PASSWORD:
            messagebox.showerror("Errore", "Password errata.")
            return

        self.login_frame.destroy()
        self._build_main()

    def _build_main(self):
        root = ttk.Frame(self, padding=10)
        root.pack(fill="both", expand=True)

        # Left: Teams
        left = ttk.Frame(root)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        ttk.Label(left, text="Squadre").pack(anchor="w")

        self.teams_tree = ttk.Treeview(left, columns=("id", "nome", "citta", "anno", "budget"), show="headings", height=12)
        for col, title, w in [
            ("id", "ID", 60),
            ("nome", "Nome", 180),
            ("citta", "Città", 140),
            ("anno", "Anno", 80),
            ("budget", "Budget", 120),
        ]:
            self.teams_tree.heading(col, text=title)
            self.teams_tree.column(col, width=w, anchor="w")
        self.teams_tree.pack(fill="x")
        self.teams_tree.bind("<<TreeviewSelect>>", lambda e: self.refresh_players())

        btns = ttk.Frame(left)
        btns.pack(fill="x", pady=6)
        ttk.Button(btns, text="Aggiorna", command=self.refresh_teams).pack(side="left")
        ttk.Button(btns, text="Cancella squadra", command=self.delete_selected_team).pack(side="left", padx=6)

        form = ttk.LabelFrame(left, text="Nuova squadra", padding=10)
        form.pack(fill="x", pady=10)

        self.team_nome = tk.StringVar()
        self.team_citta = tk.StringVar()
        self.team_anno = tk.StringVar()
        self.team_budget = tk.StringVar()

        self._row(form, "Nome club", self.team_nome)
        self._row(form, "Città", self.team_citta)
        self._row(form, "Anno fondazione", self.team_anno)
        self._row(form, "Budget", self.team_budget)
        ttk.Button(form, text="Crea squadra", command=self.create_team).pack(anchor="e", pady=(6, 0))

        # Right: Players
        right = ttk.Frame(root)
        right.pack(side="left", fill="both", expand=True)

        ttk.Label(right, text="Giocatori (della squadra selezionata)").pack(anchor="w")

        self.players_tree = ttk.Treeview(
            right, columns=("id", "nome", "cognome", "ruolo", "maglia"), show="headings", height=12
        )
        for col, title, w in [
            ("id", "ID", 60),
            ("nome", "Nome", 120),
            ("cognome", "Cognome", 140),
            ("ruolo", "Ruolo", 140),
            ("maglia", "Maglia", 80),
        ]:
            self.players_tree.heading(col, text=title)
            self.players_tree.column(col, width=w, anchor="w")
        self.players_tree.pack(fill="x")

        pform = ttk.LabelFrame(right, text="Nuovo giocatore (per squadra selezionata)", padding=10)
        pform.pack(fill="x", pady=10)

        self.p_nome = tk.StringVar()
        self.p_cognome = tk.StringVar()
        self.p_ruolo = tk.StringVar()
        self.p_maglia = tk.StringVar()

        self._row(pform, "Nome", self.p_nome)
        self._row(pform, "Cognome", self.p_cognome)
        self._row(pform, "Ruolo", self.p_ruolo)
        self._row(pform, "Numero maglia", self.p_maglia)
        ttk.Button(pform, text="Crea giocatore", command=self.create_player).pack(anchor="e", pady=(6, 0))

        tform = ttk.LabelFrame(right, text="Trasferimento (giocatore selezionato -> squadra selezionata)", padding=10)
        tform.pack(fill="x", pady=10)
        ttk.Button(tform, text="Trasferisci", command=self.transfer_selected_player).pack(anchor="e")

        self.refresh_teams()

    def _row(self, parent, label, var):
        row = ttk.Frame(parent)
        row.pack(fill="x", pady=2)
        ttk.Label(row, text=label, width=18).pack(side="left")
        ttk.Entry(row, textvariable=var).pack(side="left", fill="x", expand=True)

    def refresh_teams(self):
        try:
            teams = self.api.list_teams()
        except ApiError as e:
            messagebox.showerror("Errore server", str(e))
            return

        for i in self.teams_tree.get_children():
            self.teams_tree.delete(i)

        for r in teams:
            # (id_squadra, nome_club, citta, anno_fondazione, budget)
            self.teams_tree.insert("", "end", values=(r[0], r[1], r[2], r[3], r[4]))

        self.refresh_players()

    def selected_team_id(self):
        sel = self.teams_tree.selection()
        if not sel:
            return None
        values = self.teams_tree.item(sel[0], "values")
        return int(values[0])

    def refresh_players(self):
        team_id = self.selected_team_id()
        for i in self.players_tree.get_children():
            self.players_tree.delete(i)

        if team_id is None:
            return

        try:
            players = self.api.list_players_by_team(team_id)
        except ApiError as e:
            messagebox.showerror("Errore server", str(e))
            return

        for r in players:
            # (id_giocatore, nome, cognome, ruolo, numero_maglia)
            self.players_tree.insert("", "end", values=(r[0], r[1], r[2], r[3], r[4]))

    def create_team(self):
        try:
            nome = self.team_nome.get().strip()
            citta = self.team_citta.get().strip()
            anno = int(self.team_anno.get().strip())
            if not (1850 <= anno <= CURRENT_YEAR):
                raise ValueError(f"Anno fondazione non valido. Inserisci un anno tra 1850 e {CURRENT_YEAR}.")
            budget = float(self.team_budget.get().strip().replace(",", "."))

            if not nome or not citta:
                raise ValueError("Nome e città sono obbligatori.")

            self.api.create_team(nome, citta, anno, budget)
            self.team_nome.set(""); self.team_citta.set(""); self.team_anno.set(""); self.team_budget.set("")
            self.refresh_teams()
        except (ValueError, ApiError) as e:
            messagebox.showerror("Errore", str(e))

    def delete_selected_team(self):
        team_id = self.selected_team_id()
        if team_id is None:
            messagebox.showinfo("Info", "Seleziona una squadra.")
            return
        if not messagebox.askyesno("Conferma", "Cancellare la squadra? (giocatori -> svincolati)"):
            return
        try:
            self.api.delete_team(team_id)
            self.refresh_teams()
        except ApiError as e:
            messagebox.showerror("Errore server", str(e))

    def create_player(self):
        team_id = self.selected_team_id()
        if team_id is None:
            messagebox.showinfo("Info", "Seleziona una squadra.")
            return
        try:
            nome = self.p_nome.get().strip()
            cognome = self.p_cognome.get().strip()
            ruolo = self.p_ruolo.get().strip()
            maglia = int(self.p_maglia.get().strip())

            if not nome or not cognome or not ruolo:
                raise ValueError("Nome, cognome e ruolo sono obbligatori.")
            if not (1 <= maglia <= 99):
                raise ValueError("Numero maglia deve essere 1..99.")

            self.api.create_player(nome, cognome, ruolo, maglia, team_id)
            self.p_nome.set(""); self.p_cognome.set(""); self.p_ruolo.set(""); self.p_maglia.set("")
            self.refresh_players()
        except (ValueError, ApiError) as e:
            messagebox.showerror("Errore", str(e))

    def transfer_selected_player(self):
        team_id = self.selected_team_id()
        sel = self.players_tree.selection()
        if team_id is None:
            messagebox.showinfo("Info", "Seleziona una squadra di destinazione.")
            return
        if not sel:
            messagebox.showinfo("Info", "Seleziona un giocatore.")
            return

        values = self.players_tree.item(sel[0], "values")
        player_id = int(values[0])

        if not messagebox.askyesno("Conferma", f"Trasferire giocatore ID {player_id} alla squadra ID {team_id}?"):
            return

        try:
            self.api.transfer_player(player_id, team_id)
            self.refresh_players()
        except ApiError as e:
            messagebox.showerror("Errore server", str(e))


def main():
    App().mainloop()


if __name__ == "__main__":
    main()
