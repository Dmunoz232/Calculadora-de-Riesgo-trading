import tkinter as tk
from tkinter import ttk
import math
import requests
import threading

# ── Paleta de colores ──────────────────────────────────────────────────────────
BG        = "#1a1a18"
SURFACE   = "#242422"
CARD      = "#2c2c2a"
BORDER    = "#3a3a38"
TEXT      = "#f0ede6"
TEXT_SEC  = "#888780"
GREEN     = "#5DCAA5"
GREEN_DIM = "#1d3d30"
RED       = "#F09595"
RED_DIM   = "#3d1d1d"
AMBER     = "#EF9F27"
ENTRY_BG  = "#1e1e1c"
ENTRY_FG  = "#f0ede6"
ACCENT    = "#7F77DD"

# ── Fuentes ───────────────────────────────────────────────────────────────────
FONT_BODY  = ("Helvetica", 11)
FONT_SMALL = ("Helvetica", 10)
FONT_LARGE = ("Helvetica", 16, "bold")
FONT_MED   = ("Helvetica", 13, "bold")
FONT_LABEL = ("Helvetica", 10)

# ── Ventana principal ─────────────────────────────────────────────────────────
root = tk.Tk()
root.title("Calculadora de Riesgo · Trading")
root.configure(bg=BG)
root.resizable(True, True)
root.minsize(680, 780)

# ── Variables reactivas ───────────────────────────────────────────────────────
v_entry     = tk.DoubleVar(value=100.0)
v_direction = tk.StringVar(value="long")
v_tp        = tk.DoubleVar(value=5.0)
v_sl        = tk.DoubleVar(value=2.0)
v_capital   = tk.DoubleVar(value=0.0)
v_cripto    = tk.StringVar(value="bitcoin")

# ── Helpers ───────────────────────────────────────────────────────────────────
def fmt(n):
    return f"${abs(n):,.2f}"

def fmt_signed(n):
    sign = "+" if n >= 0 else "-"
    return f"{sign}${abs(n):,.2f}"

def quality_label(ratio):
    if ratio >= 3:   return ("Excelente", GREEN)
    elif ratio >= 2: return ("Bueno",     GREEN)
    elif ratio >= 1: return ("Aceptable", AMBER)
    else:            return ("Desfavorable", RED)

# ── Canvas de barra visual ────────────────────────────────────────────────────
def draw_bar(canvas, entry, tp_price, sl_price, direction):
    canvas.delete("all")
    W = canvas.winfo_width()
    H = canvas.winfo_height()
    if W < 10 or H < 10:
        return

    lo = min(tp_price, sl_price)
    hi = max(tp_price, sl_price)
    pad = (hi - lo) * 0.25 if (hi - lo) > 0 else entry * 0.01
    lo -= pad
    hi += pad
    rng = hi - lo if (hi - lo) > 0 else 1

    def to_x(p):
        return ((p - lo) / rng) * (W - 40) + 20

    tp_x  = to_x(tp_price)
    sl_x  = to_x(sl_price)
    ent_x = to_x(entry)
    mid   = H // 2

    tp_color  = GREEN if direction == "long" else RED
    sl_color  = RED   if direction == "long" else GREEN
    tp_dim    = GREEN_DIM if direction == "long" else RED_DIM
    sl_dim    = RED_DIM   if direction == "long" else GREEN_DIM

    x0_tp = min(ent_x, tp_x)
    x1_tp = max(ent_x, tp_x)
    canvas.create_rectangle(x0_tp, mid-14, x1_tp, mid+14, fill=tp_dim, outline="")

    x0_sl = min(ent_x, sl_x)
    x1_sl = max(ent_x, sl_x)
    canvas.create_rectangle(x0_sl, mid-14, x1_sl, mid+14, fill=sl_dim, outline="")

    for x, price, color, label in [
        (sl_x,  sl_price,  sl_color,   "SL"),
        (ent_x, entry,     TEXT_SEC,   "Entrada"),
        (tp_x,  tp_price,  tp_color,   "TP"),
    ]:
        dash = () if x == ent_x else (4, 3)
        canvas.create_line(x, mid-18, x, mid+18, fill=color, width=2, dash=dash)
        canvas.create_text(x, mid-26, text=label,              fill=color, font=FONT_SMALL, anchor="center")
        canvas.create_text(x, mid+28, text=f"${price:.2f}",    fill=color, font=FONT_SMALL, anchor="center")

