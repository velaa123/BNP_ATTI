// backend/src/models/forecastModel.ts
// TypeScript shapes for sales, demand, product forecasting, and inventory data.

export type PredictionSource = 'model' | 'mock';

export interface SalesForecast {
  product_id: string;
  product_name: string;
  period_start: string;
  period_end: string;
  forecasted_sales: number;
  source: PredictionSource;
}

export interface DemandForecast {
  product_id: string;
  product_name: string;
  period_start: string;
  period_end: string;
  forecasted_units: number;
  source: PredictionSource;
}

// Matches frontend's SalesData type: real historical sales, not forecast.
export interface SalesDataPoint {
  period: string;
  sales: number;
}

// Matches frontend's SalesForecast type: period with actual and/or forecast values.
export interface FrontendSalesForecastPoint {
  period: string;
  actual?: number;
  forecast?: number;
}

// Matches frontend's ProductForecast type.
export interface FrontendProductForecast {
  rank: number;
  product: string;
  category: string;
  predictedUnits: number;
  growth: number;
}

// Matches frontend's DemandForecast type.
export interface FrontendDemandForecast {
  period: string;
  demand: number;
}

// Matches frontend's InventoryItem type — reframed from a fabricated
// "current stock" concept (no such data exists in the source dataset)
// to a real, demand-derived reorder priority.
export interface FrontendInventoryItem {
  product: string;
  category: string;
  predictedDemand: number;
  reorderPriority: 'Low' | 'Medium' | 'High';
}
