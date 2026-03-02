import tkinter as tk
from tkinter import messagebox
import json
from typing import Any

SOUBOR = "pacienti.json"
AKTUALNI_ROK = 2026

def nacti_data() -> list[dict[str, Any]]:
    try:
        with open(SOUBOR, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def uloz_data(data: list[dict[str, Any]]) -> None:
    with open(SOUBOR, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def pridej_pacienta() -> None:
    jmeno = entry_jmeno.get().strip()
    
    if not jmeno:
        messagebox.showerror("Chyba", "Jméno nesmí být prázdné!")
        return

    try:
        rok = int(entry_rok.get())
        vyska = float(entry_vyska.get())
        hmotnost = float(entry_hmotnost.get())

        if not (1900 <= rok <= AKTUALNI_ROK):
            raise ValueError()
        if not (40 <= vyska <= 250):
            raise ValueError()
        if not (2 <= hmotnost <= 300):
            raise ValueError()
            
    except ValueError:
        messagebox.showerror("Chyba", "Zkontrolujte čísla (rok: 1900-2026, výška: 40-250cm, váha: 2-300kg).")
        return

    pacienti = nacti_data()
    pacienti.append({
        "jmeno": jmeno,
        "rok": rok,
        "vyska": vyska,
        "hmotnost": hmotnost
    })
    uloz_data(pacienti)
    
    entry_jmeno.delete(0, tk.END)
    entry_rok.delete(0, tk.END)
    entry_vyska.delete(0, tk.END)
    entry_hmotnost.delete(0, tk.END)
    
    zobraz_pacienty()

def odeber_pacienta() -> None:
    vyber = listbox.curselection()
    if not vyber:
        messagebox.showwarning("Varování", "Vyberte pacienta ze seznamu k odstranění.")
        return
    
    index = vyber[0]
    pacienti = nacti_data()
    
    hodnota = listbox.get(index)
    jmeno_k_smazani = hodnota.split(" | ")[0]
    
    pacienti = [p for p in pacienti if p.get("jmeno") != jmeno_k_smazani]
    uloz_data(pacienti)
    zobraz_pacienty()

def zobraz_pacienty(razeni: str | None = None, filtr: str | None = None) -> None:
    listbox.delete(0, tk.END)
    vsichni_pacienti = nacti_data()
    
    platni_pacienti = []
    for p in vsichni_pacienti:
        if p.get("rok") is not None and p.get("vyska") is not None and p.get("hmotnost") is not None:
            platni_pacienti.append(p)

    match filtr:
        case "mladsi_18":
            platni_pacienti = [p for p in platni_pacienti if (AKTUALNI_ROK - p["rok"]) < 18]
        case "starsi_50":
            platni_pacienti = [p for p in platni_pacienti if (AKTUALNI_ROK - p["rok"]) > 50]
        case _:
            pass

    match razeni:
        case "jmeno":
            platni_pacienti.sort(key=lambda x: x["jmeno"])
        case "vek":
            platni_pacienti.sort(key=lambda x: AKTUALNI_ROK - x["rok"])
        case "hmotnost":
            platni_pacienti.sort(key=lambda x: x["hmotnost"])
        case "vyska":
            platni_pacienti.sort(key=lambda x: x["vyska"])
        case _:
            pass

    for p in platni_pacienti:
        vek = AKTUALNI_ROK - p["rok"]
        radek = f"{p["jmeno"]} | Věk: {vek} | Výška: {p["vyska"]} cm | Váha: {p["hmotnost"]} kg"
        listbox.insert(tk.END, radek)

def otevri_bmi_okno() -> None:
    bmi_okno = tk.Toplevel(root)
    bmi_okno.title("Výpis podle BMI")
    bmi_okno.geometry("500x400")
    
    tk.Label(bmi_okno, text="Pacienti rozdělení podle BMI", font=("Arial", 14, "bold")).pack(pady=10)
    bmi_listbox = tk.Listbox(bmi_okno, width=60, height=15)
    bmi_listbox.pack(pady=10)
    
    pacienti = nacti_data()
    podvaha = normal = nadvaha = 0
    
    for p in pacienti:
        if p.get("vyska") is None or p.get("hmotnost") is None:
            continue

        vyska_m = p["vyska"] / 100
        bmi = p["hmotnost"] / (vyska_m ** 2)
        
        if bmi < 18.5:
            kategorie = "Podváha"
            podvaha += 1
        elif 18.5 <= bmi <= 25:
            kategorie = "Normální"
            normal += 1
        else:
            kategorie = "Nadváha"
            nadvaha += 1
            
        radek = f"{p.get("jmeno", "Neznámý")} | BMI: {bmi:.1f} ({kategorie})"
        bmi_listbox.insert(tk.END, radek)
        
    shrnut_text = f"Statistika:\nPodváha: {podvaha}\nNormální: {normal}\nNadváha: {nadvaha}"
    tk.Label(bmi_okno, text=shrnut_text, justify=tk.LEFT, font=("Arial", 12)).pack(pady=10)

root = tk.Tk()
root.title("Evidence pacientů")
root.geometry("650x600")

frame_form = tk.Frame(root)
frame_form.pack(pady=10)

tk.Label(frame_form, text="Jméno:").grid(row=0, column=0, padx=5, pady=5)
entry_jmeno = tk.Entry(frame_form)
entry_jmeno.grid(row=0, column=1)

tk.Label(frame_form, text="Rok narození:").grid(row=1, column=0, padx=5, pady=5)
entry_rok = tk.Entry(frame_form)
entry_rok.grid(row=1, column=1)

tk.Label(frame_form, text="Výška (cm):").grid(row=2, column=0, padx=5, pady=5)
entry_vyska = tk.Entry(frame_form)
entry_vyska.grid(row=2, column=1)

tk.Label(frame_form, text="Hmotnost (kg):").grid(row=3, column=0, padx=5, pady=5)
entry_hmotnost = tk.Entry(frame_form)
entry_hmotnost.grid(row=3, column=1)

tk.Button(frame_form, text="Přidat pacienta", command=pridej_pacienta, bg="lightgreen").grid(row=4, column=0, columnspan=2, pady=10, sticky="we")
tk.Button(root, text="Odebrat vybraného pacienta", command=odeber_pacienta, bg="salmon").pack(pady=5)

frame_ovladani = tk.Frame(root)
frame_ovladani.pack(pady=10)

tk.Label(frame_ovladani, text="Řadit podle:").grid(row=0, column=0, padx=5)
tk.Button(frame_ovladani, text="Jména", command=lambda: zobraz_pacienty(razeni="jmeno")).grid(row=0, column=1, padx=2)
tk.Button(frame_ovladani, text="Věku", command=lambda: zobraz_pacienty(razeni="vek")).grid(row=0, column=2, padx=2)
tk.Button(frame_ovladani, text="Výšky", command=lambda: zobraz_pacienty(razeni="vyska")).grid(row=0, column=3, padx=2)
tk.Button(frame_ovladani, text="Hmotnosti", command=lambda: zobraz_pacienty(razeni="hmotnost")).grid(row=0, column=4, padx=2)

tk.Label(frame_ovladani, text="Filtry:").grid(row=1, column=0, padx=5, pady=5)
tk.Button(frame_ovladani, text="Všichni", command=lambda: zobraz_pacienty()).grid(row=1, column=1, padx=2)
tk.Button(frame_ovladani, text="< 18 let", command=lambda: zobraz_pacienty(filtr="mladsi_18")).grid(row=1, column=2, padx=2)
tk.Button(frame_ovladani, text="> 50 let", command=lambda: zobraz_pacienty(filtr="starsi_50")).grid(row=1, column=3, padx=2)

listbox = tk.Listbox(root, width=75, height=10)
listbox.pack(pady=10)

tk.Button(root, text="Otevřít okno s výpočty BMI", command=otevri_bmi_okno, font=("Arial", 10, "bold"), bg="lightblue").pack(pady=10)

zobraz_pacienty()

root.mainloop()