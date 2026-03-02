"""
Evidence pacientů – Python Tkinter + JSON
==========================================
Funkce:
 • Přidávání / odebírání pacientů
 • Validace vstupních údajů
 • Ukládání do JSON souboru
 • Řazení dle jména / věku / výšky / hmotnosti
 • Filtrování dle věku (<18, >50) a BMI kategorií
 • BMI výpis v novém formulářovém okně + výsečový graf (Canvas)
"""

import json
import os
import tkinter as tk
from tkinter import ttk, messagebox

# ---------------------------------------------------------------------------
# Datová vrstva
# ---------------------------------------------------------------------------

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pacienti.json")


def load_patients():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_patients(patients):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(patients, f, ensure_ascii=False, indent=2)




PI = 3.1415
CURRENT_YEAR = 0  


def _sin(x):
    """Sinus pomocí Taylorovy řady."""
    x = x % (2 * PI)
    if x > PI:
        x -= 2 * PI
    result = 0.0
    term = x
    for n in range(1, 15):
        result += term
        term *= -x * x / ((2 * n) * (2 * n + 1))
    return result


def _cos(x):
    """Kosinus pomocí Taylorovy řady."""
    return _sin(x + PI / 2)


def _radians(deg):
    return deg * PI / 180.0


def compute_age(birth_year):
    return CURRENT_YEAR - birth_year


def compute_bmi(weight_kg, height_cm):
    height_m = height_cm / 100.0
    return weight_kg / (height_m ** 2)


def bmi_category(bmi):
    if bmi < 18.5:
        return "Podváha"
    elif bmi < 25:
        return "Normální váha"
    else:
        return "Nadváha"

def draw_pie_chart(canvas, data, colors, cx, cy, radius):
    total = sum(data.values())
    if total == 0:
        canvas.create_text(cx, cy, text="Žádná data", font=("Segoe UI", 14))
        return

    x0, y0 = cx - radius, cy - radius
    x1, y1 = cx + radius, cy + radius


    nonzero = [(label, count) for label, count in data.items() if count > 0]

    if len(nonzero) == 1:
        label, count = nonzero[0]
        color = colors.get(label, "#999")
        canvas.create_oval(x0, y0, x1, y1, fill=color, outline="white", width=2)
        pct = 100.0
        canvas.create_text(
            cx, cy,
            text=f"{label}\n{pct:.1f} %\n({count})",
            font=("Segoe UI", 11, "bold"), fill="white", justify="center"
        )
    else:
        start_angle = 0.0
        for label, count in nonzero:
            extent = (count / total) * 360.0
            color = colors.get(label, "#999")

            canvas.create_arc(
                x0, y0, x1, y1,
                start=start_angle, extent=extent,
                fill=color, outline="white", width=2, style="pieslice"
            )

            # Popisek uprostřed výseče
            mid_angle = _radians(start_angle + extent / 2)
            pct = count / total * 100
            lbl_r = radius * 0.62
            lx = cx + lbl_r * _cos(mid_angle)
            ly = cy - lbl_r * _sin(mid_angle)
            canvas.create_text(
                lx, ly,
                text=f"{label}\n{pct:.1f} %\n({count})",
                font=("Segoe UI", 9, "bold"), fill="white", justify="center"
            )

            start_angle += extent

    canvas.create_text(cx, cy - radius - 24, text="Rozložení pacientů dle BMI",
                       font=("Segoe UI", 12, "bold"), fill="#1e3a5f")


# ---------------------------------------------------------------------------
# Hlavní okno aplikace
# ---------------------------------------------------------------------------