# ── Actualización reactiva ────────────────────────────────────────────────────
def calcular(*_):
    try:
        entry   = v_entry.get()
        tp_pct  = v_tp.get()
        sl_pct  = v_sl.get()
        try:
            capital = v_capital.get()
        except tk.TclError:
            capital = 0.0
        direc   = v_direction.get()
    except tk.TclError:
        return

    if direc == "long":
        tp_price = entry * (1 + tp_pct / 100)
        sl_price = entry * (1 - sl_pct / 100)
    else:
        tp_price = entry * (1 - tp_pct / 100)
        sl_price = entry * (1 + sl_pct / 100)

    tp_diff = tp_price - entry
    sl_diff = sl_price - entry
    ratio   = (tp_pct / sl_pct) if sl_pct > 0 else 0

    # Cards de precio
    lbl_entry_val.config(text=fmt(entry))
    lbl_tp_val.config(text=fmt(tp_price))
    lbl_sl_val.config(text=fmt(sl_price))
    lbl_tp_diff.config(text=fmt_signed(tp_diff))
    lbl_sl_diff.config(text=fmt_signed(sl_diff))

    # Ratio
    lbl_ratio_val.config(text=f"1 : {ratio:.2f}")
    q_text, q_color = quality_label(ratio)
    lbl_quality_val.config(text=q_text, fg=q_color)

    # Cálculo de ganancia/pérdida en USD y unidades
    if entry > 0:
        if capital > 0:
            units = capital / entry
            gain = units * abs(tp_diff)
            loss = units * abs(sl_diff)
            lbl_gain_destacado.config(text=fmt_signed(gain), fg=GREEN)
            lbl_loss_destacado.config(text=f"-{fmt(loss)}", fg=RED)
            lbl_units_val.config(text=f"{units:.8f} {v_cripto.get().capitalize()}")
        else:
            # capital es 0 o vacío: mostrar ceros
            lbl_gain_destacado.config(text="+$0.00", fg=GREEN)
            lbl_loss_destacado.config(text="-$0.00", fg=RED)
            lbl_units_val.config(text=f"0.00000000 {v_cripto.get().capitalize()}")
        # Mostrar el frame de resultados si aún no está visible
        try:
            frame_resultados.pack(fill="x", pady=(0, 14))
        except tk.TclError:
            pass  # ya está empacado
    else:
        # Ocultar resultados si el precio de entrada es inválido
        frame_resultados.pack_forget()

    # Barra visual
    root.after(10, lambda: draw_bar(bar_canvas, entry, tp_price, sl_price, direc))

def sync_tp_slider(val):
    # Limitar el valor máximo a 10
    new_val = min(10.0, max(0.1, float(val)))
    v_tp.set(round(new_val, 1))
    calcular()

def sync_sl_slider(val):
    # Limitar el valor máximo a 10
    new_val = min(10.0, max(0.1, float(val)))
    v_sl.set(round(new_val, 1))
    calcular()

# ── OBTENER PRECIO EN TIEMPO REAL (CoinGecko) ─────────────────────────────────
def fetch_price_thread():
    def task():
        try:
            coin_id = v_cripto.get().strip().lower()
            url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd"
            response = requests.get(url, timeout=8)
            data = response.json()
            if coin_id not in data:
                raise ValueError("Moneda no encontrada")
            price = data[coin_id]["usd"]
            root.after(0, lambda: v_entry.set(price))
            root.after(0, lambda: lbl_status.config(text=f"✓ Precio actual: ${price:,.2f}", fg=GREEN))
        except Exception as e:
            root.after(0, lambda: lbl_status.config(text=f"✗ Error: {e}", fg=RED))
    threading.Thread(target=task, daemon=True).start()

