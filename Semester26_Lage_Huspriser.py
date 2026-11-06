import math
import numpy as np
import pandas as pd

cities = {
    "Bergen": {
        "centers": [(41, 57, 1.5),   # Sentrum
                    (45, 18, 0.5)],  # Fana
        "base_price": 75.0,
    },
    "Stavanger": {
        "centers": [(47, 65, 1.4),   # Sentrum
                    (34, 45, 0.6)],  # Madla
        "base_price": 70.0,
    },
}


def factor_distance(x1, y1, x2, y2):
    distance = math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)
    return math.exp(-distance * 0.1)


def factor_position(city, x, y):
    w = 1
    for cx, cy, weight in cities[city]["centers"]:
        w = w + weight * factor_distance(cx, cy, x, y)
    return w


def factor_standard(standard):
    return math.sqrt(standard)


def factor_small(m2):
    t = (m2 - 50) / (200 - 50)     # normalize 50→300 to 0→1
    t = min(max(t, 0.5), 1)           # keep inside range
    return 1 - 0.5 * t             # linear inverse


def factor_house_type(t):
    if t == 1:
        return 0.7
    if t == 2:
        return 1.0
    return 1.2


def make_house_price(city, x, y, house_type, standard, m2):
    price = (factor_position(city, x, y)
             * factor_house_type(house_type)
             * factor_standard(standard)
             * m2 * cities[city]["base_price"] * factor_small(m2))
    return price


np.random.seed(1234)
count = 400
tables = []

for city in cities:
    xs = np.random.randint(0, 100, count)
    ys = np.random.randint(0, 100, count)
    house_types = np.random.randint(1, 4, count)
    standards = np.random.uniform(1.0, 4.0, count)
    m2s = np.random.randint(30, 250, count)

    prices = []
    for i in range(count):
        price = make_house_price(city, xs[i], ys[i], house_types[i], standards[i], m2s[i])
        price = price * np.random.uniform(0.95, 1.05)
        prices.append(int(price))

    table = pd.DataFrame({
        "city": city,
        "x": xs,
        "y": ys,
        "m2": m2s,
        "house_type": house_types,
        "standard": np.round(standards, 1),
        "sales_price": prices,
    })
    tables.append(table)

df = pd.concat(tables, ignore_index=True)
df.to_csv("House_Prices.csv", index=False)

print("Filen House_Prices.csv er laget:", len(df), "rader")
for city in cities:
    cx, cy, _ = cities[city]["centers"][0]
    print(f"{city} sentrum (leilighet, 100 m2, standard 3) = {make_house_price(city, cx, cy, 3, 3, 100):>10,.0f}")
