"""Generate the backend handoff CSV files from the supplied workbook."""

import argparse
import json
from pathlib import Path

from churn.evaluate import audit
from churn.predict import rank_active_customers
from preprocessing.clean_data import load_customers


def main() -> None:
    folder = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=folder / "data/raw/dataset.xls")
    parser.add_argument("--output", type=Path, default=folder / "outputs")
    parser.add_argument("--as-of", help="Optional YYYY-MM-DD snapshot date")
    args = parser.parse_args()

    customers = load_customers(args.input)
    ranked, cutoff = rank_active_customers(customers, as_of=args.as_of)
    args.output.mkdir(parents=True, exist_ok=True)
    ranked.to_csv(args.output / "churn_predictions.csv", index=False)
    ranked[["customer_id", "risk_score", "risk_segment"]].to_csv(
        args.output / "customer_segments.csv", index=False
    )
    diagnostics = audit(customers, ranked)
    diagnostics["as_of"] = cutoff.strftime("%Y-%m-%d")
    (args.output / "churn_audit.json").write_text(json.dumps(diagnostics, indent=2), encoding="utf-8")
    print(json.dumps(diagnostics, indent=2))
    print("\nTop 10 active customers:\n", ranked.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
