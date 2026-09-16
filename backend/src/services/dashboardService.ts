// backend/src/services/dashboardService.ts
// Aggregates dashboard summary KPIs across customers, orders, and churn.
// totalCustomers/revenue are always real data. churnRate uses real historical
// subscription_status (NOT the churn prediction mock — that's a forward-looking
// guess, not a backward-looking rate, and conflating them would mislabel the KPI).
// highRiskCustomers depends on churn predictions (mock until the model lands).

import { pool } from '../config/database';
import * as mlService from './mlService';

export interface DashboardSummary {
  totalCustomers: number;
  churnRate: number;
  revenue: number;
  highRiskCustomers: number;
}

export async function getDashboardSummary(): Promise<DashboardSummary> {
  const [customerCountResult, revenueResult, cancelledCountResult, predictions] = await Promise.all([
    pool.query<{ count: string }>('SELECT COUNT(*) FROM customers'),
    pool.query<{ total: number | null }>(`
      SELECT SUM(p.unit_price * o.quantity) AS total
      FROM orders o
      JOIN products p ON o.product_id = p.product_id
    `),
    pool.query<{ count: string }>(
      "SELECT COUNT(*) FROM customers WHERE subscription_status = 'cancelled'"
    ),
    mlService.getChurnPredictions(),
  ]);

  const totalCustomers = parseInt(customerCountResult.rows[0].count, 10);
  const cancelledCount = parseInt(cancelledCountResult.rows[0].count, 10);
  const revenue = revenueResult.rows[0].total ?? 0;
  const churnRate = totalCustomers > 0 ? parseFloat(((cancelledCount / totalCustomers) * 100).toFixed(2)) : 0;
  const highRiskCustomers = predictions.filter((p) => p.risk_tier === 'high' || p.risk_tier === 'critical').length;

  return { totalCustomers, churnRate, revenue, highRiskCustomers };
}
