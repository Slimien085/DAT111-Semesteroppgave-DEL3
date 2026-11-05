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


CURRENT_YEAR = 2025


def standard_score(year_built, last_renovated, renovation_price, m2) -> float:
    """Standard 1.0 (dårlig) - 4.0 (luksus) ut fra byggeår, siste oppussing og oppussingspris (1000 kr)."""
    build = np.clip((year_built - 1900) / (CURRENT_YEAR - 1900), 0, 1)
    eff_year = max(year_built, last_renovated)                       # nybygg regnes som nylig "oppusset"
    recency = np.clip(1 - (CURRENT_YEAR - eff_year) / 40, 0, 1)      # 0 etter 40 år
    invest = np.clip(1000 * renovation_price / m2 / 10000, 0, 1)     # 10 000 kr/m² = full effekt
    score = 0.45 * build + 0.55 * recency * (0.4 + 0.6 * invest)
    return float(1 + 3 * score)


def make_house_price(city, x, y, house_type, year_built, last_renovated, renovation_price, m2) -> float:
    standard = standard_score(year_built, last_renovated, renovation_price, m2)
    return (factor_position(city, x, y) * factor_house_type(house_type)
            * math.sqrt(standard) * m2 * CITIES[city]["base"] * factor_small(m2))


def make_city(city: str, samples: int, rng) -> pd.DataFrame:
    xs = rng.integers(0, 100, samples)
    ys = rng.integers(0, 100, samples)
    types = np.round(rng.uniform(1, 4, samples)).astype(int)
    m2s = rng.integers(30, 250, samples)
    built = rng.integers(1900, CURRENT_YEAR + 1, samples)
    renovated, reno_price = built.copy(), np.zeros(samples, dtype=int) 
    for i in range(samples):
        if rng.random() < 0.6 and built[i] < CURRENT_YEAR:
            renovated[i] = rng.integers(built[i] + 1, CURRENT_YEAR + 1)
            reno_price[i] = int(m2s[i] * rng.uniform(1000, 14000) / 1000) 
    prices = [int(make_house_price(city, xs[i], ys[i], types[i], built[i], renovated[i], reno_price[i], m2s[i])
                  * rng.uniform(0.95, 1.05)) for i in range(samples)]
    return pd.DataFrame({"city": city, "x": xs, "y": ys, "m2": m2s, "house_type": types,
                         "year_built": built, "last_renovated": renovated,
                         "renovation_price": reno_price, "sales_price": prices})


if __name__ == "__main__":
    rng = np.random.default_rng(1234)
    df = pd.concat([make_city(c, 600, rng) for c in CITIES], ignore_index=True)
    df.to_csv("House_Prices_v2.csv", index=False)
    print(f"House_Prices_v2.csv laget: {len(df)} rader")
