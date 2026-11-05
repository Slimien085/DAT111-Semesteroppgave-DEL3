"""Lager kunstige boligpriser for flere byer -> House_Prices_v2.csv (kolonne 'city')."""
import math
import numpy as np
import pandas as pd

from geo import GEO

# Prissentre som (breddegrad, lengdegrad, vekt). Vekt = hvor mye de påvirker prisen.
# Posisjonene gjøres om til kartets x/y (0-100) via geo.py, så de ligger riktig på kartet.
_CENTERS_LATLON = {
    "Bergen":    [(60.3924, 5.3243, 1.5),    # Bergen sentrum
                  (60.2638, 5.3823, 0.5)],   # Fana
    "Stavanger": [(58.9697, 5.7343, 1.4),    # Breiavatnet / sentrum
                  (58.9501, 5.7058, 0.6)],   # Madla / Tjensvoll
}
CITIES = {
    "Bergen":    {"centers": [(*GEO["Bergen"].latlon_to_xy(la, lo), w) for la, lo, w in _CENTERS_LATLON["Bergen"]],
                  "base": 75.0},
    "Stavanger": {"centers": [(*GEO["Stavanger"].latlon_to_xy(la, lo), w) for la, lo, w in _CENTERS_LATLON["Stavanger"]],
                  "base": 70.0},
}


def factor_distance(x1, y1, x2, y2) -> float:
    return math.exp(-math.hypot(x1 - x2, y1 - y2) * 0.1)


def factor_position(city: str, x, y) -> float:
    return 1 + sum(w * factor_distance(cx, cy, x, y) for cx, cy, w in CITIES[city]["centers"])


def factor_small(m2):
    t = np.clip((m2 - 50) / (200 - 50), 0.5, 1)
    return 1 - 0.5 * t


def factor_house_type(t: int) -> float:
    return {1: 0.7, 2: 1.0, 3: 1.2}.get(t, 1.0)


def make_house_price(city, x, y, house_type, standard, m2) -> float:
    return (factor_position(city, x, y) * factor_house_type(house_type)
            * math.sqrt(standard) * m2 * CITIES[city]["base"] * factor_small(m2))


def make_city(city: str, samples: int, rng) -> pd.DataFrame:
    xs = rng.integers(0, 100, samples)
    ys = rng.integers(0, 100, samples)
    types = np.round(rng.uniform(1, 4, samples)).astype(int)
    stds = rng.uniform(1.0, 4.0, samples)
    m2s = rng.integers(30, 250, samples)
    prices = [int(make_house_price(city, xs[i], ys[i], types[i], stds[i], m2s[i])
                  * rng.uniform(0.95, 1.05)) for i in range(samples)]
    return pd.DataFrame({"city": city, "x": xs, "y": ys, "m2": m2s, "house_type": types,
                         "standard": np.round(stds, 1), "sales_price": prices})


if __name__ == "__main__":
    rng = np.random.default_rng(1234)
    df = pd.concat([make_city(c, 600, rng) for c in CITIES], ignore_index=True)
    df.to_csv("House_Prices_v2.csv", index=False)
    print(f"House_Prices_v2.csv laget: {len(df)} rader")
