import os
import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

INPUT_FILE = os.path.join(
    BASE_DIR,
    "ml",
    "data",
    "raw",
    "dataset.xls"
)

OUTPUT_DIR = os.path.join(
    BASE_DIR,
    "ml",
    "data",
    "processed"
)

OUTPUT_FILE = os.path.join(
    OUTPUT_DIR,
    "cleaned_data.csv"
)


# ============================================================
# EXPECTED COLUMNS
# ============================================================

EXPECTED_COLUMNS = [
    "order_id",
    "customer_id",
    "age",
    "gender",
    "product_id",
    "country",
    "signup_date",
    "last_purchase_date",
    "cancellations_count",
    "subscription_status",
    "unit_price",
    "quantity",
    "purchase_frequency",
    "product_name",
    "category",
    "Ratings"
]


# ============================================================
# LOAD DATASET
# ============================================================

def load_dataset():
    """
    Load the default raw dataset used by the cleaning pipeline.
    """

    print("=" * 70)
    print("CUSTOMER CHURN PROJECT - DATA CLEANING")
    print("=" * 70)

    print("\n[1/8] Loading dataset...")
    print(f"Input file: {INPUT_FILE}")

    if not os.path.exists(INPUT_FILE):
        raise FileNotFoundError(
            "\nDataset not found.\n"
            f"Expected location:\n{INPUT_FILE}\n\n"
            "Make sure dataset.xls is inside:\n"
            "ml/data/raw/"
        )

    try:
        df = pd.read_excel(INPUT_FILE)

    except ImportError:
        print("\nERROR: Required Excel package is missing.")
        print("Install it using:")
        print("pip install xlrd")
        raise

    except Exception as e:
        raise RuntimeError(
            "Could not read the Excel dataset.\n"
            f"Error: {e}"
        )

    print("Dataset loaded successfully.")
    print(f"Rows: {len(df)}")
    print(f"Columns: {len(df.columns)}")

    return df


# ============================================================
# LOAD CUSTOMERS
# ============================================================

def load_customers(input_path):
    """
    Load and clean customer data for run_churn.py.

    Unlike load_dataset(), this function accepts an explicit
    input file path.

    The complete cleaning process is applied before returning
    the DataFrame.
    """

    input_path = os.fspath(input_path)

    print("=" * 70)
    print("CUSTOMER CHURN PROJECT - CUSTOMER DATA LOADING")
    print("=" * 70)

    print("\nInput file:")
    print(input_path)

    if not os.path.exists(input_path):
        raise FileNotFoundError(
            "\nInput dataset not found.\n"
            f"Expected location:\n{input_path}"
        )

    try:
        df = pd.read_excel(input_path)

    except ImportError:
        print("\nERROR: Required Excel package is missing.")
        print("Install it using:")
        print("pip install xlrd")
        raise

    except Exception as e:
        raise RuntimeError(
            "Could not read the Excel dataset.\n"
            f"Error: {e}"
        )

    print("\nDataset loaded successfully.")
    print(f"Rows: {len(df)}")
    print(f"Columns: {len(df.columns)}")

    # --------------------------------------------------------
    # 1. Validate columns
    # --------------------------------------------------------

    df = validate_columns(df)

    # --------------------------------------------------------
    # 2. Clean string columns
    # --------------------------------------------------------

    df = clean_string_columns(df)

    # --------------------------------------------------------
    # 3. Clean date columns
    # --------------------------------------------------------

    df = clean_date_columns(df)

    # --------------------------------------------------------
    # 4. Clean numeric columns
    # --------------------------------------------------------

    df = clean_numeric_columns(df)

    # --------------------------------------------------------
    # 5. Remove duplicates
    # --------------------------------------------------------

    df = remove_duplicates(df)

    # --------------------------------------------------------
    # 6. Handle missing values
    # --------------------------------------------------------

    df = handle_missing_values(df)

    # --------------------------------------------------------
    # 7. Check date consistency
    # --------------------------------------------------------

    df = check_date_consistency(df)

    # --------------------------------------------------------
    # 8. Sort data
    # --------------------------------------------------------

    df = sort_data(df)

    print("\nCustomer data preparation completed successfully.")
    print(f"Final rows: {len(df)}")
    print(f"Final columns: {len(df.columns)}")

    return df


# ============================================================
# VALIDATE COLUMNS
# ============================================================

def validate_columns(df):
    """
    Validate that all required columns are present.
    """

    print("\n[2/8] Validating columns...")

    actual_columns = list(df.columns)

    missing_columns = [
        column
        for column in EXPECTED_COLUMNS
        if column not in actual_columns
    ]

    extra_columns = [
        column
        for column in actual_columns
        if column not in EXPECTED_COLUMNS
    ]

    if missing_columns:
        raise ValueError(
            "\nMissing required columns:\n"
            f"{missing_columns}\n\n"
            "Columns found:\n"
            f"{actual_columns}"
        )

    if extra_columns:
        print(
            f"Extra columns found: {extra_columns}"
        )

    # Keep only expected columns and fixed order.
    df = df[EXPECTED_COLUMNS].copy()

    print("Column validation successful.")

    return df


