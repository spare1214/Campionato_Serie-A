import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
from datetime import date
from client.api import CampionatoAPI, ApiError

PASSWORD = "mypass" 
ROLES = ["Portiere", "Difensore", "Centrocampista", "Attaccante"]
current_year = date.today().year




class LoginView(tk.Frame):
    def __init__(self, master, on_success):
        super().__init__(master, bg="#0B0F2A", bd=0, highlightthickness=0)
        self.on_success = on_success

        tk.Label(self, text="Campionato Serie A", font=("Segoe UI", 20, "bold"),
                 fg="white", bg="#0B0F2A").pack(pady=(15, 10))

        tk.Label(self, text="Password:", fg="white", bg="#0B0F2A",
                 font=("Segoe UI", 11)).pack(anchor="w", padx=18)

        self.pwd_var = tk.StringVar()
        e = ttk.Entry(self, textvariable=self.pwd_var, show="*")
        e.pack(fill="x", padx=18, pady=(6, 12))
        e.focus()

        ttk.Button(self, text="Entra", command=self._login).pack(pady=(0, 15))

        master.bind("<Return>", lambda _e: self._login())

    def _login(self):
        """
        Authenticate the user by checking the provided password.

        Earlier versions accidentally duplicated this method multiple times.
        Keeping a single definition avoids confusion and ensures that the bound
        login behaviour is consistent.
        """
        if self.pwd_var.get().strip() != PASSWORD:
            messagebox.showerror("Errore", "Password errata.")
            return
        # delegate to the callback on successful login
        self.on_success()

class DashboardView:
    def __init__(self, master, api: CampionatoAPI):
        self.master = master
        self.api = api

        style = ttk.Style()

        # Soft button styling
        style.configure(
            "Soft.TButton",
            font=("Segoe UI", 13, "bold"),
            padding=(18, 12)
        )

        # Column positioning (tune relx to move left/right)
        col = tk.Frame(master, bg="", bd=0, highlightthickness=0)
        col.place(relx=0.82, rely=0.50, anchor="center")  # slightly more left than before

        # Subtle "card" color that blends with your blue background
        CARD_BG = "#11183A"   # softer than pure navy
        CARD_EDGE = "#25306A" # subtle border line

        def soft_tile(parent, text, cmd):
            # Outer wrapper for a soft border effect
            outer = tk.Frame(parent, bg=CARD_EDGE, bd=0, highlightthickness=0)
            outer.pack(pady=14)

            # Inner soft background
            inner = tk.Frame(outer, bg=CARD_BG, bd=0, highlightthickness=0)
            inner.pack(padx=2, pady=2)

            # Button (keep ttk for consistent text rendering)
            btn = ttk.Button(inner, text=text, style="Soft.TButton", width=18, command=cmd)
            btn.pack(padx=14, pady=14)

            return outer

        soft_tile(col, "DISPLAY", self.open_display)
        soft_tile(col, "INSERT",  self.open_insert)
        soft_tile(col, "UPDATE",  self.open_update)
        soft_tile(col, "DELETE",  self.open_delete)

    def open_display(self):
        DisplayWindow(self.master, self.api)

    def open_insert(self):
        InsertWindow(self.master, self.api)

    def open_update(self):
        UpdateWindow(self.master, self.api)

    def open_delete(self):
        DeleteWindow(self.master, self.api)

    # Note: removed duplicate definitions of open_display, open_insert,
    # open_update, open_delete and an unused destroy() method.  Keeping a
    # single definition for each helper ensures the Dashboard behaves
    # consistently.


