// backend/src/services/mlService.ts
// Reads churn/segment predictions from the ML team's real CSV output when
// present; falls back to a heuristic mock (clearly labeled) otherwise.
// Column names below match the ACTUAL output of Member 2's model —
// verified against customer-churn-sales-forecasting/ml/outputs/*.csv.
//
// Sales/demand/product forecasting and inventory are still mock-derived
// from real order data, since Member 3's ml-only branch output hasn't
// been merged/adopted yet. Same CSV-or-mock seam pattern applies there
// once that data's real path and columns are confirmed with the team.

import fs from 'fs';
import path from 'path';
import { pool } from '../config/database';
import { ChurnPrediction, RiskTier, CustomerSegment } from '../models/churnModel';
import { FrontendCustomer } from '../models/customerModel';
import {
  SalesDataPoint,
  FrontendSalesForecastPoint,
  FrontendProductForecast,
  FrontendDemandForecast,
  FrontendInventoryItem,
} from '../models/forecastModel';

// NOTE: path confirmed to differ from the original Stage 5 plan (ml/ at repo
// root). The ML team's actual structure is customer-churn-sales-forecasting/ml/.
// Adjust these constants if their outputs/ folder ends up somewhere else —
// nothing else in this file needs to change.
const CHURN_CSV_PATH = path.resolve(
  __dirname,
  '../../../customer-churn-sales-forecasting/ml/outputs/churn_predictions.csv'
);
const SEGMENTS_CSV_PATH = path.resolve(
  __dirname,
  '../../../customer-churn-sales-forecasting/ml/outputs/customer_segments.csv'
);

function deriveRiskTier(probability: number): RiskTier {
  if (probability > 0.85) return 'critical';
  if (probability > 0.7) return 'high';
  if (probability > 0.4) return 'medium';
  return 'low';
}

function normalizeRiskLevel(raw: string): RiskTier {
  const lower = raw.trim().toLowerCase();
  if (lower === 'low' || lower === 'medium' || lower === 'high' || lower === 'critical') {
    return lower;
  }
  // Unrecognized value from the model — don't silently guess, fall back
  // to 'medium' so a garbage risk_level never masquerades as a clean tier.
  return 'medium';
}

// Simple CSV line parser handling quoted fields (model output may quote
// fields containing commas, e.g. recommended_action text).
function parseCsvLine(line: string): string[] {
  const cells: string[] = [];
  let current = '';
  let inQuotes = false;
  for (let i = 0; i < line.length; i++) {
    const char = line[i];
    if (char === '"') {
      inQuotes = !inQuotes;
    } else if (char === ',' && !inQuotes) {
      cells.push(current);
      current = '';
    } else {
      current += char;
    }
  }
  cells.push(current);
  return cells.map((c) => c.trim());
}

function parseChurnCsv(csvContent: string): ChurnPrediction[] {
  const lines = csvContent.trim().split('\n');
  const header = parseCsvLine(lines[0]);

  const idx = {
    customer_id: header.indexOf('customer_id'),
    churn_probability: header.indexOf('churn_probability'),
    risk_level: header.indexOf('risk_level'),
    revenue_at_risk: header.indexOf('revenue_at_risk'),
    customer_value: header.indexOf('customer_value'),
    total_orders: header.indexOf('total_orders'),
    total_revenue: header.indexOf('total_revenue'),
  };

  const required = ['customer_id', 'churn_probability', 'risk_level'] as const;
  const missing = required.filter((key) => idx[key] === -1);
  if (missing.length > 0) {
    throw new Error(
      `churn_predictions.csv is missing required columns: ${missing.join(', ')}. Found: ${header.join(', ')}`
    );
  }

  return lines.slice(1).filter((l) => l.trim().length > 0).map((line) => {
    const cells = parseCsvLine(line);
    const probability = parseFloat(cells[idx.churn_probability]);
    return {
      customer_id: cells[idx.customer_id],
      churn_probability: probability,
      risk_tier: normalizeRiskLevel(cells[idx.risk_level]),
      revenue_at_risk: parseFloat(cells[idx.revenue_at_risk] ?? '0'),
      customer_value: parseFloat(cells[idx.customer_value] ?? '0'),
      total_orders: parseInt(cells[idx.total_orders] ?? '0', 10),
      total_revenue: parseFloat(cells[idx.total_revenue] ?? '0'),
      source: 'model' as const,
    };
  });
}

