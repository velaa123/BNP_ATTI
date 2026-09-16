// backend/src/services/mlService.ts
// Reads churn/segment predictions from the ML team's real CSV output when
// present; falls back to a heuristic mock (clearly labeled) otherwise.
// Same CSV-or-mock pattern now applies to sales/demand/product forecasting,
// reading Member 3's real output from ml/outputs/ when present.

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

// Churn/segments — Member 2's output path (unconfirmed after the ML folder
// was accidentally deleted and not yet re-added; falls back to mock).
const CHURN_CSV_PATH = path.resolve(
  __dirname,
  '../../../customer-churn-sales-forecasting/ml/outputs/churn_predictions.csv'
);
const SEGMENTS_CSV_PATH = path.resolve(
  __dirname,
  '../../../customer-churn-sales-forecasting/ml/outputs/customer_segments.csv'
);

// Sales/demand/product forecasting — Member 3's confirmed real output path.
const SALES_FORECAST_CSV_PATH = path.resolve(__dirname, '../../../ml/outputs/sales_forecast.csv');
const DEMAND_FORECAST_CSV_PATH = path.resolve(__dirname, '../../../ml/outputs/demand_forecast.csv');
const TOP_PRODUCTS_CSV_PATH = path.resolve(__dirname, '../../../ml/outputs/top_10_products.csv');

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
  return 'medium';
}

// Simple CSV line parser handling quoted fields.
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

// ── Churn predictions ────────────────────────────────────────────────────

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
    if (bCancel !== aCancel) return bCancel - aCancel;
    return a.customer_id.localeCompare(b.customer_id);
  });
}

export async function getTopRiskCustomers(limit: number): Promise<ChurnPrediction[]> {
  const predictions = await getChurnPredictions();
  const sorted = await sortByRiskWithTiebreak(predictions);
  return sorted.slice(0, limit);
}

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
    name: pred.customer_id,
    segment: segmentMap.get(pred.customer_id) ?? 'UNKNOWN',
    churnProbability: pred.churn_probability,
    risk: capitalizeRiskForFrontend(pred.risk_tier),
  }));
}

// ── Sales / demand / product forecasting ────────────────────────────────

function parseSalesForecastCsv(csvContent: string): { period: string; forecast: number }[] {
  const lines = csvContent.trim().split('\n');
  const header = parseCsvLine(lines[0]);
  const dateIdx = header.indexOf('date');
  const salesIdx = header.indexOf('predicted_sales');

  if (dateIdx === -1 || salesIdx === -1) {
    throw new Error(`sales_forecast.csv missing required columns. Found: ${header.join(', ')}`);
  }

  return lines.slice(1).filter((l) => l.trim().length > 0).map((line) => {
    const cells = parseCsvLine(line);
    const period = cells[dateIdx].slice(0, 7); // 'YYYY-MM-DD' -> 'YYYY-MM'
    return { period, forecast: parseFloat(cells[salesIdx]) };
  });
}

function parseDemandForecastCsv(csvContent: string): { period: string; demand: number }[] {
  const lines = csvContent.trim().split('\n');
  const header = parseCsvLine(lines[0]);
  const dateIdx = header.indexOf('date');
  const demandIdx = header.indexOf('predicted_demand');

  if (dateIdx === -1 || demandIdx === -1) {
    throw new Error(`demand_forecast.csv missing required columns. Found: ${header.join(', ')}`);
  }

  return lines.slice(1).filter((l) => l.trim().length > 0).map((line) => {
    const cells = parseCsvLine(line);
    const period = cells[dateIdx].slice(0, 7);
    return { period, demand: Math.round(parseFloat(cells[demandIdx])) };
  });
}

function parseTopProductsCsv(csvContent: string): { product_name: string; predicted_sales_2026: number }[] {
  const lines = csvContent.trim().split('\n');
  const header = parseCsvLine(lines[0]);
  const nameIdx = header.indexOf('product_name');
  const salesIdx = header.indexOf('predicted_sales_2026');

  if (nameIdx === -1 || salesIdx === -1) {
    throw new Error(`top_10_products.csv missing required columns. Found: ${header.join(', ')}`);
  }

  return lines.slice(1).filter((l) => l.trim().length > 0).map((line) => {
    const cells = parseCsvLine(line);
    return { product_name: cells[nameIdx], predicted_sales_2026: parseFloat(cells[salesIdx]) };
  });
}

