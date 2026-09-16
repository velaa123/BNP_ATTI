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


def prepare_demand_data(df):
    df["last_purchase_date"] = pd.to_datetime(
        df["last_purchase_date"],
        errors="coerce"
    )

    monthly_demand = (
        df.set_index("last_purchase_date")
        .resample("MS")["quantity"]
        .sum()
        .reset_index()
    )

    monthly_demand.columns = [
        "date",
        "demand"
    ]

    return monthly_demand


def create_features(data):
    data = data.copy()

    data["lag_1"] = data["demand"].shift(1)
    data["lag_2"] = data["demand"].shift(2)
    data["lag_3"] = data["demand"].shift(3)
    data["lag_6"] = data["demand"].shift(6)

    data["rolling_3"] = (
        data["demand"].shift(1).rolling(3).mean()
    )

    data["rolling_6"] = (
        data["demand"].shift(1).rolling(6).mean()
    )

    data["month"] = data["date"].dt.month
    data["year"] = data["date"].dt.year

    return data.dropna().reset_index(drop=True)


def train_model(data):
    model = XGBRegressor(
        n_estimators=300,
        learning_rate=0.05,
        max_depth=4,
        subsample=0.8,
        colsample_bytree=0.8,
        objective="reg:squarederror",
        random_state=42
    )

    model.fit(
        data[FEATURES],
        data["demand"]
    )

    return model


def generate_forecast(model, monthly_demand):
    history = monthly_demand[
        ["date", "demand"]
    ].copy()

    future_dates = pd.date_range(
        "2026-01-01",
        periods=12,
        freq="MS"
    )

    predictions = []

    for current_date in future_dates:
        demand_history = history["demand"]

        row = pd.DataFrame([{
            "lag_1": demand_history.iloc[-1],
            "lag_2": demand_history.iloc[-2],
            "lag_3": demand_history.iloc[-3],
            "lag_6": demand_history.iloc[-6],
            "rolling_3": demand_history.iloc[-3:].mean(),
            "rolling_6": demand_history.iloc[-6:].mean(),
            "month": current_date.month,
            "year": current_date.year
        }])

        prediction = max(
            0,
            model.predict(row[FEATURES])[0]
        )

        predictions.append(prediction)

        history = pd.concat([
            history,
            pd.DataFrame({
                "date": [current_date],
                "demand": [prediction]
            })
        ], ignore_index=True)

    return pd.DataFrame({
        "date": future_dates,
        "predicted_demand": predictions
    })


def main():
    df = pd.read_excel(DATA_PATH)

    monthly_demand = prepare_demand_data(df)
    feature_data = create_features(monthly_demand)

    model = train_model(feature_data)

    forecast = generate_forecast(
        model,
        monthly_demand
    )

    forecast.to_csv(
        os.path.join(
            OUTPUT_DIR,
            "demand_forecast.csv"
        ),
        index=False
    )

    joblib.dump(
        model,
        os.path.join(
            MODEL_DIR,
            "demand_model.pkl"
        )
    )

    print("Demand forecasting completed successfully.")
    print(forecast)


if __name__ == "__main__":
    main()