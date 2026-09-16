// backend/src/models/churnModel.ts
// Matches the ACTUAL columns produced by the churn ML model
// (customer-churn-sales-forecasting/ml/outputs/churn_predictions.csv
// and customer_segments.csv), not an invented minimal contract.

export type RiskTier = 'low' | 'medium' | 'high' | 'critical';
export type PredictionSource = 'model' | 'mock';

export interface ChurnPrediction {
  customer_id: string;
  churn_probability: number;       // 0-1
  risk_tier: RiskTier;             // normalized lowercase from risk_level
  revenue_at_risk: number;
  customer_value: number;
  total_orders: number;
  total_revenue: number;
  source: PredictionSource;
}

// customer_segment values are model-defined strings (e.g. 'CRITICAL_RETENTION')
// — kept as raw string rather than a narrow union, since the model may
// introduce new segment names the backend shouldn't hardcode against.
export interface CustomerSegment {
  customer_id: string;
  customer_segment: string;
  retention_priority: string;
  recommended_action: string;
  needs_immediate_attention: boolean;
  high_value_risk: boolean;
  priority_score: number;
  source: PredictionSource;
}