class PatientApp(tk.Tk):
    def __init__(self):
        super().__init__()

    
        global CURRENT_YEAR
        CURRENT_YEAR = int(self.tk.eval('clock format [clock seconds] -format %Y'))

        self.title("Evidence pacientů")
        self.geometry("960x640")
        self.minsize(800, 500)
        self.configure(bg="#f0f4f8")

        self.patients = load_patients()

        self._build_ui()
        self._refresh_table()

    # ---- Stavba UI --------------------------------------------------------

    def _build_ui(self):
        # -- Horní panel: formulář ------------------------------------------
        form_frame = tk.LabelFrame(
            self, text="  Nový pacient  ", font=("Segoe UI", 11, "bold"),
            bg="#f0f4f8", fg="#1e3a5f", padx=12, pady=8
        )
        form_frame.pack(fill="x", padx=12, pady=(12, 4))

        labels = ["Jméno:", "Rok narození:", "Výška (cm):", "Hmotnost (kg):"]
        self.entries = {}
        keys = ["jmeno", "rok_narozeni", "vyska", "hmotnost"]

        for i, (lbl, key) in enumerate(zip(labels, keys)):
            tk.Label(form_frame, text=lbl, font=("Segoe UI", 10),
                     bg="#f0f4f8", fg="#333").grid(row=0, column=i * 2, padx=(8, 2), pady=4, sticky="e")
            entry = tk.Entry(form_frame, font=("Segoe UI", 10), width=14, relief="solid", bd=1)
            entry.grid(row=0, column=i * 2 + 1, padx=(2, 8), pady=4)
            self.entries[key] = entry

        btn_add = tk.Button(
            form_frame, text="Přidat", font=("Segoe UI", 10, "bold"),
            bg="#2b7a4b", fg="white", activebackground="#236b3e",
            relief="flat", padx=14, pady=4, cursor="hand2",
            command=self._add_patient
        )
        btn_add.grid(row=0, column=8, padx=(16, 8), pady=4)

        btn_del = tk.Button(
            form_frame, text="Odebrat", font=("Segoe UI", 10, "bold"),
            bg="#c0392b", fg="white", activebackground="#a93226",
            relief="flat", padx=14, pady=4, cursor="hand2",
            command=self._remove_patient
        )
        btn_del.grid(row=0, column=9, padx=(4, 8), pady=4)

        # -- Střední panel: ovládání ----------------------------------------
        ctrl_frame = tk.Frame(self, bg="#f0f4f8")
        ctrl_frame.pack(fill="x", padx=12, pady=4)

        tk.Label(ctrl_frame, text="Řadit dle:", font=("Segoe UI", 10, "bold"),
                 bg="#f0f4f8", fg="#1e3a5f").pack(side="left", padx=(4, 4))

        sort_options = [("Jméno", "jmeno"), ("Věk", "vek"), ("Výška", "vyska"), ("Hmotnost", "hmotnost")]
        for label, key in sort_options:
            tk.Button(
                ctrl_frame, text=label, font=("Segoe UI", 9),
                bg="#3498db", fg="white", activebackground="#2980b9",
                relief="flat", padx=10, pady=2, cursor="hand2",
                command=lambda k=key: self._sort_by(k)
            ).pack(side="left", padx=2)

        ttk.Separator(ctrl_frame, orient="vertical").pack(side="left", fill="y", padx=10, pady=2)

        tk.Label(ctrl_frame, text="Filtr věk:", font=("Segoe UI", 10, "bold"),
                 bg="#f0f4f8", fg="#1e3a5f").pack(side="left", padx=(4, 4))

        tk.Button(
            ctrl_frame, text="< 18 let", font=("Segoe UI", 9),
            bg="#8e44ad", fg="white", activebackground="#7d3c98",
            relief="flat", padx=10, pady=2, cursor="hand2",
            command=lambda: self._filter_age("<18")
        ).pack(side="left", padx=2)

        tk.Button(
            ctrl_frame, text="> 50 let", font=("Segoe UI", 9),
            bg="#8e44ad", fg="white", activebackground="#7d3c98",
            relief="flat", padx=10, pady=2, cursor="hand2",
            command=lambda: self._filter_age(">50")
        ).pack(side="left", padx=2)

        ttk.Separator(ctrl_frame, orient="vertical").pack(side="left", fill="y", padx=10, pady=2)

        tk.Button(
            ctrl_frame, text="BMI analýza", font=("Segoe UI", 10, "bold"),
            bg="#e67e22", fg="white", activebackground="#d35400",
            relief="flat", padx=14, pady=2, cursor="hand2",
            command=self._open_bmi_window
        ).pack(side="left", padx=6)

        tk.Button(
            ctrl_frame, text="Zobrazit vše", font=("Segoe UI", 9),
            bg="#7f8c8d", fg="white", activebackground="#6c7a7d",
            relief="flat", padx=10, pady=2, cursor="hand2",
            command=self._refresh_table
        ).pack(side="right", padx=4)

        # -- Spodní panel: tabulka ------------------------------------------
        table_frame = tk.Frame(self, bg="#f0f4f8")
        table_frame.pack(fill="both", expand=True, padx=12, pady=(4, 12))

        columns = ("jmeno", "rok_narozeni", "vek", "vyska", "hmotnost", "bmi")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=18)

        headings = {
            "jmeno": "Jméno", "rok_narozeni": "Rok narození", "vek": "Věk",
            "vyska": "Výška (cm)", "hmotnost": "Hmotnost (kg)", "bmi": "BMI",
        }
        widths = {
            "jmeno": 200, "rok_narozeni": 110, "vek": 60,
            "vyska": 100, "hmotnost": 110, "bmi": 90,
        }
        for col in columns:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=widths[col], anchor="center" if col != "jmeno" else "w")

        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Treeview", font=("Segoe UI", 10), rowheight=26,
                        background="#ffffff", fieldbackground="#ffffff", foreground="#222")
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"),
                        background="#1e3a5f", foreground="white")
        style.map("Treeview", background=[("selected", "#d6eaf8")])

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Status bar
        self.status_var = tk.StringVar(value="Připraveno")
        tk.Label(self, textvariable=self.status_var, font=("Segoe UI", 9),
                 bg="#1e3a5f", fg="white", anchor="w", padx=10).pack(fill="x", side="bottom")

    # ---- Akce -------------------------------------------------------------

    def _add_patient(self):
        jmeno = self.entries["jmeno"].get().strip()
        rok_str = self.entries["rok_narozeni"].get().strip()
        vyska_str = self.entries["vyska"].get().strip()
        hmotnost_str = self.entries["hmotnost"].get().strip()

        if not jmeno:
            messagebox.showwarning("Chyba", "Zadejte jméno pacienta.")
            return

        try:
            rok = int(rok_str)
            if rok < 1900 or rok > CURRENT_YEAR:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Chyba", f"Rok narození musí být celé číslo v rozmezí 1900 - {CURRENT_YEAR}.")
            return

        try:
            vyska = float(vyska_str)
            if vyska <= 0 or vyska > 300:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Chyba", "Výška musí být kladné číslo (max 300 cm).")
            return

        try:
            hmotnost = float(hmotnost_str)
            if hmotnost <= 0 or hmotnost > 500:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Chyba", "Hmotnost musí být kladné číslo (max 500 kg).")
            return

        patient = {"jmeno": jmeno, "rok_narozeni": rok, "vyska": vyska, "hmotnost": hmotnost}
        self.patients.append(patient)
        save_patients(self.patients)

        for entry in self.entries.values():
            entry.delete(0, tk.END)

        self._refresh_table()
        self.status_var.set(f"Pacient \"{jmeno}\" přidán.  Celkem: {len(self.patients)}")

    def _remove_patient(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Info", "Nejprve vyberte pacienta v tabulce.")
            return

        idx = self.tree.index(selected[0])
        if hasattr(self, "_displayed_indices") and self._displayed_indices is not None:
            real_idx = self._displayed_indices[idx]
        else:
            real_idx = idx

        name = self.patients[real_idx]["jmeno"]
        if messagebox.askyesno("Potvrdit", f"Opravdu odebrat pacienta \"{name}\"?"):
            self.patients.pop(real_idx)
            save_patients(self.patients)
            self._refresh_table()
            self.status_var.set(f"Pacient \"{name}\" odebrán.  Celkem: {len(self.patients)}")

    # ---- Tabulka ----------------------------------------------------------

    def _refresh_table(self, data=None, indices=None):
        self.tree.delete(*self.tree.get_children())
        show = data if data is not None else self.patients
        self._displayed_indices = indices

        for p in show:
            age = compute_age(p["rok_narozeni"])
            bmi = compute_bmi(p["hmotnost"], p["vyska"])
            self.tree.insert("", "end", values=(
                p["jmeno"], p["rok_narozeni"], age,
                f'{p["vyska"]:.0f}', f'{p["hmotnost"]:.1f}', f'{bmi:.1f}'
            ))

        count = len(show)
        total = len(self.patients)
        if data is not None:
            self.status_var.set(f"Zobrazeno {count} z {total} pacientů  (filtr aktivní)")
        else:
            self.status_var.set(f"Celkem pacientů: {total}")

    # ---- Řazení -----------------------------------------------------------

    def _sort_by(self, key):
        if key == "jmeno":
            self.patients.sort(key=lambda p: p["jmeno"].lower())
        elif key == "vek":
            self.patients.sort(key=lambda p: compute_age(p["rok_narozeni"]))
        elif key == "vyska":
            self.patients.sort(key=lambda p: p["vyska"])
        elif key == "hmotnost":
            self.patients.sort(key=lambda p: p["hmotnost"])

        save_patients(self.patients)
        self._refresh_table()
        labels = {"jmeno": "jménu", "vek": "věku", "vyska": "výšce", "hmotnost": "hmotnosti"}
        self.status_var.set(f"Seřazeno dle {labels[key]}.  Celkem: {len(self.patients)}")

    # ---- Filtry -----------------------------------------------------------

    def _filter_age(self, mode):
        filtered = []
        indices = []
        for i, p in enumerate(self.patients):
            age = compute_age(p["rok_narozeni"])
            if mode == "<18" and age < 18:
                filtered.append(p)
                indices.append(i)
            elif mode == ">50" and age > 50:
                filtered.append(p)
                indices.append(i)

        label = "mladší 18 let" if mode == "<18" else "starší 50 let"
        self._refresh_table(filtered, indices)
        self.status_var.set(f"Filtr: {label} — nalezeno {len(filtered)} pacientů")

    # ---- BMI okno ---------------------------------------------------------

    def _open_bmi_window(self):
        if not self.patients:
            messagebox.showinfo("Info", "Nejsou žádní pacienti k analýze.")
            return

        win = tk.Toplevel(self)
        win.title("BMI analýza pacientů")
        win.geometry("1000x600")
        win.configure(bg="#f0f4f8")
        win.grab_set()

        # Grid layout – levý sloupec (tabulka) a pravý sloupec (graf)
        win.columnconfigure(0, weight=1, minsize=420)
        win.columnconfigure(1, weight=1, minsize=380)
        win.rowconfigure(0, weight=1)

        groups = {"Podváha": [], "Normální váha": [], "Nadváha": []}
        for p in self.patients:
            bmi = compute_bmi(p["hmotnost"], p["vyska"])
            cat = bmi_category(bmi)
            groups[cat].append({**p, "bmi": bmi})

        bmi_colors = {"Podváha": "#3498db", "Normální váha": "#27ae60", "Nadváha": "#e74c3c"}

        # --- Levý panel: tabulka ---
        left = tk.Frame(win, bg="#f0f4f8")
        left.grid(row=0, column=0, sticky="nsew", padx=(12, 4), pady=12)

        btn_frame = tk.Frame(left, bg="#f0f4f8")
        btn_frame.pack(fill="x", pady=(0, 6))

        for cat_name, color in bmi_colors.items():
            count = len(groups[cat_name])
            tk.Button(
                btn_frame, text=f"{cat_name} ({count})", font=("Segoe UI", 9, "bold"),
                bg=color, fg="white", relief="flat", padx=10, pady=3, cursor="hand2",
                command=lambda c=cat_name: _show_bmi_group(c)
            ).pack(side="left", padx=3)

        tk.Button(
            btn_frame, text="Všichni", font=("Segoe UI", 9),
            bg="#7f8c8d", fg="white", relief="flat", padx=10, pady=3, cursor="hand2",
            command=lambda: _show_bmi_group(None)
        ).pack(side="left", padx=3)

        cols = ("jmeno", "vek", "vyska", "hmotnost", "bmi", "kategorie")
        bmi_tree = ttk.Treeview(left, columns=cols, show="headings", height=16)
        head_map = {"jmeno": "Jméno", "vek": "Věk", "vyska": "Výška",
                    "hmotnost": "Hmotnost", "bmi": "BMI", "kategorie": "Kategorie"}
        w_map = {"jmeno": 150, "vek": 50, "vyska": 70, "hmotnost": 80, "bmi": 70, "kategorie": 110}
        for c in cols:
            bmi_tree.heading(c, text=head_map[c])
            bmi_tree.column(c, width=w_map[c], anchor="center" if c != "jmeno" else "w")
        bmi_tree.pack(fill="both", expand=True)

        def _show_bmi_group(cat_filter):
            bmi_tree.delete(*bmi_tree.get_children())
            for cat_name in ["Podváha", "Normální váha", "Nadváha"]:
                if cat_filter and cat_name != cat_filter:
                    continue
                for p in groups[cat_name]:
                    bmi_tree.insert("", "end", values=(
                        p["jmeno"], compute_age(p["rok_narozeni"]),
                        f'{p["vyska"]:.0f}', f'{p["hmotnost"]:.1f}',
                        f'{p["bmi"]:.1f}', cat_name
                    ))

        _show_bmi_group(None)

        # --- Pravý panel: výsečový graf (Canvas) ---
        right = tk.Frame(win, bg="#f0f4f8")
        right.grid(row=0, column=1, sticky="nsew", padx=(4, 12), pady=12)

        chart_canvas = tk.Canvas(right, bg="#f0f4f8", highlightthickness=0,
                                 width=360, height=400)
        chart_canvas.pack(fill="both", expand=True)

        pie_data = {}
        for cat_name in ["Podváha", "Normální váha", "Nadváha"]:
            pie_data[cat_name] = len(groups[cat_name])

        def _draw_chart(event=None):
            chart_canvas.delete("all")
            w = chart_canvas.winfo_width()
            h = chart_canvas.winfo_height()
            if w < 10 or h < 10:
                return
            cx, cy = w // 2, h // 2 + 10
            radius = min(w, h) // 2 - 40
            if radius < 40:
                radius = 40
            draw_pie_chart(chart_canvas, pie_data, bmi_colors, cx, cy, radius)

        chart_canvas.bind("<Configure>", _draw_chart)
        # Zajistit vykreslení i po prvním zobrazení okna
        win.after(100, _draw_chart)


if __name__ == "__main__":
    app = PatientApp()
    app.mainloop()