# ============================================================
# CLEAN STRING COLUMNS
# ============================================================

def clean_string_columns(df):
    """
    Clean text/string columns.
    """

    print("\n[3/8] Cleaning text columns...")

    string_columns = [
        "order_id",
        "customer_id",
        "gender",
        "product_id",
        "country",
        "subscription_status",
        "product_name",
        "category"
    ]

    for column in string_columns:

        df[column] = (
            df[column]
            .astype("string")
            .str.strip()
        )

        # Convert empty strings to missing values.
        df[column] = df[column].replace(
            "",
            pd.NA
        )

    print("Text columns cleaned.")

    return df


# ============================================================
# CLEAN DATE COLUMNS
# ============================================================

def clean_date_columns(df):
    """
    Convert date columns to pandas datetime.
    """

    print("\n[4/8] Cleaning date columns...")

    date_columns = [
        "signup_date",
        "last_purchase_date"
    ]

    for column in date_columns:

        df[column] = pd.to_datetime(
            df[column],
            errors="coerce"
        )

    for column in date_columns:

        invalid_count = df[column].isna().sum()

        if invalid_count > 0:
            print(
                f"Warning: {invalid_count} invalid/missing "
                f"dates found in {column}."
            )

    print("Date columns converted successfully.")

    return df


# ============================================================
# CLEAN NUMERIC COLUMNS
# ============================================================

def clean_numeric_columns(df):
    """
    Convert numeric columns to numeric dtype and report
    suspicious values.
    """

    print("\n[5/8] Cleaning numeric columns...")

    numeric_columns = [
        "age",
        "cancellations_count",
        "unit_price",
        "quantity",
        "purchase_frequency",
        "Ratings"
    ]

    for column in numeric_columns:

        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )

    # --------------------------------------------------------
    # Check suspicious values
    # --------------------------------------------------------

    if (df["age"] <= 0).any():

        count = (
            df["age"] <= 0
        ).sum()

        print(
            f"Warning: {count} rows have invalid age values."
        )

    if (df["unit_price"] < 0).any():

        count = (
            df["unit_price"] < 0
        ).sum()

        print(
            f"Warning: {count} rows have negative unit prices."
        )

    if (df["quantity"] <= 0).any():

        count = (
            df["quantity"] <= 0
        ).sum()

        print(
            f"Warning: {count} rows have invalid quantity values."
        )

    if (df["purchase_frequency"] < 0).any():

        count = (
            df["purchase_frequency"] < 0
        ).sum()

        print(
            f"Warning: {count} rows have invalid "
            f"purchase frequency values."
        )

    if (df["cancellations_count"] < 0).any():

        count = (
            df["cancellations_count"] < 0
        ).sum()

        print(
            f"Warning: {count} rows have invalid "
            f"cancellation counts."
        )

    if (
        (df["Ratings"] < 0)
        | (df["Ratings"] > 5)
    ).any():

        count = (
            (df["Ratings"] < 0)
            | (df["Ratings"] > 5)
        ).sum()

        print(
            f"Warning: {count} rows have ratings "
            f"outside the expected 0-5 range."
        )

    print("Numeric columns cleaned.")

    return df


# ============================================================
# REMOVE DUPLICATES
# ============================================================

def remove_duplicates(df):
    """
    Remove duplicate order records and completely
    duplicated rows.
    """

    print("\n[6/8] Checking duplicate records...")

    before = len(df)

    duplicate_order_ids = (
        df["order_id"].duplicated().sum()
    )

    if duplicate_order_ids > 0:

        print(
            f"Duplicate order IDs found: "
            f"{duplicate_order_ids}"
        )

        df = df.drop_duplicates(
            subset=["order_id"],
            keep="first"
        )

    # Also remove completely duplicated rows.
    df = df.drop_duplicates()

    after = len(df)

    removed = before - after

    print(
        f"Duplicate rows removed: {removed}"
    )

    print(
        f"Rows remaining: {after}"
    )

    return df


# ============================================================
# HANDLE MISSING VALUES
# ============================================================

