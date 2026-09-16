import pandas as pd
import unittest

from churn.predict import rank_active_customers
from preprocessing.clean_data import clean_customers


def sample():
    return pd.DataFrame(
        {
            "customer_id": ["A", "B", "C", "D"],
            "signup_date": ["1/1/2024", "1/1/2024", "1/1/2024", "1/1/2025"],
            "last_purchase_date": ["1/2/2024", "12/1/2025", "1/2/2024", "1/1/2024"],
            "subscription_status": ["active", "active", "cancelled", "active"],
            "purchase_frequency": [1, 30, 1, 1],
            "Ratings": [1.0, 5.0, 1.0, 1.0],
        }
    )


class ChurnTests(unittest.TestCase):
    def test_invalid_and_cancelled_are_excluded_and_ranking_is_explainable(self):
        customers = clean_customers(sample())
        self.assertEqual(int(customers["invalid_date"].sum()), 1)
        ranked, as_of = rank_active_customers(customers)
        self.assertEqual(as_of, pd.Timestamp("2025-12-01"))
        self.assertEqual(ranked["customer_id"].tolist(), ["A", "B"])
        self.assertGreater(ranked.loc[0, "risk_score"], ranked.loc[1, "risk_score"])
        self.assertEqual(ranked.loc[0, "reason"], "long time since last purchase")

    def test_missing_and_duplicate_ids_fail_fast(self):
        customers = sample()
        customers.loc[1, "customer_id"] = "A"
        with self.assertRaisesRegex(ValueError, "unique"):
            clean_customers(customers)


if __name__ == "__main__":
    unittest.main()