function parseSegmentsCsv(csvContent: string): CustomerSegment[] {
  const lines = csvContent.trim().split('\n');
  const header = parseCsvLine(lines[0]);

  const idx = {
    customer_id: header.indexOf('customer_id'),
    customer_segment: header.indexOf('customer_segment'),
    retention_priority: header.indexOf('retention_priority'),
    recommended_action: header.indexOf('recommended_action'),
    needs_immediate_attention: header.indexOf('needs_immediate_attention'),
    high_value_risk: header.indexOf('high_value_risk'),
    priority_score: header.indexOf('priority_score'),
  };

  const required = ['customer_id', 'customer_segment'] as const;
  const missing = required.filter((key) => idx[key] === -1);
  if (missing.length > 0) {
    throw new Error(
      `customer_segments.csv is missing required columns: ${missing.join(', ')}. Found: ${header.join(', ')}`
    );
  }

  return lines.slice(1).filter((l) => l.trim().length > 0).map((line) => {
    const cells = parseCsvLine(line);
    return {
      customer_id: cells[idx.customer_id],
      customer_segment: cells[idx.customer_segment],
      retention_priority: idx.retention_priority !== -1 ? cells[idx.retention_priority] : '',
      recommended_action: idx.recommended_action !== -1 ? cells[idx.recommended_action] : '',
      needs_immediate_attention: idx.needs_immediate_attention !== -1
        ? cells[idx.needs_immediate_attention].toLowerCase() === 'true'
        : false,
      high_value_risk: idx.high_value_risk !== -1
        ? cells[idx.high_value_risk].toLowerCase() === 'true'
        : false,
      priority_score: idx.priority_score !== -1 ? parseFloat(cells[idx.priority_score]) : 0,
      source: 'model' as const,
    };
  });
}

// Mock fallback: simple heuristic from real customer data. NOT a trained
// model. Used only until churn_predictions.csv exists at the path above.
async function getMockPredictions(): Promise<ChurnPrediction[]> {
  const result = await pool.query<{
    customer_id: string;
    subscription_status: string;
    cancellations_count: number;
  }>('SELECT customer_id, subscription_status, cancellations_count FROM customers');

  return result.rows.map((row) => {
    let probability = 0.1;
    if (row.subscription_status === 'cancelled') probability = 0.9;
    else if (row.subscription_status === 'paused') probability = 0.6;
    probability += Math.min(row.cancellations_count * 0.05, 0.3);
    probability = Math.min(probability, 0.99);

    return {
      customer_id: row.customer_id,
      churn_probability: parseFloat(probability.toFixed(4)),
      risk_tier: deriveRiskTier(probability),
      revenue_at_risk: 0,
      customer_value: 0,
      total_orders: 0,
      total_revenue: 0,
      source: 'mock' as const,
    };
  });
}

async function getMockSegments(): Promise<CustomerSegment[]> {
  const result = await pool.query<{
    customer_id: string;
    subscription_status: string;
    cancellations_count: number;
  }>('SELECT customer_id, subscription_status, cancellations_count FROM customers');

  return result.rows.map((row) => {
    const isAtRisk = row.subscription_status === 'cancelled' || row.cancellations_count >= 2;
    return {
      customer_id: row.customer_id,
      customer_segment: isAtRisk ? 'AT_RISK' : 'STABLE',
      retention_priority: isAtRisk ? 'MEDIUM' : 'LOW',
      recommended_action: isAtRisk ? 'Review account for retention outreach' : 'No action needed',
      needs_immediate_attention: false,
      high_value_risk: false,
      priority_score: 0,
      source: 'mock' as const,
    };
  });
}

export async function getChurnPredictions(): Promise<ChurnPrediction[]> {
  if (fs.existsSync(CHURN_CSV_PATH)) {
    return parseChurnCsv(fs.readFileSync(CHURN_CSV_PATH, 'utf-8'));
  }
  return getMockPredictions();
}

export async function getCustomerSegments(): Promise<CustomerSegment[]> {
  if (fs.existsSync(SEGMENTS_CSV_PATH)) {
    return parseSegmentsCsv(fs.readFileSync(SEGMENTS_CSV_PATH, 'utf-8'));
  }
  return getMockSegments();
}