# ── Construcción de la UI ─────────────────────────────────────────────────────
outer = tk.Frame(root, bg=BG)
outer.pack(fill="both", expand=True, padx=24, pady=20)

def section_label(parent, text):
    tk.Label(parent, text=text, bg=BG, fg=TEXT_SEC, font=FONT_LABEL).pack(anchor="w", pady=(0, 4))

def styled_entry(parent, textvariable, width=14):
    e = tk.Entry(parent, textvariable=textvariable, bg=ENTRY_BG, fg=ENTRY_FG,
                 insertbackground=TEXT, relief="flat", font=FONT_BODY,
                 width=width, highlightthickness=1,
                 highlightbackground=BORDER, highlightcolor=ACCENT)
    return e

# ── Fila 0: Selector de cripto + botón precio real ────────────────────────────
row0 = tk.Frame(outer, bg=BG)
row0.pack(fill="x", pady=(0, 14))

col_selector = tk.Frame(row0, bg=BG)
col_selector.pack(side="left", fill="x", expand=True, padx=(0, 12))
section_label(col_selector, "Criptomoneda")
cripto_combo = ttk.Combobox(col_selector, textvariable=v_cripto,
                            values=["bitcoin", "ethereum", "solana", "cardano", "dogecoin", "ripple"],
                            state="readonly", font=FONT_BODY)
cripto_combo.pack(fill="x", ipady=4)
cripto_combo.bind("<<ComboboxSelected>>", lambda e: fetch_price_thread())

col_btn = tk.Frame(row0, bg=BG)
col_btn.pack(side="left", fill="x", expand=True)
section_label(col_btn, "Precio actual")
btn_fetch = tk.Button(col_btn, text="Obtener precio en tiempo real", command=fetch_price_thread,
                      bg=ACCENT, fg=TEXT, font=FONT_BODY, cursor="hand2", relief="flat", padx=12, pady=4)
btn_fetch.pack(fill="x")
lbl_status = tk.Label(col_btn, text="", bg=BG, fg=GREEN, font=FONT_SMALL)
lbl_status.pack(pady=(4,0))

# ── Fila 1: Precio + Dirección ────────────────────────────────────────────────
row1 = tk.Frame(outer, bg=BG)
row1.pack(fill="x", pady=(0, 14))

col_price = tk.Frame(row1, bg=BG)
col_price.pack(side="left", fill="x", expand=True, padx=(0, 12))
section_label(col_price, "Precio de entrada")
entry_frame = tk.Frame(col_price, bg=ENTRY_BG, highlightthickness=1,
                       highlightbackground=BORDER)
entry_frame.pack(fill="x")
tk.Label(entry_frame, text="$", bg=ENTRY_BG, fg=TEXT_SEC, font=FONT_BODY,
         padx=8).pack(side="left")
styled_entry(entry_frame, v_entry, width=12).pack(side="left", fill="x", expand=True, ipady=4)

col_dir = tk.Frame(row1, bg=BG)
col_dir.pack(side="left", fill="x", expand=True)
section_label(col_dir, "Dirección")
dir_frame = tk.Frame(col_dir, bg=CARD, highlightthickness=1, highlightbackground=BORDER)
dir_frame.pack(fill="x")

def make_dir_btn(parent, text, value):
    def select():
        v_direction.set(value)
        for b, v in dir_buttons:
            if v == value:
                b.config(bg=ACCENT, fg=TEXT, relief="flat")
            else:
                b.config(bg=CARD, fg=TEXT_SEC, relief="flat")
        calcular()
    btn = tk.Button(parent, text=text, command=select, bg=CARD, fg=TEXT_SEC,
                    font=FONT_BODY, relief="flat", bd=0, padx=12, pady=6,
                    cursor="hand2", activebackground=SURFACE, activeforeground=TEXT)
    return btn

btn_long  = make_dir_btn(dir_frame, "Long (compra)", "long")
btn_short = make_dir_btn(dir_frame, "Short (venta)", "short")
btn_long.pack(side="left", fill="x", expand=True)
btn_short.pack(side="left", fill="x", expand=True)
dir_buttons = [(btn_long, "long"), (btn_short, "short")]
btn_long.config(bg=ACCENT, fg=TEXT)

