# Lager kunstige huspriser for Bergen og Stavanger og lagrer dem i House_Prices.csv
import math
import numpy as np
import pandas as pd

# For hver by: hvor de dyreste områdene ligger (x, y, vekt) og grunnpris per m2 (i 1000 kr).
# x og y er posisjon på kartet fra 0 til 100.
byer = {
    "Bergen": {
        "sentre": [(41, 57, 1.5),   # Sentrum
                   (45, 18, 0.5)],  # Fana
        "grunnpris": 75.0,
    },
    "Stavanger": {
        "sentre": [(47, 65, 1.4),   # Sentrum (Breiavatnet)
                   (34, 45, 0.6)],  # Madla
        "grunnpris": 70.0,
    },
}


def faktor_avstand(x1, y1, x2, y2):
    avstand = math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)
    return math.exp(-avstand * 0.1)       # nær senteret -> nær 1, langt unna -> nær 0


def faktor_posisjon(by, x, y):
    w = 1
    for sx, sy, vekt in byer[by]["sentre"]:
        w = w + vekt * faktor_avstand(sx, sy, x, y)
    return w


def faktor_standard(standard):
    return math.sqrt(standard)


def faktor_sma(m2):
    # Små hus er dyrere per m2 enn store hus
    t = (m2 - 50) / (200 - 50)
    t = min(max(t, 0.5), 1)               # hold t mellom 0.5 og 1
    return 1 - 0.5 * t


def faktor_boligtype(t):
    if t == 1:        # enebolig
        return 0.7
    if t == 2:        # rekkehus
        return 1.0
    return 1.2        # leilighet


def lag_huspris(by, x, y, boligtype, standard, m2):
    pris = (faktor_posisjon(by, x, y)
            * faktor_boligtype(boligtype)
            * faktor_standard(standard)
            * m2 * byer[by]["grunnpris"] * faktor_sma(m2))
    return pris


np.random.seed(1234)
antall = 400                               # antall salg per by
tabeller = []

for by in byer:
    xs = np.random.randint(0, 100, antall)
    ys = np.random.randint(0, 100, antall)
    boligtyper = np.random.randint(1, 4, antall)         # 1, 2 eller 3
    standarder = np.random.uniform(1.0, 4.0, antall)
    m2s = np.random.randint(30, 250, antall)

    priser = []
    for i in range(antall):
        pris = lag_huspris(by, xs[i], ys[i], boligtyper[i], standarder[i], m2s[i])
        pris = pris * np.random.uniform(0.95, 1.05)       # litt tilfeldig støy
        priser.append(int(pris))

    tabell = pd.DataFrame({
        "city": by,
        "x": xs,
        "y": ys,
        "m2": m2s,
        "house_type": boligtyper,
        "standard": np.round(standarder, 1),
        "sales_price": priser,
    })
    tabeller.append(tabell)

df = pd.concat(tabeller, ignore_index=True)
df.to_csv("House_Prices.csv", index=False)

print("Filen House_Prices.csv er laget:", len(df), "rader")
for by in byer:
    sx, sy, _ = byer[by]["sentre"][0]
    print(f"{by} sentrum (leilighet, 100 m2, standard 3) = {lag_huspris(by, sx, sy, 3, 3, 100):>10,.0f}")
