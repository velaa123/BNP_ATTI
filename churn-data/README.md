# BNP_Atti

## Churn Analysis Handoff (Member 2)

This module ranks **active customers for outreach** using an explainable indicator. It does not predict the probability of churn next quarter: the supplied workbook contains one row per customer and no dated future churn labels.

Current `subscription_status` only filters who is eligible for outreach. Do not display the score with a `%` sign.

## Run

From this `ml` directory, install dependencies:

```bash
python -m pip install -r requirements.txt