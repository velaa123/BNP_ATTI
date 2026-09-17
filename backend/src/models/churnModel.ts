// backend/src/models/churnModel.ts
// Matches the ACTUAL columns produced by the real V2 churn model
// (churn-data/outputs/churn_predictions.csv and customer_segments.csv).
// This is the full, rich schema — churn_probability, financial fields,
// and business segmentation are all genuine model/pipeline output now.

export type RiskTier = 'low' | 'medium' | 'high' | 'critical';
export type PredictionSource = 'model' | 'mock';

export interface ChurnPrediction {
  customer_id: string;
  churn_probability: number;       // real 0-1 value from the model
  risk_tier: RiskTier;             // normalized lowercase from risk_segment
  revenue_at_risk: number;
  customer_value: number;
  total_orders: number;
  total_revenue: number;
  reason?: string;
  days_since_purchase?: number;
  source: PredictionSource;
}

export interface CustomerSegment {
  customer_id: string;
  customer_segment: string;        // e.g. 'CRITICAL_RETENTION', 'LOYAL_ACTIVE'
  retention_priority: string;      // e.g. 'URGENT', 'HIGH', 'MEDIUM', 'LOW'
  recommended_action: string;      // real, from the model pipeline now
  needs_immediate_attention: boolean;
  high_value_risk: boolean;
  priority_score: number;
  source: PredictionSource;
}