class DisplayWindow(tk.Toplevel):
    def __init__(self, master, api: CampionatoAPI):
        super().__init__(master, bg="#0B0F2A", bd=0, highlightthickness=0)
        self.configure(padx=10, pady=10)
        self.api = api
        self.title("DISPLAY - Squadre / Giocatori / Svincolati")
        self.geometry("1100x650")

        root = ttk.Frame(self, padding=10)
        root.pack(fill="both", expand=True)

        # Teams
        ttk.Label(root, text="Squadre", font=("Segoe UI", 12, "bold")).pack(anchor="w")
        self.teams = ttk.Treeview(root, columns=("id", "nome", "citta", "anno", "budget"), show="headings", height=8)
        self._setup_tree(self.teams, [("id","ID",60), ("nome","Nome",200), ("citta","Città",160), ("anno","Anno",80), ("budget","Budget",120)])
        self.teams.pack(fill="x")
        self.teams.bind("<<TreeviewSelect>>", lambda _e: self.refresh_players())

        btns = ttk.Frame(root)
        btns.pack(fill="x", pady=6)
        ttk.Button(btns, text="Aggiorna tutto", command=self.refresh_all).pack(side="left")

        # Players for selected team
        ttk.Separator(root).pack(fill="x", pady=10)
        ttk.Label(root, text="Giocatori (squadra selezionata)", font=("Segoe UI", 12, "bold")).pack(anchor="w")
        self.players = ttk.Treeview(root, columns=("id","nome","cognome","ruolo","maglia"), show="headings", height=8)
        self._setup_tree(self.players, [("id","ID",60), ("nome","Nome",140), ("cognome","Cognome",160), ("ruolo","Ruolo",160), ("maglia","Maglia",80)])
        self.players.pack(fill="x")

        # Free agents
        ttk.Separator(root).pack(fill="x", pady=10)
        ttk.Label(root, text="Svincolati", font=("Segoe UI", 12, "bold")).pack(anchor="w")
        self.free = ttk.Treeview(root, columns=("id","nome","cognome","ruolo","maglia"), show="headings", height=8)
        self._setup_tree(self.free, [("id","ID",60), ("nome","Nome",140), ("cognome","Cognome",160), ("ruolo","Ruolo",160), ("maglia","Maglia",80)])
        self.free.pack(fill="x")

        self.refresh_all()

    def _setup_tree(self, tree, cols):
        for c, title, w in cols:
            tree.heading(c, text=title)
            tree.column(c, width=w, anchor="w")

    def _clear(self, tree):
        for i in tree.get_children():
            tree.delete(i)

    def selected_team_id(self):
        sel = self.teams.selection()
        if not sel:
            return None
        return int(self.teams.item(sel[0], "values")[0])

    def refresh_all(self):
        self.refresh_teams()
        self.refresh_players()
        self.refresh_free_agents()

    def refresh_teams(self):
        try:
            rows = self.api.list_teams()
        except ApiError as e:
            messagebox.showerror("Errore server", str(e))
            return
        self._clear(self.teams)
        for r in rows:
            self.teams.insert("", "end", values=(r[0], r[1], r[2], r[3], r[4]))

    def refresh_players(self):
        team_id = self.selected_team_id()
        self._clear(self.players)
        if team_id is None:
            return
        try:
            rows = self.api.list_players_by_team(team_id)
        except ApiError as e:
            messagebox.showerror("Errore server", str(e))
            return
        for r in rows:
            self.players.insert("", "end", values=(r[0], r[1], r[2], r[3], r[4]))

    def refresh_free_agents(self):
        self._clear(self.free)
        try:
            rows = self.api.list_free_agents()
        except ApiError as e:
            messagebox.showerror("Errore server", str(e))
            return
        for r in rows:
            self.free.insert("", "end", values=(r[0], r[1], r[2], r[3], r[4]))


