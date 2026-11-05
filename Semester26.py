"""Boligprisestimat for Bergen og Stavanger (klikk i kartet).

Nytt i denne versjonen:
  - flere byer, med egne modeller (beste modell velges automatisk per by)
  - ekte koordinater: aksene viser breddegrad/lengdegrad, og målestokk i km
  - stolpediagram farget etter standard, referanselinje for 100 m² og grid
  - m²-slider og infoboks med posisjon, totalpris og modell (MAE / R²)
"""
import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from matplotlib.widgets import RadioButtons, Slider
from matplotlib.patches import Rectangle

from Semester26_Model import load_models
from Semester26_Lage_Huspriser import standard_score
from geo import GEO

HERE = os.path.dirname(os.path.abspath(__file__))
MODELS = load_models(os.path.join(HERE, "House_Prices_v2.csv"))
CITY_MAPS = {"Bergen": "Semester26_Bergen.jpg", "Stavanger": "Semester26_Stavanger.png"}
HOUSE_TYPES = {"Enebolig": 1, "Rekke": 2, "Leilighet": 3}
STD_CMAP = plt.get_cmap("RdYlGn")                                      # standard 1 -> 4 : rød -> grønn
M2_LIST = [50, 100, 150, 200]
BG = "#f4f6f8"

state = {"city": "Bergen", "house_type": 1, "year_built": 1990, "last_renovated": 2010, "renovation_price": 500, "m2": 100, "point": (41, 57)}
_images = {}


def load_map(city):
    if city not in _images:
        path = os.path.join(HERE, CITY_MAPS[city])
        if os.path.exists(path):
            img = mpimg.imread(path)
            g = GEO[city]
            if abs(img.shape[0] - g.h) > 1:          # Bergen: fjern bunnteksten (målestokk/logo)
                img = img[:g.h]
        else:                                        # fallback hvis kartbilde mangler
            img = np.dstack([np.linspace(0.85, 0.7, 100)[:, None] * np.ones((100, 100))] * 3)
        _images[city] = img
    return _images[city]


def current_standard(m2=None):
    return standard_score(state["year_built"], state["last_renovated"], state["renovation_price"], m2 or state["m2"])


def price_per_m2(m2):
    x, y = state["point"]
    return 1000 * MODELS[state["city"]].predict(x, y, m2, state["house_type"],
                                           state["year_built"], state["last_renovated"], state["renovation_price"]) / m2  # data i 1000 kr


def draw_scale_bar(geo, km):
    """Målestokklinje nederst til venstre i kartet (lengde i km)."""
    w_pct, _ = geo.km_to_xy(km)
    ax_map.add_patch(Rectangle((3, 2), w_pct + 3, 7, transform=ax_map.transData, facecolor="white", alpha=0.8, zorder=3))
    ax_map.plot([4.5, 4.5 + w_pct], [4.5, 4.5], color="black", lw=3, zorder=4)
    ax_map.text(4.5 + w_pct / 2, 6.3, f"{km} km", ha="center", fontsize=9, zorder=4)


