"""Georeferering av kartbildene (uten eksterne pakker).

Hvert kart er knyttet til EPSG:25833 (ETRS89 / UTM sone 33N), som er det Kartverket bruker.
Programmets x/y (0-100) er prosent av kartbildets bredde og høyde (y=0 nederst).

Kalibrering per by:
  - Bergen:    senterposisjon og målestokk (4 km-linje) fra bunnteksten i Kartverkets utskrift.
  - Stavanger: målestokk (2 km-linje) fra bildet. Ankerpunktet er Breiavatnet (omtrentlig).
"""
import math

# GRS80-ellipsoiden (ETRS89)
A = 6378137.0
F = 1 / 298.257222101
K0 = 0.9996
LON0 = math.radians(15.0)           # sentralmeridian, UTM sone 33
E0 = 500000.0

_n = F / (2 - F)
_A = A / (1 + _n) * (1 + _n**2 / 4 + _n**4 / 64)
_alpha = [_n / 2 - 2 * _n**2 / 3 + 5 * _n**3 / 16,
          13 * _n**2 / 48 - 3 * _n**3 / 5,
          61 * _n**3 / 240]
_beta = [_n / 2 - 2 * _n**2 / 3 + 37 * _n**3 / 96,
         _n**2 / 48 + _n**3 / 15,
         17 * _n**3 / 480]
_delta = [2 * _n - 2 * _n**2 / 3 - 2 * _n**3,
          7 * _n**2 / 3 - 8 * _n**3 / 5,
          56 * _n**3 / 15]


def latlon_to_utm33(lat: float, lon: float) -> tuple[float, float]:
    """WGS84/ETRS89 grader -> (easting, northing) i EPSG:25833."""
    phi, lam = math.radians(lat), math.radians(lon) - LON0
    e = math.sqrt(F * (2 - F))
    t = math.sinh(math.atanh(math.sin(phi)) - e * math.atanh(e * math.sin(phi)))
    xi = math.atan2(t, math.cos(lam))
    eta = math.atanh(math.sin(lam) / math.sqrt(1 + t * t))
    x = eta + sum(a * math.cos(2 * (j + 1) * xi) * math.sinh(2 * (j + 1) * eta) for j, a in enumerate(_alpha))
    y = xi + sum(a * math.sin(2 * (j + 1) * xi) * math.cosh(2 * (j + 1) * eta) for j, a in enumerate(_alpha))
    return E0 + K0 * _A * x, K0 * _A * y


def utm33_to_latlon(easting: float, northing: float) -> tuple[float, float]:
    """(easting, northing) i EPSG:25833 -> (breddegrad, lengdegrad)."""
    xi = northing / (K0 * _A)
    eta = (easting - E0) / (K0 * _A)
    xi_p = xi - sum(b * math.sin(2 * (j + 1) * xi) * math.cosh(2 * (j + 1) * eta) for j, b in enumerate(_beta))
    eta_p = eta - sum(b * math.cos(2 * (j + 1) * xi) * math.sinh(2 * (j + 1) * eta) for j, b in enumerate(_beta))
    chi = math.asin(math.sin(xi_p) / math.cosh(eta_p))
    phi = chi + sum(d * math.sin(2 * (j + 1) * chi) for j, d in enumerate(_delta))
    lam = LON0 + math.atan2(math.sinh(eta_p), math.cos(xi_p))
    return math.degrees(phi), math.degrees(lam)


class MapGeo:
    """Knytter pikselposisjon i kartbildet til UTM33 og lat/lon.

    px_per_km  : antall piksler per km (målt fra målestokklinjen)
    anchor_px  : (px, py) i bildet (py regnet ovenfra) for et kjent punkt
    anchor_utm : (easting, northing) for samme punkt
    map_h      : høyden på selve kartet i piksler (uten bunntekst)
    """

    def __init__(self, width: int, map_h: int, px_per_km: float, anchor_px, anchor_utm):
        self.w, self.h, self.ppk = width, map_h, px_per_km
        self.ax, self.ay = anchor_px
        self.ae, self.an = anchor_utm

    # --- piksler <-> UTM -------------------------------------------------
    def px_to_utm(self, px: float, py: float) -> tuple[float, float]:
        return (self.ae + (px - self.ax) / self.ppk * 1000,
                self.an - (py - self.ay) / self.ppk * 1000)

    # --- programmets 0-100-system <-> lat/lon ----------------------------
    def xy_to_latlon(self, x: float, y: float) -> tuple[float, float]:
        px, py = x / 100 * self.w, (1 - y / 100) * self.h
        return utm33_to_latlon(*self.px_to_utm(px, py))

    def latlon_to_xy(self, lat: float, lon: float) -> tuple[float, float]:
        e, n = latlon_to_utm33(lat, lon)
        px = self.ax + (e - self.ae) / 1000 * self.ppk
        py = self.ay - (n - self.an) / 1000 * self.ppk
        return px / self.w * 100, (1 - py / self.h) * 100

    # --- størrelse i km ---------------------------------------------------
    @property
    def width_km(self) -> float:
        return self.w / self.ppk

    @property
    def height_km(self) -> float:
        return self.h / self.ppk

    def km_to_xy(self, km: float) -> tuple[float, float]:
        """Lengde i km som prosent av bredde/høyde."""
        return km / self.width_km * 100, km / self.height_km * 100


# ---- Kalibrering ---------------------------------------------------------
# Bergen (879 x 1256 px, kart uten bunntekst: ca. 1195 px høyt).
# Utskriftens senterposisjon: -29533.35, 6731520.12 (EPSG:25833). 4 km-linja er 128.5 px lang.
_BERGEN_H = 1195
BERGEN = MapGeo(879, _BERGEN_H, px_per_km=128.5 / 4,
                anchor_px=(879 / 2, _BERGEN_H / 2),
                anchor_utm=(-29533.35, 6731520.12))

# Stavanger (2880 x 1800 px). 2 km-linja er ca. 379 px lang => ca. 189.5 px/km.
# Ankerpunkt: Breiavatnet (ca. 58.9697 N, 5.7343 E), som ligger ca. (1360, 625) i bildet.
STAVANGER = MapGeo(2880, 1800, px_per_km=379 / 2,
                   anchor_px=(1360, 625),
                   anchor_utm=latlon_to_utm33(58.9697, 5.7343))

GEO = {"Bergen": BERGEN, "Stavanger": STAVANGER}


if __name__ == "__main__":
    # Selvtest: rundtur lat/lon -> UTM -> lat/lon, og Bergen sentrum mot kartet
    lat, lon = 60.3913, 5.3221
    e, n = latlon_to_utm33(lat, lon)
    print("Rundtur:", utm33_to_latlon(e, n), "(forventet", (lat, lon), ")")
    x, y = BERGEN.latlon_to_xy(60.3924, 5.3243)
    print(f"Bergen sentrum (Torgallmenningen) -> x={x:.1f}, y={y:.1f}")
    x, y = STAVANGER.latlon_to_xy(58.9697, 5.7343)
    print(f"Stavanger Breiavatnet -> x={x:.1f}, y={y:.1f}")
    for name, g in GEO.items():
        print(f"{name}: {g.width_km:.1f} km x {g.height_km:.1f} km")