// Real historical sales, bucketed by month from actual order_date values.
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

export async function getSalesForecastForFrontend(): Promise<FrontendSalesForecastPoint[]> {
  const history = await getSalesHistory();
  const points: FrontendSalesForecastPoint[] = history.map((h) => ({ period: h.period, actual: h.sales }));

  if (fs.existsSync(SALES_FORECAST_CSV_PATH)) {
    const realForecast = parseSalesForecastCsv(fs.readFileSync(SALES_FORECAST_CSV_PATH, 'utf-8'));
    realForecast.forEach((f) => points.push({ period: f.period, forecast: parseFloat(f.forecast.toFixed(2)) }));
    return points;
  }

  // Mock fallback: seasonal year-over-year baseline.
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
    points.push({ period: futurePeriod, forecast: parseFloat((seasonalValue ?? fallbackAvg).toFixed(2)) });
  }
  return points;
}

export async function getDemandForecastForFrontend(): Promise<FrontendDemandForecast[]> {
  const result = await pool.query<{ period: string; units: string }>(`
    SELECT TO_CHAR(o.order_date, 'YYYY-MM') AS period, SUM(o.quantity) AS units
    FROM orders o GROUP BY TO_CHAR(o.order_date, 'YYYY-MM') ORDER BY period
  `);
  const history = result.rows.map((r) => ({ period: r.period, demand: parseInt(r.units, 10) }));

  if (fs.existsSync(DEMAND_FORECAST_CSV_PATH)) {
    const realForecast = parseDemandForecastCsv(fs.readFileSync(DEMAND_FORECAST_CSV_PATH, 'utf-8'));
    return [...history, ...realForecast];
  }

  // Mock fallback: seasonal year-over-year baseline.
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

export async function getProductForecastForFrontend(limit: number = 10): Promise<FrontendProductForecast[]> {
  if (fs.existsSync(TOP_PRODUCTS_CSV_PATH)) {
    const topProducts = parseTopProductsCsv(fs.readFileSync(TOP_PRODUCTS_CSV_PATH, 'utf-8'));

    const results: FrontendProductForecast[] = [];
    for (let i = 0; i < Math.min(topProducts.length, limit); i++) {
      const tp = topProducts[i];

      // product_name isn't guaranteed unique in this dataset (duplicates like
      // "Running Shoes" / "RunningShoes" seen before) — this takes the first
      // match, an approximation worth knowing about, not a hidden assumption.
      const lookup = await pool.query<{ category: string; total_revenue: string | null }>(`
        SELECT p.category, SUM(p.unit_price * o.quantity) AS total_revenue
        FROM products p
        LEFT JOIN orders o ON o.product_id = p.product_id
        WHERE p.product_name = $1
        GROUP BY p.category
        LIMIT 1
      `, [tp.product_name]);

      const category = lookup.rows[0]?.category ?? 'Unknown';
      const historicalRevenue = parseFloat(lookup.rows[0]?.total_revenue ?? '0');
      const growth = historicalRevenue > 0
        ? parseFloat((((tp.predicted_sales_2026 - historicalRevenue) / historicalRevenue) * 100).toFixed(1))
        : 0;

      results.push({
        rank: i + 1,
        product: tp.product_name,
        category,
        // NOTE: this is a predicted sales VALUE (currency), not a unit count.
        // top_10_products.csv gives predicted_sales_2026, not unit volume —
        // flagged to the team, may need a field rename discussion later.
        predictedUnits: Math.round(tp.predicted_sales_2026),
        growth,
      });
    }
    return results;
  }

  // Mock fallback: rank by real historical revenue.
  const result = await pool.query<{
    product_id: string; product_name: string; category: string;
    total_units: string; total_revenue: number;
  }>(`
    SELECT p.product_id, p.product_name, p.category, SUM(o.quantity) AS total_units, SUM(p.unit_price * o.quantity) AS total_revenue
    FROM orders o JOIN products p ON o.product_id = p.product_id
    GROUP BY p.product_id, p.product_name, p.category ORDER BY total_revenue DESC LIMIT $1
  `, [limit]);

  return result.rows.map((row, idx) => ({
    rank: idx + 1,
    product: row.product_name,
    category: row.category,
    predictedUnits: parseInt(row.total_units, 10),
    growth: 0,
  }));
}

// ── Inventory ────────────────────────────────────────────────────────────
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