def handle_missing_values(df):
    """
    Handle missing numeric and categorical values.
    """

    print("\n[7/8] Handling missing values...")

    numeric_columns = [
        "age",
        "cancellations_count",
        "unit_price",
        "quantity",
        "purchase_frequency",
        "Ratings"
    ]

    categorical_columns = [
        "gender",
        "country",
        "subscription_status",
        "product_name",
        "category"
    ]

    # --------------------------------------------------------
    # Numeric missing values
    # --------------------------------------------------------

    for column in numeric_columns:

        missing_count = (
            df[column].isna().sum()
        )

        if missing_count > 0:

            median_value = df[column].median()

            if pd.isna(median_value):
                median_value = 0

            df[column] = (
                df[column]
                .fillna(median_value)
            )

            print(
                f"{column}: filled "
                f"{missing_count} missing values "
                f"with median ({median_value})"
            )

    # --------------------------------------------------------
    # Categorical missing values
    # --------------------------------------------------------

    for column in categorical_columns:

        missing_count = (
            df[column].isna().sum()
        )

        if missing_count > 0:

            df[column] = (
                df[column]
                .fillna("Unknown")
            )

            print(
                f"{column}: filled "
                f"{missing_count} missing values "
                "with 'Unknown'"
            )

    # --------------------------------------------------------
    # ID columns
    # --------------------------------------------------------

    id_columns = [
        "order_id",
        "customer_id",
        "product_id"
    ]

    for column in id_columns:

        missing_count = (
            df[column].isna().sum()
        )

        if missing_count > 0:

            print(
                f"Warning: {column} contains "
                f"{missing_count} missing values."
            )

    # --------------------------------------------------------
    # Date columns
    # --------------------------------------------------------

    date_columns = [
        "signup_date",
        "last_purchase_date"
    ]

    for column in date_columns:

        missing_count = (
            df[column].isna().sum()
        )

        if missing_count > 0:

            print(
                f"Warning: {column} contains "
                f"{missing_count} missing/invalid dates."
            )

    return df


# ============================================================
# CHECK DATE CONSISTENCY
# ============================================================

def check_date_consistency(df):
    """
    Check whether signup_date occurs after
    last_purchase_date.
    """

    print("\nChecking date consistency...")

    valid_dates = (
        df["signup_date"].notna()
        & df["last_purchase_date"].notna()
    )

    inconsistent = (
        valid_dates
        & (
            df["signup_date"]
            > df["last_purchase_date"]
        )
    )

    inconsistent_count = (
        inconsistent.sum()
    )

    if inconsistent_count > 0:

        print(
            f"Warning: {inconsistent_count} rows have "
            "signup_date after last_purchase_date."
        )

        print(
            "These rows are NOT deleted because they may "
            "represent source-data inconsistencies."
        )

    else:

        print(
            "No signup/last-purchase date inconsistencies found."
        )

    return df


# ============================================================
# SORT DATA
# ============================================================

def sort_data(df):
    """
    Sort data by customer, purchase date and order.
    """

    print("\nSorting dataset...")

    sort_columns = [
        "customer_id",
        "last_purchase_date",
        "order_id"
    ]

    df = df.sort_values(
        by=sort_columns,
        na_position="last"
    ).reset_index(drop=True)

    return df


# ============================================================
# SAVE CLEANED DATA
# ============================================================

def save_dataset(df):
    """
    Save the cleaned dataset.
    """

    print("\n[8/8] Saving cleaned dataset...")

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True
    )

    df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print(
        "Cleaned dataset saved successfully."
    )

    print(
        f"Output file: {OUTPUT_FILE}"
    )


# ============================================================
# PRINT FINAL SUMMARY
# ============================================================

def print_summary(df):
    """
    Print final cleaning summary.
    """

    print("\n")
    print("=" * 70)
    print("CLEANING COMPLETE")
    print("=" * 70)

    print(
        f"Final rows       : {len(df)}"
    )

    print(
        f"Final columns    : {len(df.columns)}"
    )

    print(
        f"Unique customers : "
        f"{df['customer_id'].nunique(dropna=True)}"
    )

    print(
        f"Unique orders    : "
        f"{df['order_id'].nunique(dropna=True)}"
    )

    print(
        f"Unique products  : "
        f"{df['product_id'].nunique(dropna=True)}"
    )

    print("\nColumns:")

    for column in df.columns:
        print(
            f"  - {column}"
        )

    print("\nRemaining missing values:")

    missing_values = df.isna().sum()

    has_missing = False

    for column, count in missing_values.items():

        if count > 0:

            has_missing = True

            print(
                f"  - {column}: {count}"
            )

    if not has_missing:
        print("  None")

    print("\nData types:")

    print(df.dtypes)

    print("\nFirst 5 rows:")

    print(df.head())

    print("\n" + "=" * 70)
    print("NEXT STEP:")
    print("Use cleaned_data.csv for feature engineering.")
    print("=" * 70)


# ============================================================
# MAIN
# ============================================================

def main():

    try:

        # Step 1: Load
        df = load_dataset()

        # Step 2: Validate columns
        df = validate_columns(df)

        # Step 3: Clean strings
        df = clean_string_columns(df)

        # Step 4: Clean dates
        df = clean_date_columns(df)

        # Step 5: Clean numeric values
        df = clean_numeric_columns(df)

        # Step 6: Remove duplicates
        df = remove_duplicates(df)

        # Step 7: Handle missing values
        df = handle_missing_values(df)

        # Additional consistency check
        df = check_date_consistency(df)

        # Sort records
        df = sort_data(df)

        # Save
        save_dataset(df)

        # Final report
        print_summary(df)

    except Exception as e:

        print("\n")
        print("=" * 70)
        print("DATA CLEANING FAILED")
        print("=" * 70)

        print(
            f"Error: {e}"
        )

        print("=" * 70)

        raise


# ============================================================
# RUN PROGRAM
# ============================================================

if __name__ == "__main__":
    main()