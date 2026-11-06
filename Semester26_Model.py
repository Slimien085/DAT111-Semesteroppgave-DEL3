import os
import numpy as np
import pandas as pd
from sklearn.preprocessing import PolynomialFeatures, StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression, Ridge, RidgeCV
from sklearn.pipeline import make_pipeline
from sklearn.metrics import r2_score, mean_absolute_error

columns = ["x", "y", "m2", "house_type", "standard"]
degrees = [1, 2, 3, 4]
model_types = ["LinearRegression", "Ridge", "RidgeCV"]


def make_model(type_name, degree):
    if type_name == "LinearRegression":
        regression = LinearRegression()
    elif type_name == "Ridge":
        regression = Ridge(alpha=1.0)
    else:
        regression = RidgeCV(alphas=[0.001, 0.01, 0.1, 1, 10, 100, 1000])
    return make_pipeline(PolynomialFeatures(degree), StandardScaler(), regression)


def make_data(df_city):
    X = df_city[columns].copy()
    X["x2"] = X["x"] ** 1.5
    X["y2"] = X["y"] ** 1.5
    Y = df_city["sales_price"].values
    return X, Y


def train_city(city, df_city):
    X, Y = make_data(df_city)
    x_train, x_test, y_train, y_test = train_test_split(X, Y, test_size=0.25, random_state=42)

    print(f"\n=== {city} ===")
    print(f"{'Modell':<18}{'Grad':>7}{'MAE':>9}{'R2':>9}")

    best = None
    for type_name in model_types:
        for degree in degrees:
            model = make_model(type_name, degree)
            model.fit(x_train, np.log(y_train))        # price is a product of factors, so learn log(price)
            y_pred = np.exp(model.predict(x_test))
            mae = mean_absolute_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)
            print(f"{type_name:<18}{degree:>7}{mae:>9.0f}{r2:>9.3f}")
            if best is None or mae < best["mae"]:
                best = {"model": model, "name": type_name, "degree": degree, "mae": mae, "r2": r2}

    print(f"Beste for {city}: {best['name']}, grad {best['degree']}  (MAE {best['mae']:.0f}, R2 {best['r2']:.3f})")
    return best


def predict_price(city, x, y, m2, house_type, standard):
    house = pd.DataFrame([[x, y, m2, house_type, standard]], columns=columns)
    house["x2"] = house["x"] ** 1.5
    house["y2"] = house["y"] ** 1.5
    return float(np.exp(models[city]["model"].predict(house)[0]))


file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "House_Prices.csv")
df = pd.read_csv(file_path)
models = {}
for city_name in df["city"].unique():
    models[city_name] = train_city(city_name, df[df["city"] == city_name])
