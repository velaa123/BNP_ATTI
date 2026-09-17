// backend/src/models/anomalyModel.ts
// Two distinct anomaly detection methods, kept separate and clearly labeled:
// 1. Statistical (IQR) outliers on churn_probability — may legitimately be
//    empty if the distribution has high natural variance (no single value
//    stands out relative to the population).
// 2. Extreme business-risk flags on revenue_at_risk — top 1% by dollar
//    exposure, a different and complementary signal, not a fallback
//    pretending to be the same thing as #1.

export interface ChurnAnomaly {
  customer_id: string;
  churn_probability: number;
  reason: string;
}

export interface HighRiskExposure {
  customer_id: string;
  revenue_at_risk: number;
  churn_probability: number;
  reason: string;
}

export interface SalesAnomaly {
  period: string;
  actual_sales: number;
  expected_range_low: number;
  expected_range_high: number;
  deviation_percent: number;
}

export interface AnomalyReport {
  churn_anomalies: ChurnAnomaly[];
  churn_anomaly_note: string;    // explains why this may be empty — not silent
  high_risk_exposures: HighRiskExposure[];
  sales_anomalies: SalesAnomaly[];
  churn_probability_bounds: { lower: number; upper: number; q1: number; q3: number };
  generated_at: string;
}