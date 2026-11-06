# Maskinlæring: lærer å estimere huspriser fra salgsdata (en modell per by)
import os
import numpy as np
import pandas as pd
from sklearn.preprocessing import PolynomialFeatures, StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression, Ridge, RidgeCV
from sklearn.pipeline import make_pipeline
from sklearn.metrics import r2_score, mean_absolute_error

kolonner = ["x", "y", "m2", "house_type", "standard"]
grader = [1, 2, 3, 4]                         # polynomgrader vi prøver
modelltyper = ["LinearRegression", "Ridge", "RidgeCV"]


def lag_modell(type_navn, grad):
    """Lager en modell: polynom -> skalering -> regresjon."""
    if type_navn == "LinearRegression":
        regresjon = LinearRegression()
    elif type_navn == "Ridge":
        regresjon = Ridge(alpha=1.0)
    else:
        regresjon = RidgeCV(alphas=[0.001, 0.01, 0.1, 1, 10, 100, 1000])
    # StandardScaler gjør alle tallene like store, ellers blir Ridge urettferdig
    return make_pipeline(PolynomialFeatures(grad), StandardScaler(), regresjon)


def lag_data(df_by):
    """Henter ut X og Y fra tabellen. Posisjon vektlegges mer med x^1.5 og y^1.5."""
    X = df_by[kolonner].copy()
    X["x2"] = X["x"] ** 1.5
    X["y2"] = X["y"] ** 1.5
    Y = df_by["sales_price"].values
    return X, Y


def tren_by(by, df_by):
    """Prøver alle kombinasjoner av modelltype og grad, og velger den med lavest MAE.

    Prisen er et produkt av mange faktorer (posisjon * standard * boligtype ...).
    Tar vi logaritmen av prisen blir det en sum, og det er mye lettere for modellen å lære.
    """
    X, Y = lag_data(df_by)
    x_train, x_test, y_train, y_test = train_test_split(X, Y, test_size=0.25, random_state=42)

    print(f"\n=== {by} ===")
    print(f"{'Modell':<18}{'Grad':>5}{'MAE':>9}{'R2':>9}")

    beste = None
    for type_navn in modelltyper:
        for grad in grader:
            modell = lag_modell(type_navn, grad)
            modell.fit(x_train, np.log(y_train))       # lærer log av prisen (se kommentar over)
            y_pred = np.exp(modell.predict(x_test))    # tilbake til vanlig pris
            mae = mean_absolute_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)
            print(f"{type_navn:<18}{grad:>5}{mae:>9.0f}{r2:>9.3f}")
            if beste is None or mae < beste["mae"]:
                beste = {"modell": modell, "navn": type_navn, "grad": grad, "mae": mae, "r2": r2}

    print(f"Beste for {by}: {beste['navn']}, grad {beste['grad']}  (MAE {beste['mae']:.0f}, R2 {beste['r2']:.3f})")
    return beste


def predict_price(by, x, y, m2, house_type, standard):
    """Estimert pris (i 1000 kr) for ett hus i en gitt by."""
    hus = pd.DataFrame([[x, y, m2, house_type, standard]], columns=kolonner)
    hus["x2"] = hus["x"] ** 1.5
    hus["y2"] = hus["y"] ** 1.5
    return float(np.exp(modeller[by]["modell"].predict(hus)[0]))


# Dette kjøres når filen importeres: les data og tren en modell per by
filsti = os.path.join(os.path.dirname(os.path.abspath(__file__)), "House_Prices.csv")
df = pd.read_csv(filsti)
modeller = {}
for by_navn in df["city"].unique():
    modeller[by_navn] = tren_by(by_navn, df[df["city"] == by_navn])
