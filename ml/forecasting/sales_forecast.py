import os
import joblib
import pandas as pd
from xgboost import XGBRegressor


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_PATH = os.path.join(
    BASE_DIR,
    "data",
    "raw",
    "E-Commerce Customer Insights and Churn Dataset3938d09.xls"
)

OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")
MODEL_DIR = os.path.join(BASE_DIR, "forecasting", "models")

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(MODEL_DIR, exist_ok=True)


FEATURES = [
    "lag_1",
    "lag_2",
    "lag_3",
    "lag_6",
    "rolling_3",
    "rolling_6",
    "month",
    "year"
]


def prepare_monthly_sales(df):
    df["last_purchase_date"] = pd.to_datetime(
        df["last_purchase_date"],
        errors="coerce"
    )

    df["revenue"] = df["unit_price"] * df["quantity"]

    monthly_sales = (
        df.set_index("last_purchase_date")
        .resample("MS")["revenue"]
        .sum()
        .reset_index()
    )

    monthly_sales.columns = ["date", "sales"]

    return monthly_sales


def create_features(monthly_sales):
    data = monthly_sales.copy()

    data["lag_1"] = data["sales"].shift(1)
    data["lag_2"] = data["sales"].shift(2)
    data["lag_3"] = data["sales"].shift(3)
    data["lag_6"] = data["sales"].shift(6)

    data["rolling_3"] = (
        data["sales"].shift(1).rolling(3).mean()
    )

    data["rolling_6"] = (
        data["sales"].shift(1).rolling(6).mean()
    )

    data["month"] = data["date"].dt.month
    data["year"] = data["date"].dt.year

    return data.dropna().reset_index(drop=True)


def train_model(data):
    X = data[FEATURES]
    y = data["sales"]

    model = XGBRegressor(
        n_estimators=300,
        learning_rate=0.05,
        max_depth=4,
        subsample=0.8,
        colsample_bytree=0.8,
        objective="reg:squarederror",
        random_state=42
    )

    model.fit(X, y)

    return model


def generate_forecast(model, monthly_sales):
    history = monthly_sales[["date", "sales"]].copy()

    future_dates = pd.date_range(
        start="2026-01-01",
        periods=12,
        freq="MS"
    )

    predictions = []

    for current_date in future_dates:
        sales_history = history["sales"]

        row = pd.DataFrame([{
            "lag_1": sales_history.iloc[-1],
            "lag_2": sales_history.iloc[-2],
            "lag_3": sales_history.iloc[-3],
            "lag_6": sales_history.iloc[-6],
            "rolling_3": sales_history.iloc[-3:].mean(),
            "rolling_6": sales_history.iloc[-6:].mean(),
            "month": current_date.month,
            "year": current_date.year
        }])

        prediction = max(
            0,
            model.predict(row[FEATURES])[0]
        )

        predictions.append(prediction)

        history = pd.concat(
            [
                history,
                pd.DataFrame({
                    "date": [current_date],
                    "sales": [prediction]
                })
            ],
            ignore_index=True
        )

    forecast = pd.DataFrame({
        "date": future_dates,
        "predicted_sales": predictions
    })

    forecast["forecast_year"] = forecast["date"].dt.year

    return forecast


def main():
    df = pd.read_excel(DATA_PATH)

    monthly_sales = prepare_monthly_sales(df)
    feature_data = create_features(monthly_sales)

    model = train_model(feature_data)

    forecast = generate_forecast(
        model,
        monthly_sales
    )

    forecast.to_csv(
        os.path.join(
            OUTPUT_DIR,
            "sales_forecast.csv"
        ),
        index=False
    )

    joblib.dump(
        model,
        os.path.join(
            MODEL_DIR,
            "sales_model.pkl"
        )
    )

    print("Sales forecasting completed successfully.")
    print(forecast)


if __name__ == "__main__":
    main()