// Fetches cancellations_count for tiebreaking predictions that share the same
// churn_probability (common with capped/rounded scores). Works whether
// predictions came from the mock heuristic or a real model CSV — this data
// isn't assumed to exist in either source, it's always pulled fresh from
// customers directly.
async function getCancellationCounts(): Promise<Map<string, number>> {
  const result = await pool.query<{ customer_id: string; cancellations_count: number }>(
    'SELECT customer_id, cancellations_count FROM customers'
  );
  return new Map(result.rows.map((r) => [r.customer_id, r.cancellations_count]));
}

async function sortByRiskWithTiebreak(predictions: ChurnPrediction[]): Promise<ChurnPrediction[]> {
  const cancellations = await getCancellationCounts();

  return [...predictions].sort((a, b) => {
    if (b.churn_probability !== a.churn_probability) {
      return b.churn_probability - a.churn_probability;
    }
    const aCancel = cancellations.get(a.customer_id) ?? 0;
    const bCancel = cancellations.get(b.customer_id) ?? 0;
    if (bCancel !== aCancel) {
      return bCancel - aCancel;
    }
    // final deterministic tiebreak so results are stable across requests
    return a.customer_id.localeCompare(b.customer_id);
  });
}

export async function getTopRiskCustomers(limit: number): Promise<ChurnPrediction[]> {
  const predictions = await getChurnPredictions();
  const sorted = await sortByRiskWithTiebreak(predictions);
  return sorted.slice(0, limit);
}

// critical maps to 'High' for the frontend, which only supports three
// tiers — the real 'critical' distinction is preserved on the raw
// ChurnPrediction/risk_tier field for anything that wants it directly.
function capitalizeRiskForFrontend(tier: RiskTier): 'Low' | 'Medium' | 'High' {
  if (tier === 'critical') return 'High';
  return (tier.charAt(0).toUpperCase() + tier.slice(1)) as 'Low' | 'Medium' | 'High';
}

export async function getHighRiskCustomersForFrontend(limit: number = 10): Promise<FrontendCustomer[]> {
  const [predictions, segments] = await Promise.all([
    getChurnPredictions(),
    getCustomerSegments(),
  ]);

  const sorted = await sortByRiskWithTiebreak(predictions);
  const segmentMap = new Map(segments.map((s) => [s.customer_id, s.customer_segment]));

  return sorted.slice(0, limit).map((pred) => ({
    id: pred.customer_id,
    name: pred.customer_id, // no real name field in the dataset
    segment: segmentMap.get(pred.customer_id) ?? 'UNKNOWN',
    churnProbability: pred.churn_probability,
    risk: capitalizeRiskForFrontend(pred.risk_tier),
  }));
}

// ── Sales / demand / product forecasting + inventory ────────────────────
// Still mock-derived from real order data — Member 3's ml-only branch
// output (date-keyed CSVs) has not been adopted yet; same CSV-or-mock
// seam pattern applies here once that data's path/columns are confirmed.

// Real historical sales, bucketed by month from actual order_date values.
// NOT a forecast — this is what actually happened, per the caveat that
// only ~2000 sparse order events exist, not a dense daily sales table.
export async function getSalesHistory(): Promise<SalesDataPoint[]> {
  const result = await pool.query<{ period: string; sales: number }>(`
    SELECT
      TO_CHAR(o.order_date, 'YYYY-MM') AS period,
      SUM(p.unit_price * o.quantity) AS sales
    FROM orders o
    JOIN products p ON o.product_id = p.product_id
    GROUP BY TO_CHAR(o.order_date, 'YYYY-MM')
    ORDER BY period
  `);
  return result.rows.map((r) => ({ period: r.period, sales: parseFloat(r.sales.toString()) }));
}

// Seasonal baseline: forecast each future month from the same month last
// year, not a trailing average — avoids distortion from the dataset's
// sparse final months. Falls back to a trailing-3-month average only if
// no same-month data exists a year back.
export async function getSalesForecastForFrontend(): Promise<FrontendSalesForecastPoint[]> {
  const history = await getSalesHistory();
  const points: FrontendSalesForecastPoint[] = history.map((h) => ({ period: h.period, actual: h.sales }));
  if (history.length === 0) return points;

  const historyMap = new Map(history.map((h) => [h.period, h.sales]));
  const lastPeriod = history[history.length - 1].period;
  const [lastYear, lastMonth] = lastPeriod.split('-').map(Number);

  const trailing = history.slice(-3);
  const fallbackAvg = trailing.reduce((sum, h) => sum + h.sales, 0) / trailing.length;

  for (let i = 1; i <= 3; i++) {
    const futureDate = new Date(lastYear, lastMonth - 1 + i, 1);
    const futurePeriod = `${futureDate.getFullYear()}-${String(futureDate.getMonth() + 1).padStart(2, '0')}`;
    const sameMonthLastYear = `${futureDate.getFullYear() - 1}-${String(futureDate.getMonth() + 1).padStart(2, '0')}`;
    const seasonalValue = historyMap.get(sameMonthLastYear);

    points.push({
      period: futurePeriod,
      forecast: parseFloat((seasonalValue ?? fallbackAvg).toFixed(2)),
    });
  }

  return points;
}

