export type RiskLevel = 'Low' | 'Medium' | 'High'

export type StockStatus = 'Healthy' | 'Low' | 'Critical'

export interface Customer {
  id: string
  churnProbability: number
  risk: RiskLevel
  source?: 'model' | 'mock'
}

export interface ChurnSummary {
  churnRate: number
  highRiskCustomers: number
  mediumRiskCustomers: number
  lowRiskCustomers: number
  retentionRate: number
}

export interface SalesData {
  period: string
  sales: number
}

export interface SalesForecast {
  period: string
  actual?: number
  forecast?: number
}

export interface ProductForecast {
  rank: number
  product: string
  category: string
  predictedUnits: number
  growth: number
}

export interface DemandForecast {
  period: string
  demand: number
}

export interface InventoryItem {
  product: string
  category: string
  predictedDemand: number
  reorderPriority: 'Low' | 'Medium' | 'High'
}

export interface DashboardSummary {
  totalCustomers: number
  churnRate: number
  revenue: number
  highRiskCustomers: number
}