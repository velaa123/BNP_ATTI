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
    "lag_3",
    "lag_6",
    "rolling_3",
    "rolling_6",
    "month",
    "year"
]


def prepare_product_data(df):
    df["last_purchase_date"] = pd.to_datetime(
        df["last_purchase_date"],
        errors="coerce"
    )

    df["revenue"] = df["unit_price"] * df["quantity"]

    product_monthly = (
        df.set_index("last_purchase_date")
        .groupby("product_name")["revenue"]
        .resample("MS")
        .sum()
        .reset_index()
    )

    product_monthly.columns = [
        "product_name",
        "date",
        "sales"
    ]

    return product_monthly.sort_values(
        ["product_name", "date"]
    )


def create_features(data):
    data = data.copy()

    grouped_sales = data.groupby("product_name")["sales"]

    data["lag_1"] = grouped_sales.shift(1)
    data["lag_3"] = grouped_sales.shift(3)
    data["lag_6"] = grouped_sales.shift(6)

    data["rolling_3"] = (
        grouped_sales
        .transform(lambda x: x.shift(1).rolling(3).mean())
    )

    data["rolling_6"] = (
        grouped_sales
        .transform(lambda x: x.shift(1).rolling(6).mean())
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
        data["sales"]
    )

    return model


def generate_forecast(model, product_monthly):
    results = []

    future_dates = pd.date_range(
        start="2026-01-01",
        periods=12,
        freq="MS"
    )

    for product, group in product_monthly.groupby("product_name"):

        history = (
            group[["date", "sales"]]
            .sort_values("date")
            .reset_index(drop=True)
        )

        for current_date in future_dates:

            sales_history = history["sales"]

            row = pd.DataFrame([{
                "lag_1": sales_history.iloc[-1],
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

            results.append({
                "product_name": product,
                "date": current_date,
                "predicted_sales": prediction,
                "forecast_year": current_date.year
            })

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

    return pd.DataFrame(results)


def main():
    df = pd.read_excel(DATA_PATH)

    product_monthly = prepare_product_data(df)
    feature_data = create_features(product_monthly)

    model = train_model(feature_data)

    forecast = generate_forecast(
        model,
        product_monthly
    )

    top_products = (
        forecast.groupby("product_name", as_index=False)
        .agg(
            predicted_sales_2026=("predicted_sales", "sum")
        )
        .sort_values(
            "predicted_sales_2026",
            ascending=False
        )
        .head(10)
    )

    forecast.to_csv(
        os.path.join(
            OUTPUT_DIR,
            "product_forecast.csv"
        ),
        index=False
    )

    top_products.to_csv(
        os.path.join(
            OUTPUT_DIR,
            "top_10_products.csv"
        ),
        index=False
    )

    joblib.dump(
        model,
        os.path.join(
            MODEL_DIR,
            "product_model.pkl"
        )
    )

    print("Product forecasting completed successfully.")
    print("\nTop 10 predicted products:")
    print(top_products.to_string(index=False))


if __name__ == "__main__":
    main()