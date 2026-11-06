# Boligpriser per m2 i Bergen og Stavanger. Klikk i kartet for å se estimert pris.
import os
import math
import matplotlib.pyplot as plt
from matplotlib.widgets import RadioButtons
import matplotlib.image as mpimg
from Semester26_Model import predict_price, modeller

mappe = os.path.dirname(os.path.abspath(__file__))

# Informasjon om hvert kart: bildefil, breddegrad/lengdegrad i midten av kartet og kartets størrelse i km.
# (Tallene er regnet ut fra målestokken i kartbildene, så de er omtrentlige.)
byer = {
    "Bergen": {"fil": "Semester26_Bergen.jpg", "lat": 60.3709, "lon": 5.3754,
               "bredde_km": 27.4, "hoyde_km": 37.2, "start": (41, 57)},
    "Stavanger": {"fil": "Semester26_Stavanger.png", "lat": 58.9574, "lon": 5.7450,
                  "bredde_km": 15.2, "hoyde_km": 9.5, "start": (47, 65)},
}
house_types = {
    'Enebolig': 1,
    'Rekke': 2,
    'Leilighet': 3
}
standard_types = {
    'Dårlig': 1,
    'God': 2,
    'Meget God': 3,
    'Luksus': 4
}
# Farge på stolpene etter standard: rød = dårlig, gul = middels, grønn = god
standard_farger = {1: 'red', 2: 'gold', 3: 'yellowgreen', 4: 'green'}

by = "Bergen"
house_type = 1
standard_type = 1
m2 = 100
marked_point = byer[by]["start"]

# Les inn kartbildene én gang
bilder = {}
for navn in byer:
    bilde = mpimg.imread(os.path.join(mappe, byer[navn]["fil"]))
    if navn == "Bergen":
        bilde = bilde[:1195]      # klipper bort teksten nederst på Bergen-kartet
    bilder[navn] = bilde


def xy_til_latlon(x, y):
    """Gjør kartets x og y (0-100) om til breddegrad og lengdegrad."""
    b = byer[by]
    km_ost = (x - 50) / 100 * b["bredde_km"]       # km øst for midten
    km_nord = (y - 50) / 100 * b["hoyde_km"]       # km nord for midten
    lat = b["lat"] + km_nord / 111.2               # 1 breddegrad er ca. 111,2 km
    lon = b["lon"] + km_ost / (111.2 * math.cos(math.radians(b["lat"])))
    return lat, lon


def draw_the_map():
    x, y = marked_point
    bilde = bilder[by]
    hoyde, bredde = bilde.shape[0], bilde.shape[1]

    # ---- kartet ----
    ax_map.cla()
    ax_map.imshow(bilde, extent=(0, 100, 0, 100), aspect='auto')
    ax_map.set_box_aspect(hoyde / bredde)           # beholder riktig form på kartet
    ax_map.set_title(by)

    # Aksene viser breddegrad og lengdegrad i stedet for 0-100
    ticks = [0, 25, 50, 75, 100]
    ax_map.set_xticks(ticks)
    ax_map.set_yticks(ticks)
    ax_map.set_xticklabels([f"{xy_til_latlon(t, 50)[1]:.2f}°Ø" for t in ticks], fontsize=8)
    ax_map.set_yticklabels([f"{xy_til_latlon(50, t)[0]:.2f}°N" for t in ticks], fontsize=8)
    ax_map.scatter(x, y, marker='+', c='blue', s=200)

    # ---- priser ----
    m2list = [50, 100, 150, 200]
    price_m2 = [predict_price(by, x, y, _m2, house_type, standard_type) / _m2 * 1000 for _m2 in m2list]
    pris_100 = predict_price(by, x, y, 100, house_type, standard_type) / 100 * 1000   # kr per m2 for 100 m2
    pris_valgt = predict_price(by, x, y, m2, house_type, standard_type) / m2 * 1000

    price = f"{round(pris_valgt, -2):,.0f} kr/m²".replace(",", " ")
    ax_map.text(min(x + 3, 60), max(y - 4, 5), price, color='blue', fontsize=12,
                bbox=dict(facecolor='white', alpha=0.8, edgecolor='none'))

    # ---- stolpediagram ----
    ax_history.cla()
    ax_history.bar([str(v) for v in m2list], price_m2, color=standard_farger[standard_type], width=0.6)
    ax_history.axhline(pris_100, color='black', linestyle='--',
                       label=f"100 m²: {pris_100:,.0f} kr".replace(",", " "))
    ax_history.grid(True, axis='y', alpha=0.4)
    ax_history.set_axisbelow(True)
    ax_history.set_ylim(0, max(price_m2) * 1.3)
    ax_history.set_xlabel("m²")
    ax_history.set_ylabel("kr per m²")
    ax_history.set_title("Pris per m²", fontsize=10)
    ax_history.legend(fontsize=8, loc="upper right")

    # ---- info om modellen ----
    lat, lon = xy_til_latlon(x, y)
    b = modeller[by]
    ax_info.cla()
    ax_info.axis('off')
    ax_info.text(0, 1, f"Posisjon: {lat:.4f}°N, {lon:.4f}°Ø\n"
                       f"Modell: {b['navn']}, grad {b['grad']}\n"
                       f"MAE: {b['mae']:,.0f}   R²: {b['r2']:.3f}".replace(",", " "),
                 va='top', fontsize=9, family='monospace')

    plt.draw()


def on_click_map(event):
    global marked_point
    if event.inaxes != ax_map:
        return
    marked_point = (event.xdata, event.ydata)
    draw_the_map()


def on_city(key):
    global by, marked_point
    by = key
    marked_point = byer[by]["start"]
    draw_the_map()


def on_house_type(key):
    global house_type
    house_type = house_types[key]
    draw_the_map()


def on_standard(key):
    global standard_type
    standard_type = standard_types[key]
    draw_the_map()


# Lag vinduet
fig = plt.figure(figsize=(10.0, 6.5), facecolor='lightgray')  # type: ignore[arg-type]
fig.suptitle("Huspriser (per m²)", fontsize=20, y=0.97)

ax_radio_city = fig.add_axes((0.03, 0.78, 0.25, 0.12))
ax_radio_house_type = fig.add_axes((0.03, 0.62, 0.25, 0.13))
ax_radio_standard = fig.add_axes((0.03, 0.44, 0.25, 0.15))
ax_history = fig.add_axes((0.11, 0.17, 0.18, 0.21))
ax_info = fig.add_axes((0.03, 0.01, 0.30, 0.07))
ax_map = fig.add_axes((0.38, 0.08, 0.58, 0.82))
for ax in (ax_radio_city, ax_radio_house_type, ax_radio_standard):
    ax.set_facecolor('lightgray')

radio_button_city = RadioButtons(ax_radio_city, list(byer.keys()))
radio_button_category = RadioButtons(ax_radio_house_type, list(house_types.keys()))
radio_button_standard = RadioButtons(ax_radio_standard, list(standard_types.keys()))
radio_button_city.on_clicked(on_city)
radio_button_category.on_clicked(on_house_type)
radio_button_standard.on_clicked(on_standard)

draw_the_map()
plt.connect('button_press_event', on_click_map)
plt.show()