class InsertWindow(tk.Toplevel):
    def __init__(self, master, api: CampionatoAPI):
        super().__init__(master)
        self.api = api
        self.title("INSERT - Nuova Squadra / Nuovo Giocatore")
        self.geometry("650x520")

        root = ttk.Frame(self, padding=12)
        root.pack(fill="both", expand=True)

        # Team form
        team = ttk.LabelFrame(root, text="Nuova squadra", padding=10)
        team.pack(fill="x")

        self.t_nome = tk.StringVar()
        self.t_citta = tk.StringVar()
        self.t_anno = tk.StringVar()
        self.t_budget = tk.StringVar()

        self._row(team, "Nome club", self.t_nome)
        self._row(team, "Città", self.t_citta)
        self._row(team, "Anno", self.t_anno)
        self._row(team, "Budget", self.t_budget)

        ttk.Button(team, text="Crea squadra", command=self.create_team).pack(anchor="e", pady=(8, 0))

        # Player form
        player = ttk.LabelFrame(root, text="Nuovo giocatore", padding=10)
        player.pack(fill="x", pady=12)


        self.p_nome = tk.StringVar()
        self.p_cognome = tk.StringVar()
        self.p_ruolo = tk.StringVar(value=ROLES[0])
        self.p_maglia = tk.StringVar()
        self.p_team_id = tk.StringVar()  # optional: empty => svincolato

        self._row(player, "Nome", self.p_nome)
        self._row(player, "Cognome", self.p_cognome)
        self._row_combo(player, "Ruolo", self.p_ruolo, ROLES)
        self._row(player, "Maglia (1-99)", self.p_maglia)
        self._row(player, "ID Squadra (vuoto=svincolato)", self.p_team_id)

        ttk.Button(player, text="Crea giocatore", command=self.create_player).pack(anchor="e", pady=(8, 0))

    def _row(self, parent, label, var):
        row = ttk.Frame(parent)
        row.pack(fill="x", pady=2)
        ttk.Label(row, text=label, width=26).pack(side="left")
        ttk.Entry(row, textvariable=var).pack(side="left", fill="x", expand=True)

    def _row_combo(self, parent, label, var, values):
        row = ttk.Frame(parent)
        row.pack(fill="x", pady=2)
        ttk.Label(row, text=label, width=28).pack(side="left")
        cb = ttk.Combobox(row, textvariable=var, values=values, state="readonly", width=20)
        cb.pack(side="left", fill="x", expand=True)

    def create_team(self):
        try:
            nome = self.t_nome.get().strip()
            citta = self.t_citta.get().strip()
            anno = int(self.t_anno.get().strip())            
            if not (1850 <= anno <= current_year):
                raise ValueError(f"Anno fondazione non valido. Inserisci un anno tra 1850 e {current_year}.")
            
            budget = float(self.t_budget.get().strip().replace(",", "."))
            if not nome or not citta:
                raise ValueError("Nome e città obbligatori.")
            team_id = self.api.create_team(nome, citta, anno, budget)
            messagebox.showinfo("OK", f"Squadra creata. ID={team_id}")
            self.t_nome.set(""); self.t_citta.set(""); self.t_anno.set(""); self.t_budget.set("")
        except (ValueError, ApiError) as e:
            messagebox.showerror("Errore", str(e))

    def create_player(self):
        try:
            nome = self.p_nome.get().strip()
            cognome = self.p_cognome.get().strip()
            ruolo = self.p_ruolo.get()
            maglia = int(self.p_maglia.get().strip())
            raw_team = self.p_team_id.get().strip()
            team_id = int(raw_team) if raw_team else None

            if not nome or not cognome or not ruolo:
                raise ValueError("Nome, cognome e ruolo obbligatori.")
            if not (1 <= maglia <= 99):
                raise ValueError("Maglia deve essere 1..99.")

            pid = self.api.create_player(nome, cognome, ruolo, maglia, team_id)
            messagebox.showinfo("OK", f"Giocatore creato. ID={pid}")
            self.p_nome.set(""); self.p_cognome.set(""); self.p_ruolo.set(ROLES[0]); self.p_maglia.set(""); self.p_team_id.set("")
        except (ValueError, ApiError) as e:
            messagebox.showerror("Errore", str(e))