// Mock top-products-by-predicted-sales: ranks by actual historical revenue
// as a stand-in for predicted future sales. NOT a trained model.
export async function getProductForecastForFrontend(limit: number = 10): Promise<FrontendProductForecast[]> {
  const result = await pool.query<{
    product_id: string;
    product_name: string;
    category: string;
    total_units: string;
    total_revenue: number;
  }>(`
    SELECT
      p.product_id,
      p.product_name,
      p.category,
      SUM(o.quantity) AS total_units,
      SUM(p.unit_price * o.quantity) AS total_revenue
    FROM orders o
    JOIN products p ON o.product_id = p.product_id
    GROUP BY p.product_id, p.product_name, p.category
    ORDER BY total_revenue DESC
    LIMIT $1
  `, [limit]);

  return result.rows.map((row, idx) => ({
    rank: idx + 1,
    product: row.product_name,
    category: row.category,
    predictedUnits: parseInt(row.total_units, 10),
    growth: 0, // no historical baseline to compute real growth from — single order per product
  }));
}

// Seasonal demand forecast — same year-over-year approach as sales.
export async function getDemandForecastForFrontend(): Promise<FrontendDemandForecast[]> {
  const result = await pool.query<{ period: string; units: string }>(`
    SELECT TO_CHAR(o.order_date, 'YYYY-MM') AS period, SUM(o.quantity) AS units
    FROM orders o
    GROUP BY TO_CHAR(o.order_date, 'YYYY-MM')
    ORDER BY period
  `);

  const history = result.rows.map((r) => ({ period: r.period, demand: parseInt(r.units, 10) }));
  if (history.length === 0) return [];

  const historyMap = new Map(history.map((h) => [h.period, h.demand]));
  const trailing = history.slice(-3);
  const fallbackAvg = Math.round(trailing.reduce((sum, h) => sum + h.demand, 0) / trailing.length);

  const lastPeriod = history[history.length - 1].period;
  const [lastYear, lastMonth] = lastPeriod.split('-').map(Number);
  const forecastPoints: FrontendDemandForecast[] = [];

  for (let i = 1; i <= 3; i++) {
    const futureDate = new Date(lastYear, lastMonth - 1 + i, 1);
    const futurePeriod = `${futureDate.getFullYear()}-${String(futureDate.getMonth() + 1).padStart(2, '0')}`;
    const sameMonthLastYear = `${futureDate.getFullYear() - 1}-${String(futureDate.getMonth() + 1).padStart(2, '0')}`;
    const seasonalValue = historyMap.get(sameMonthLastYear);

    forecastPoints.push({ period: futurePeriod, demand: seasonalValue ?? fallbackAvg });
  }

  return [...history, ...forecastPoints];
}

// Reorder priority derived from real demand ranking (top/middle/bottom third
// of products by total quantity sold) — NOT a fabricated stock comparison,
// since no stock-tracking data exists in the source dataset.
export async function getInventoryForFrontend(): Promise<FrontendInventoryItem[]> {
  const result = await pool.query<{
    product_name: string;
    category: string;
    total_units: string;
  }>(`
    SELECT p.product_name, p.category, SUM(o.quantity) AS total_units
    FROM orders o
    JOIN products p ON o.product_id = p.product_id
    GROUP BY p.product_id, p.product_name, p.category
    ORDER BY total_units DESC
  `);

  const items = result.rows.map((row) => ({
    product: row.product_name,
    category: row.category,
    predictedDemand: parseInt(row.total_units, 10),
  }));

  const total = items.length;
  const topThird = Math.ceil(total / 3);
  const middleThird = Math.ceil((total * 2) / 3);

  return items.map((item, idx) => ({
    ...item,
    reorderPriority: (idx < topThird ? 'High' : idx < middleThird ? 'Medium' : 'Low') as
      | 'Low'
      | 'Medium'
      | 'High',
  }));
}