# ── Fila 2: TP + SL sliders (rango máximo 10%) ────────────────────────────────
row2 = tk.Frame(outer, bg=BG)
row2.pack(fill="x", pady=(0, 14))

def slider_block(parent, label, var, from_, to, sync_fn):
    col = tk.Frame(parent, bg=BG)
    col.pack(side="left", fill="x", expand=True, padx=(0, 12))
    section_label(col, label)
    inner = tk.Frame(col, bg=BG)
    inner.pack(fill="x")
    slider = ttk.Scale(inner, from_=from_, to=to, variable=var, orient="horizontal",
                       command=sync_fn)
    slider.pack(side="left", fill="x", expand=True, padx=(0, 8))
    pct_frame = tk.Frame(inner, bg=ENTRY_BG, highlightthickness=1,
                         highlightbackground=BORDER)
    pct_frame.pack(side="left")
    e = styled_entry(pct_frame, var, width=5)
    e.pack(side="left", ipady=4, padx=(6, 0))
    e.bind("<Return>", calcular)
    e.bind("<FocusOut>", calcular)
    tk.Label(pct_frame, text="%", bg=ENTRY_BG, fg=TEXT_SEC, font=FONT_BODY,
             padx=6).pack(side="left")
    return col

# Cambiamos el rango máximo a 10 para ambos sliders
slider_block(row2, "Take profit (%)", v_tp, 0.1, 10.0, sync_tp_slider)
slider_block(row2, "Stop loss (%)",   v_sl, 0.1, 10.0, sync_sl_slider)

# ── Fila 3: Capital invertido ─────────────────────────────────────────────────
row3 = tk.Frame(outer, bg=BG)
row3.pack(fill="x", pady=(0, 14))
section_label(row3, "Capital invertido (USD)")
cap_input = tk.Frame(row3, bg=ENTRY_BG, highlightthickness=1,
                     highlightbackground=BORDER)
cap_input.pack(side="left")
tk.Label(cap_input, text="$", bg=ENTRY_BG, fg=TEXT_SEC, font=FONT_BODY,
         padx=8).pack(side="left")
ce = styled_entry(cap_input, v_capital, width=14)
ce.pack(side="left", ipady=4)
ce.bind("<Return>", calcular)
ce.bind("<FocusOut>", calcular)

# ── Fila 4: Cards de precio ───────────────────────────────────────────────────
row4 = tk.Frame(outer, bg=BG)
row4.pack(fill="x", pady=(0, 14))

def price_card(parent, title, title_color, bg_color, border_color):
    c = tk.Frame(parent, bg=bg_color, highlightthickness=1,
                 highlightbackground=border_color, padx=16, pady=12)
    c.pack(side="left", fill="x", expand=True, padx=(0, 8))
    tk.Label(c, text=title, bg=bg_color, fg=title_color,
             font=FONT_SMALL).pack(anchor="center")
    val_lbl = tk.Label(c, text="$0.00", bg=bg_color, fg=title_color, font=FONT_LARGE)
    val_lbl.pack(anchor="center", pady=(4, 0))
    diff_lbl = tk.Label(c, text="", bg=bg_color, fg=title_color, font=FONT_SMALL)
    diff_lbl.pack(anchor="center", pady=(2, 0))
    return val_lbl, diff_lbl

lbl_entry_val, _ = price_card(row4, "Entrada",     TEXT,  CARD,      BORDER)
lbl_tp_val,   lbl_tp_diff = price_card(row4, "Take profit", GREEN, GREEN_DIM, GREEN)
lbl_sl_val,   lbl_sl_diff = price_card(row4, "Stop loss",   RED,   RED_DIM,   RED)

# ── Fila 5: Estadísticas (Ratio + Calidad) ────────────────────────────────────
row5 = tk.Frame(outer, bg=SURFACE, highlightthickness=1,
                highlightbackground=BORDER, padx=16, pady=12)
row5.pack(fill="x", pady=(0, 14))

