"""Modeller for boligpriser: sammenligner polynomgrader og regressjonstyper per by."""
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression, Ridge, RidgeCV
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import PolynomialFeatures, StandardScaler

COLUMNS = ["x", "y", "m2", "house_type", "year_built", "last_renovated", "renovation_price"]


def add_features(X: pd.DataFrame) -> pd.DataFrame:
    X = X.copy()
    X["x2"] = X["x"] ** 1.5 
    X["y2"] = X["y"] ** 1.5
    return X


def make_model(kind: str, degree: int):
    regs = {
        "Linear": LinearRegression(),
        "Ridge": Ridge(alpha=1.0),
        "RidgeCV": RidgeCV(alphas=np.logspace(-3, 3, 13)),
    }
    return make_pipeline(PolynomialFeatures(degree), StandardScaler(), regs[kind])


class CityModel:
    def __init__(self, df_city: pd.DataFrame, kinds=("Linear", "Ridge", "RidgeCV"), degrees=(1, 2, 3, 4)):
        X = add_features(df_city[COLUMNS])
        y = df_city["sales_price"].values
        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
            X, y, test_size=0.25, random_state=42)
        self.results = []
        best = None
        for kind in kinds:
            for d in degrees:
                m = make_model(kind, d).fit(self.X_train, self.y_train)
                pred = m.predict(self.X_test)
                mae, r2 = mean_absolute_error(self.y_test, pred), r2_score(self.y_test, pred)
                self.results.append((kind, d, mae, r2))
                if best is None or mae < best[0]:
                    best = (mae, kind, d)
        self.best_kind, self.best_degree = best[1], best[2]
        self.best_mae = best[0]
        self.best_r2 = next(r2 for k, d, _, r2 in self.results if (k, d) == (best[1], best[2]))
        # tren vinnermodellen på alle data
        self.model = make_model(self.best_kind, self.best_degree).fit(X, y)

    def print_comparison(self, city: str):
        print(f"\n=== {city}: modellsammenligning (testsett) ===")
        print(f"{'Modell':<9}{'Grad':>5}{'MAE':>12}{'R²':>9}")
        for kind, d, mae, r2 in self.results:
            star = "  <-- best" if (kind, d) == (self.best_kind, self.best_degree) else ""
            print(f"{kind:<9}{d:>5}{mae:>12,.0f}{r2:>9.3f}{star}")

    def predict(self, x, y, m2, house_type, year_built, last_renovated, renovation_price) -> float:
        row = pd.DataFrame([[x, y, m2, house_type, year_built, last_renovated, renovation_price]], columns=COLUMNS)
        return float(self.model.predict(add_features(row))[0])


def load_models(path="House_Prices_v2.csv") -> dict[str, CityModel]:
    df = pd.read_csv(path)
    models = {}
    for city, d in df.groupby("city"):
        models[city] = CityModel(d)
        models[city].print_comparison(city)
    return models


if __name__ == "__main__":
    load_models()