def draw():
    city = state["city"]
    geo = GEO[city]
    img = load_map(city)
    h, w = img.shape[:2]
    x, y = state["point"]
    lat, lon = geo.xy_to_latlon(x, y)

    # ---- kart ----
    ax_map.cla()
    ax_map.imshow(img, extent=(0, 100, 0, 100), aspect="auto")
    ax_map.set_box_aspect(h / w)                       # riktig sideforhold per by
    ax_map.set_title(city, fontsize=14)
    # akser i breddegrad/lengdegrad
    xt, yt = np.linspace(0, 100, 5), np.linspace(0, 100, 5)
    ax_map.set_xticks(xt)
    ax_map.set_yticks(yt)
    ax_map.set_xticklabels([f"{geo.xy_to_latlon(v, 50)[1]:.2f}°Ø" for v in xt], fontsize=8)
    ax_map.set_yticklabels([f"{geo.xy_to_latlon(50, v)[0]:.2f}°N" for v in yt], fontsize=8)
    ax_map.grid(True, color="white", alpha=0.35, lw=0.6)
    draw_scale_bar(geo, 5 if geo.width_km > 20 else 2)

    cur = price_per_m2(state["m2"])
    ax_map.scatter(x, y, marker="+", c="blue", s=200, zorder=5)
    ax_map.text(min(x + 3, 70), max(y - 4, 12), f"{round(cur, -2):,.0f} kr/m²".replace(",", " "), color="blue",
                fontsize=12, zorder=5, bbox=dict(facecolor="white", alpha=0.8, edgecolor="none"))

    # ---- stolpediagram ----
    prices = [price_per_m2(m) for m in M2_LIST]
    ref = price_per_m2(100)
    ax_bar.cla()
    ax_bar.bar([str(m) for m in M2_LIST], prices, color=STD_CMAP((current_standard() - 1) / 3), width=0.6)
    ax_bar.axhline(ref, color="black", ls="--", label=f"100 m²: {ref:,.0f} kr".replace(",", " "))
    ax_bar.set_ylim(0, max(prices + [ref]) * 1.25)
    ax_bar.yaxis.set_major_formatter(lambda v, _: f"{v / 1000:.0f}k")
    ax_bar.set_axisbelow(True)
    ax_bar.grid(True, axis="y", alpha=0.4)
    ax_bar.set_xlabel("m²")
    ax_bar.set_ylabel("kr per m²")
    ax_bar.set_title("Pris per m²", fontsize=10)
    ax_bar.legend(loc="upper right", fontsize=8)

    # ---- infoboks ----
    m = MODELS[city]
    total = cur * state["m2"]
    ax_info.cla()
    ax_info.axis("off")
    ax_info.text(0, 1, f"Posisjon: {lat:.4f}°N, {lon:.4f}°Ø\n"
                       f"Bolig: {state['m2']} m²  ->  {total / 1e6:.2f} mill. kr\n"
                       f"Standard: {current_standard():.1f} / 4\n"
                       f"Modell: {m.best_kind}, grad {m.best_degree}\n"
                       f"Test:  MAE {m.best_mae:,.0f}   R² {m.best_r2:.3f}".replace(",", " "),
                 va="top", fontsize=9, family="monospace", transform=ax_info.transAxes)
    fig.canvas.draw_idle()


def on_click(event):
    if event.inaxes is ax_map and event.xdata is not None:
        state["point"] = (event.xdata, event.ydata)
        draw()


def set_state(key, mapping):
    def cb(label):
        state[key] = mapping[label]
        draw()
    return cb


def on_city(city):
    state["city"] = city
    state["point"] = (41, 57) if city == "Bergen" else (47, 65)       # start i sentrum
    draw()


fig = plt.figure(figsize=(11, 7.5), facecolor=BG)
fig.suptitle("Boligpriser per m²", fontsize=20, y=0.97)
ax_city = fig.add_axes((0.03, 0.82, 0.22, 0.09), facecolor=BG)
ax_type = fig.add_axes((0.03, 0.66, 0.22, 0.13), facecolor=BG)
ax_built = fig.add_axes((0.10, 0.60, 0.15, 0.02), facecolor=BG)
ax_reno = fig.add_axes((0.10, 0.56, 0.15, 0.02), facecolor=BG)
ax_rprice = fig.add_axes((0.10, 0.52, 0.15, 0.02), facecolor=BG)
ax_slider = fig.add_axes((0.10, 0.47, 0.17, 0.02), facecolor=BG)
ax_bar = fig.add_axes((0.06, 0.20, 0.19, 0.17))
ax_info = fig.add_axes((0.03, 0.01, 0.30, 0.09))
ax_map = fig.add_axes((0.36, 0.08, 0.60, 0.82))

rb_city = RadioButtons(ax_city, list(CITY_MAPS))
rb_type = RadioButtons(ax_type, list(HOUSE_TYPES))
sl_built = Slider(ax_built, "Bygget", 1900, 2025, valinit=state["year_built"], valstep=1, valfmt="%d")
sl_reno = Slider(ax_reno, "Oppusset", 1900, 2025, valinit=state["last_renovated"], valstep=1, valfmt="%d")
sl_rprice = Slider(ax_rprice, "Oppussing\n(1000 kr)", 0, 3000, valinit=state["renovation_price"], valstep=50, valfmt="%d")
slider_m2 = Slider(ax_slider, "m²", 30, 250, valinit=100, valstep=5)
rb_city.on_clicked(on_city)
rb_type.on_clicked(set_state("house_type", HOUSE_TYPES))
sl_built.on_changed(lambda v: (state.update(year_built=int(v)), draw()))
sl_reno.on_changed(lambda v: (state.update(last_renovated=int(v)), draw()))
sl_rprice.on_changed(lambda v: (state.update(renovation_price=int(v)), draw()))
slider_m2.on_changed(lambda v: (state.update(m2=int(v)), draw()))
fig.canvas.mpl_connect("button_press_event", on_click)

draw()
plt.show()