def stat_cell(parent, label, side="left"):
    cell = tk.Frame(parent, bg=SURFACE)
    cell.pack(side=side, fill="x", expand=True)
    tk.Label(cell, text=label, bg=SURFACE, fg=TEXT_SEC, font=FONT_SMALL).pack()
    val = tk.Label(cell, text="—", bg=SURFACE, fg=TEXT, font=FONT_MED)
    val.pack(pady=(2, 0))
    return val

lbl_ratio_val   = stat_cell(row5, "Ratio riesgo/beneficio")
lbl_quality_val = stat_cell(row5, "Calidad del setup")

# ── Fila 6: RESULTADOS DESTACADOS (Ganancia / Pérdida) ────────────────────────
frame_resultados = tk.Frame(outer, bg=SURFACE, highlightthickness=1, highlightbackground=BORDER, padx=16, pady=12)
# NO empaquetar aquí, se hará dinámicamente en calcular()

row_result = tk.Frame(frame_resultados, bg=SURFACE)
row_result.pack(fill="x", expand=True)

col_gain = tk.Frame(row_result, bg=SURFACE)
col_gain.pack(side="left", fill="x", expand=True, padx=(0, 8))
tk.Label(col_gain, text=" GANANCIA SI TP ALCANZADO", bg=SURFACE, fg=GREEN, font=FONT_MED).pack()
lbl_gain_destacado = tk.Label(col_gain, text="+$0.00", bg=SURFACE, fg=GREEN, font=("Helvetica", 20, "bold"))
lbl_gain_destacado.pack(pady=5)

col_loss = tk.Frame(row_result, bg=SURFACE)
col_loss.pack(side="left", fill="x", expand=True)
tk.Label(col_loss, text=" PÉRDIDA SI SL ALCANZADO", bg=SURFACE, fg=RED, font=FONT_MED).pack()
lbl_loss_destacado = tk.Label(col_loss, text="-$0.00", bg=SURFACE, fg=RED, font=("Helvetica", 20, "bold"))
lbl_loss_destacado.pack(pady=5)

tk.Frame(frame_resultados, height=2, bg=BORDER).pack(fill="x", pady=8)
units_frame = tk.Frame(frame_resultados, bg=SURFACE)
units_frame.pack(fill="x")
tk.Label(units_frame, text="Unidades a comprar:", bg=SURFACE, fg=TEXT_SEC, font=FONT_BODY).pack(side="left")
lbl_units_val = tk.Label(units_frame, text="—", bg=SURFACE, fg=ACCENT, font=FONT_BODY)
lbl_units_val.pack(side="left", padx=(5,0))

# ── Barra visual ──────────────────────────────────────────────────────────────
tk.Label(outer, text="Visualización de niveles", bg=BG, fg=TEXT_SEC,
         font=FONT_LABEL).pack(anchor="w", pady=(0, 4))
bar_canvas = tk.Canvas(outer, height=80, bg=SURFACE,
                       highlightthickness=1, highlightbackground=BORDER)
bar_canvas.pack(fill="x", pady=(0, 4))
bar_canvas.bind("<Configure>", calcular)

# ── Estilos ttk ───────────────────────────────────────────────────────────────
style = ttk.Style()
style.theme_use("clam")
style.configure("Horizontal.TScale",
                background=BG,
                troughcolor=BORDER,
                sliderthickness=16,
                sliderrelief="flat")
style.configure("TCombobox", fieldbackground=ENTRY_BG, background=ENTRY_BG,
                foreground=TEXT, arrowcolor=TEXT)

# ── Bind cambios globales ─────────────────────────────────────────────────────
v_entry.trace_add("write", calcular)
v_capital.trace_add("write", calcular)

# ── Título ────────────────────────────────────────────────────────────────────
header = tk.Frame(root, bg=BG)
header.pack(before=outer, fill="x", padx=24, pady=(20, 0))
tk.Label(header, text="CALCULADORA DE RIESGO",
         bg=BG, fg=TEXT, font=("Helvetica", 14, "bold")).pack(side="left")
tk.Label(header, text="· trading con precios reales",
         bg=BG, fg=ACCENT, font=("Helvetica", 14)).pack(side="left", padx=(4, 0))

calcular()
root.mainloop()