class UpdateWindow(tk.Toplevel):
    def __init__(self, master, api: CampionatoAPI):
        super().__init__(master)
        self.api = api
        self.title("UPDATE - Modifica Giocatore / Trasferimento")
        self.geometry("900x520")

        root = ttk.Frame(self, padding=10)
        root.pack(fill="both", expand=True)

        # Left: choose team, list players
        left = ttk.Frame(root)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        ttk.Label(left, text="Seleziona squadra e giocatore", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        self.teams = ttk.Treeview(left, columns=("id","nome"), show="headings", height=10)
        self.teams.heading("id", text="ID"); self.teams.column("id", width=60, anchor="w")
        self.teams.heading("nome", text="Nome"); self.teams.column("nome", width=220, anchor="w")
        self.teams.pack(fill="x")
        self.teams.bind("<<TreeviewSelect>>", lambda _e: self.refresh_players())

        self.players = ttk.Treeview(left, columns=("id","nome","cognome","ruolo","maglia"), show="headings", height=10)
        for c,t,w in [("id","ID",60),("nome","Nome",120),("cognome","Cognome",140),("ruolo","Ruolo",140),("maglia","Maglia",80)]:
            self.players.heading(c, text=t)
            self.players.column(c, width=w, anchor="w")
        self.players.pack(fill="x", pady=(10,0))
        self.players.bind("<<TreeviewSelect>>", lambda _e: self.load_selected_player())

        self.show_free = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            left,
            text="Mostra svincolati",
            variable=self.show_free,
            command=self.refresh_players
        ).pack(anchor="w", pady=(6, 0))

        ttk.Button(left, text="Aggiorna liste", command=self.refresh_all).pack(anchor="w", pady=8)


        # Right: edit form
        right = ttk.LabelFrame(root, text="Modifica giocatore selezionato", padding=10)
        right.pack(side="left", fill="both", expand=True)

        self.sel_player_id = None

        self.f_nome = tk.StringVar()
        self.f_cognome = tk.StringVar()
        self.f_ruolo = tk.StringVar(value=ROLES[0])
        self.f_maglia = tk.StringVar()
        self.f_new_team = tk.StringVar()

        self._row(right, "Nome", self.f_nome)
        self._row(right, "Cognome", self.f_cognome)
        self._row_combo(right, "Ruolo", self.f_ruolo, ROLES)
        self._row(right, "Maglia (1-99)", self.f_maglia)
        self._row(right, "Nuovo team ID (vuoto=svincola)", self.f_new_team)


        btns = ttk.Frame(right)
        btns.pack(fill="x", pady=10)
        ttk.Button(btns, text="Salva dati", command=self.update_player).pack(side="left")
        ttk.Button(btns, text="Trasferisci", command=self.transfer_player).pack(side="left", padx=6)

        self.refresh_all()

    def _row(self, parent, label, var):
        row = ttk.Frame(parent)
        row.pack(fill="x", pady=2)
        ttk.Label(row, text=label, width=28).pack(side="left")
        ttk.Entry(row, textvariable=var).pack(side="left", fill="x", expand=True)

    def _row_combo(self, parent, label, var, values):
        row = ttk.Frame(parent)
        row.pack(fill="x", pady=2)
        ttk.Label(row, text=label, width=28).pack(side="left")
        cb = ttk.Combobox(row, textvariable=var, values=values, state="readonly")
        cb.pack(side="left", fill="x", expand=True)


    def _clear(self, tree):
        for i in tree.get_children():
            tree.delete(i)

    def selected_team_id(self):
        sel = self.teams.selection()
        if not sel:
            return None
        return int(self.teams.item(sel[0], "values")[0])

    def refresh_all(self):
        self.refresh_teams()
        self.refresh_players()

    def refresh_teams(self):
        try:
            rows = self.api.list_teams()
        except ApiError as e:
            messagebox.showerror("Errore server", str(e))
            return
        self._clear(self.teams)
        for r in rows:
            self.teams.insert("", "end", values=(r[0], r[1]))

    def refresh_players(self):
        self._clear(self.players)

        try:
            if self.show_free.get():
                rows = self.api.list_free_agents()
            else:
                team_id = self.selected_team_id()
                if team_id is None:
                    return
                rows = self.api.list_players_by_team(team_id)
        except ApiError as e:
            messagebox.showerror("Errore server", str(e))
            return

        for r in rows:
            self.players.insert("", "end", values=(r[0], r[1], r[2], r[3], r[4]))


    def load_selected_player(self):
        sel = self.players.selection()
        if not sel:
            return
        values = self.players.item(sel[0], "values")
        self.sel_player_id = int(values[0])
        self.f_nome.set(values[1])
        self.f_cognome.set(values[2])
        self.f_ruolo.set(values[3])
        self.f_maglia.set(values[4])

    def update_player(self):
        if self.sel_player_id is None:
            messagebox.showinfo("Info", "Seleziona un giocatore.")
            return
        try:
            nome = self.f_nome.get().strip()
            cognome = self.f_cognome.get().strip()
            ruolo = self.f_ruolo.get().strip()
            maglia = int(self.f_maglia.get().strip())
            if not nome or not cognome or not ruolo:
                raise ValueError("Nome, cognome, ruolo obbligatori.")
            if not (1 <= maglia <= 99):
                raise ValueError("Maglia deve essere 1..99.")
            self.api.update_player(self.sel_player_id, nome, cognome, ruolo, maglia)
            messagebox.showinfo("OK", "Giocatore aggiornato.")
            self.refresh_players()
        except (ValueError, ApiError) as e:
            messagebox.showerror("Errore", str(e))

    def transfer_player(self):
        if self.sel_player_id is None:
            messagebox.showinfo("Info", "Seleziona un giocatore.")
            return
        try:
            raw = self.f_new_team.get().strip()
            new_team = int(raw) if raw else None
            self.api.transfer_player(self.sel_player_id, new_team)
            messagebox.showinfo("OK", "Trasferimento completato.")
            self.refresh_players()
        except (ValueError, ApiError) as e:
            messagebox.showerror("Errore", str(e))


