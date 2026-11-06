# House prices per m2 in Bergen and Stavanger. Click on the map to see the estimated price.
import os
import math
import matplotlib.pyplot as plt
from matplotlib.widgets import RadioButtons
import matplotlib.image as mpimg
from Semester26_Model import predict_price, models

folder = os.path.dirname(os.path.abspath(__file__))

# Info about each map: image file, latitude/longitude at the center of the map and the map size in km.
# (The numbers are calculated from the scale in the map images, so they are approximate.)
cities = {
    "Bergen": {"file": "Semester26_Bergen.jpg", "lat": 60.3709, "lon": 5.3754,
               "width_km": 27.4, "height_km": 37.2, "start": (41, 57)},
    "Stavanger": {"file": "Semester26_Stavanger.png", "lat": 58.9574, "lon": 5.7450,
                  "width_km": 15.2, "height_km": 9.5, "start": (47, 65)},
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
# Bar color by standard: red = poor, yellow = medium, green = good
standard_colors = {1: 'red', 2: 'gold', 3: 'yellowgreen', 4: 'green'}

city = "Bergen"
house_type = 1
standard_type = 1
m2 = 100
marked_point = cities[city]["start"]

# Load the map images once
images = {}
for name in cities:
    image = mpimg.imread(os.path.join(folder, cities[name]["file"]))
    if name == "Bergen":
        image = image[:1195]      # cuts off the text at the bottom of the Bergen map
    images[name] = image


def xy_to_latlon(x, y):
    """Convert the map's x and y (0-100) to latitude and longitude."""
    c = cities[city]
    km_east = (x - 50) / 100 * c["width_km"]       # km east of the center
    km_north = (y - 50) / 100 * c["height_km"]     # km north of the center
    lat = c["lat"] + km_north / 111.2              # 1 degree of latitude is about 111.2 km
    lon = c["lon"] + km_east / (111.2 * math.cos(math.radians(c["lat"])))
    return lat, lon


def draw_the_map():
    x, y = marked_point
    image = images[city]
    height, width = image.shape[0], image.shape[1]

    # ---- the map ----
    ax_map.cla()
    ax_map.imshow(image, extent=(0, 100, 0, 100), aspect='auto')
    ax_map.set_box_aspect(height / width)           # keeps the correct shape of the map
    ax_map.set_title(city)

    # The axes show latitude and longitude instead of 0-100
    ticks = [0, 25, 50, 75, 100]
    ax_map.set_xticks(ticks)
    ax_map.set_yticks(ticks)
    ax_map.set_xticklabels([f"{xy_to_latlon(t, 50)[1]:.2f}°Ø" for t in ticks], fontsize=8)
    ax_map.set_yticklabels([f"{xy_to_latlon(50, t)[0]:.2f}°N" for t in ticks], fontsize=8)
    ax_map.scatter(x, y, marker='+', c='blue', s=200)

    # ---- prices ----
    m2list = [50, 100, 150, 200]
    price_m2 = [predict_price(city, x, y, _m2, house_type, standard_type) / _m2 * 1000 for _m2 in m2list]
    price_100 = predict_price(city, x, y, 100, house_type, standard_type) / 100 * 1000   # NOK per m2 for 100 m2
    price_selected = predict_price(city, x, y, m2, house_type, standard_type) / m2 * 1000

    price = f"{round(price_selected, -2):,.0f} kr/m²".replace(",", " ")
    ax_map.text(min(x + 3, 60), max(y - 4, 5), price, color='blue', fontsize=12,
                bbox=dict(facecolor='white', alpha=0.8, edgecolor='none'))

    # ---- bar chart ----
    ax_history.cla()
    ax_history.bar([str(v) for v in m2list], price_m2, color=standard_colors[standard_type], width=0.6)
    ax_history.axhline(price_100, color='black', linestyle='--',
                       label=f"100 m²: {price_100:,.0f} kr".replace(",", " "))
    ax_history.grid(True, axis='y', alpha=0.4)
    ax_history.set_axisbelow(True)
    ax_history.set_ylim(0, max(price_m2) * 1.3)
    ax_history.set_xlabel("m²")
    ax_history.set_ylabel("kr per m²")
    ax_history.set_title("Pris per m²", fontsize=10)
    ax_history.legend(fontsize=8, loc="upper right")

    # ---- info about the model ----
    lat, lon = xy_to_latlon(x, y)
    m = models[city]
    ax_info.cla()
    ax_info.axis('off')
    ax_info.text(0, 1, f"Posisjon: {lat:.4f}°N, {lon:.4f}°Ø\n"
                       f"Modell: {m['name']}, grad {m['degree']}\n"
                       f"MAE: {m['mae']:,.0f}   R²: {m['r2']:.3f}".replace(",", " "),
                 va='top', fontsize=9, family='monospace')

    plt.draw()


def on_click_map(event):
    global marked_point
    if event.inaxes != ax_map:
        return
    marked_point = (event.xdata, event.ydata)
    draw_the_map()


def on_city(key):
    global city, marked_point
    city = key
    marked_point = cities[city]["start"]
    draw_the_map()


def on_house_type(key):
    global house_type
    house_type = house_types[key]
    draw_the_map()


def on_standard(key):
    global standard_type
    standard_type = standard_types[key]
    draw_the_map()


# Create the window
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

radio_button_city = RadioButtons(ax_radio_city, list(cities.keys()))
radio_button_category = RadioButtons(ax_radio_house_type, list(house_types.keys()))
radio_button_standard = RadioButtons(ax_radio_standard, list(standard_types.keys()))
radio_button_city.on_clicked(on_city)
radio_button_category.on_clicked(on_house_type)
radio_button_standard.on_clicked(on_standard)

draw_the_map()
plt.connect('button_press_event', on_click_map)
plt.show()
