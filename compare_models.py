"""Sammenligner modeller (Linear / Ridge / RidgeCV) og polynomgrader med MAE og R².

Kjør:  python compare_models.py
Lager modellsammenligning.png og skriver tabeller til konsollen.
"""
import os
import matplotlib.pyplot as plt
import pandas as pd

from Semester26_Model import CityModel

HERE = os.path.dirname(os.path.abspath(__file__))
df = pd.read_csv(os.path.join(HERE, "House_Prices_v2.csv"))
COLORS = {"Linear": "#1f77b4", "Ridge": "#ff7f0e", "RidgeCV": "#2ca02c"}

cities = list(df["city"].unique())
fig, axes = plt.subplots(2, len(cities), figsize=(11, 7), sharex=True)

for col, city in enumerate(cities):
    cm = CityModel(df[df["city"] == city])
    cm.print_comparison(city)
    res = pd.DataFrame(cm.results, columns=["modell", "grad", "mae", "r2"])
    for kind, g in res.groupby("modell"):
        axes[0, col].plot(g["grad"], g["mae"], "o-", color=COLORS[kind], label=kind)
        axes[1, col].plot(g["grad"], g["r2"], "o-", color=COLORS[kind], label=kind)
    axes[0, col].set_title(f"{city}: beste = {cm.best_kind}, grad {cm.best_degree}")
    axes[0, col].set_ylabel("MAE (tusen kr)")
    axes[1, col].set_ylabel("R²")
    axes[1, col].set_xlabel("Polynomgrad")
    axes[1, col].set_xticks(sorted(res["grad"].unique()))
    for r in (0, 1):
        axes[r, col].grid(True, alpha=0.4)
    axes[0, col].legend()

fig.suptitle("Modellsammenligning på testsett (lavere MAE og høyere R² er bedre)")
fig.tight_layout()
fig.savefig(os.path.join(HERE, "modellsammenligning.png"), dpi=130)
print("\nLagret modellsammenligning.png")
plt.show()