class DeleteWindow(tk.Toplevel):
    def __init__(self, master, api: CampionatoAPI):
        super().__init__(master)
        self.api = api
        self.title("DELETE - Squadra / Giocatore")
        self.geometry("650x420")

        root = ttk.Frame(self, padding=12)
        root.pack(fill="both", expand=True)

        team = ttk.LabelFrame(root, text="Cancella squadra", padding=10)
        team.pack(fill="x")

        self.team_id = tk.StringVar()
        self._row(team, "ID squadra", self.team_id)
        ttk.Button(team, text="Cancella squadra", command=self.delete_team).pack(anchor="e", pady=(8, 0))

        player = ttk.LabelFrame(root, text="Cancella giocatore", padding=10)
        player.pack(fill="x", pady=12)

        self.player_id = tk.StringVar()
        self._row(player, "ID giocatore", self.player_id)
        ttk.Button(player, text="Cancella giocatore", command=self.delete_player).pack(anchor="e", pady=(8, 0))

    def _row(self, parent, label, var):
        row = ttk.Frame(parent)
        row.pack(fill="x", pady=2)
        ttk.Label(row, text=label, width=14).pack(side="left")
        ttk.Entry(row, textvariable=var).pack(side="left", fill="x", expand=True)

    def delete_team(self):
        try:
            team_id = int(self.team_id.get().strip())
            if not messagebox.askyesno("Conferma", "Cancellare squadra? (giocatori -> svincolati)"):
                return
            self.api.delete_team(team_id)
            messagebox.showinfo("OK", "Squadra cancellata.")
            self.team_id.set("")
        except (ValueError, ApiError) as e:
            messagebox.showerror("Errore", str(e))

    def delete_player(self):
        try:
            pid = int(self.player_id.get().strip())
            if not messagebox.askyesno("Conferma", "Cancellare giocatore?"):
                return
            self.api.delete_player(pid)
            messagebox.showinfo("OK", "Giocatore cancellato.")
            self.player_id.set("")
        except (ValueError, ApiError) as e:
            messagebox.showerror("Errore", str(e))


def main():
    api = CampionatoAPI(host="127.0.0.1", port=5000)

    root = tk.Tk()
    root.title("Campionato Serie A")
    root.geometry("1280x720")
    root.resizable(False, False)

    assets = Path(__file__).parent / "assets"
    bg = tk.PhotoImage(file=assets / "background_2.png")
    bg_label = tk.Label(root, image=bg)
    bg_label.place(x=0, y=0, relwidth=1, relheight=1)
    bg_label.image = bg

    dashboard = None  # will hold DashboardView

    def show_dashboard():
        nonlocal dashboard
        login.destroy()
        dashboard = DashboardView(root, api)

    login = LoginView(root, on_success=show_dashboard)
    login.place(relx=0.5, rely=0.5, anchor="center", width=410, height=220)

    root.mainloop()

if __name__ == "__main__":
    main()
