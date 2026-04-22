import tkinter as tk
from tkinter import ttk
import math

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

# ── NUEVO ESTILO DE LETRA (Helvetica sans-serif) ──────────────────────────────
FONT_BODY  = ("Helvetica", 11)
FONT_SMALL = ("Helvetica", 10)
FONT_LARGE = ("Helvetica", 16, "bold")
FONT_MED   = ("Helvetica", 13, "bold")
FONT_LABEL = ("Helvetica", 10)

# ── Ventana principal ──────────────────────────────────────────────────────────
root = tk.Tk()
root.title("Calculadora de Riesgo · Trading")
root.configure(bg=BG)
root.resizable(True, True)
root.minsize(640, 700)

# Variables reactivas
v_entry     = tk.DoubleVar(value=100.0)
v_direction = tk.StringVar(value="long")
v_tp        = tk.DoubleVar(value=5.0)
v_sl        = tk.DoubleVar(value=2.0)
v_capital   = tk.DoubleVar(value=0.0)

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

    # Zona TP
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

    # Líneas verticales
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
        capital = v_capital.get()
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

    # Capital
    if capital > 0:
        units    = capital / entry if entry > 0 else 0
        gain     = units * abs(tp_diff)
        loss     = units * abs(sl_diff)
        lbl_gain_val.config(text=fmt_signed(gain))
        lbl_loss_val.config(text=f"-{fmt(loss)}")
        frame_capital.grid()
    else:
        frame_capital.grid_remove()

    # Barra visual
    root.after(10, lambda: draw_bar(bar_canvas, entry, tp_price, sl_price, direc))

def sync_tp_slider(val):
    v_tp.set(round(float(val), 1))
    calcular()

def sync_sl_slider(val):
    v_sl.set(round(float(val), 1))
    calcular()

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

def card(parent, **kwargs):
    return tk.Frame(parent, bg=CARD, relief="flat",
                    highlightthickness=1, highlightbackground=BORDER, **kwargs)

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

# ── Fila 2: TP + SL sliders ───────────────────────────────────────────────────
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

slider_block(row2, "Take profit (%)", v_tp, 0.1, 100, sync_tp_slider)
slider_block(row2, "Stop loss (%)",   v_sl, 0.1, 50,  sync_sl_slider)

# ── Capital ───────────────────────────────────────────────────────────────────
row3 = tk.Frame(outer, bg=BG)
row3.pack(fill="x", pady=(0, 14))
section_label(row3, "Capital invertido")
cap_input = tk.Frame(row3, bg=ENTRY_BG, highlightthickness=1,
                     highlightbackground=BORDER)
cap_input.pack(side="left")
tk.Label(cap_input, text="$", bg=ENTRY_BG, fg=TEXT_SEC, font=FONT_BODY,
         padx=8).pack(side="left")
ce = styled_entry(cap_input, v_capital, width=14)
ce.pack(side="left", ipady=4)
ce.bind("<Return>", calcular)
ce.bind("<FocusOut>", calcular)

# ── Cards de precio ───────────────────────────────────────────────────────────
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
_ = _  # no diff for entry
lbl_tp_val,   lbl_tp_diff = price_card(row4, "Take profit", GREEN, GREEN_DIM, GREEN)
lbl_sl_val,   lbl_sl_diff = price_card(row4, "Stop loss",   RED,   RED_DIM,   RED)

# sin diff en entrada — sobreescribimos para silenciar
_ = lbl_entry_val.master.winfo_children()

# ── Barra de stats ────────────────────────────────────────────────────────────
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

frame_capital = tk.Frame(row5, bg=SURFACE)
frame_capital.pack(side="left", fill="x", expand=True)
lbl_gain_val = tk.Label(frame_capital, text="—", bg=SURFACE, fg=GREEN, font=FONT_MED)
lbl_loss_val = tk.Label(frame_capital, text="—", bg=SURFACE, fg=RED,   font=FONT_MED)
tk.Label(frame_capital, text="Ganancia potencial", bg=SURFACE, fg=TEXT_SEC, font=FONT_SMALL).pack()
lbl_gain_val.pack()
tk.Label(frame_capital, text="Pérdida máxima",    bg=SURFACE, fg=TEXT_SEC, font=FONT_SMALL).pack(pady=(4,0))
lbl_loss_val.pack()
frame_capital.grid_remove()  # oculto hasta que haya capital

# ── Barra visual ──────────────────────────────────────────────────────────────
tk.Label(outer, text="Visualización de niveles", bg=BG, fg=TEXT_SEC,
         font=FONT_LABEL).pack(anchor="w", pady=(0, 4))

bar_canvas = tk.Canvas(outer, height=80, bg=SURFACE,
                       highlightthickness=1, highlightbackground=BORDER)
bar_canvas.pack(fill="x", pady=(0, 4))
bar_canvas.bind("<Configure>", calcular)

# ── Estilos ttk ──────────────────────────────────────────────────────────────
style = ttk.Style()
style.theme_use("clam")
style.configure("Horizontal.TScale",
                background=BG,
                troughcolor=BORDER,
                sliderthickness=16,
                sliderrelief="flat")

# ── Bind cambios globales ──────────────────────────────────────────────────────
v_entry.trace_add("write", calcular)
v_capital.trace_add("write", calcular)

# ── Título ────────────────────────────────────────────────────────────────────
header = tk.Frame(root, bg=BG)
header.pack(before=outer, fill="x", padx=24, pady=(20, 0))
tk.Label(header, text="CALCULADORA DE RIESGO",
         bg=BG, fg=TEXT, font=("Helvetica", 14, "bold")).pack(side="left")
tk.Label(header, text="· trading",
         bg=BG, fg=ACCENT, font=("Helvetica", 14)).pack(side="left", padx=(4, 0))

calcular()
root.mainloop()