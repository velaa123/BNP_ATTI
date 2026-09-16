import type {
  ChurnPrediction,
  Customer,
  CustomerSegmentData,
  DashboardSummary,
  DemandForecast,
  InventoryItem,
  ProductForecast,
  SalesData,
  SalesForecast,
} from '../types'

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || 'http://localhost:8010/api'

async function request<T>(endpoint: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${endpoint}`)

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`)
  }

  const json = await response.json()

  return json.data as T
}

export const api = {
  getDashboardSummary: (): Promise<DashboardSummary> =>
    request<DashboardSummary>('/dashboard/summary'),

  getHighRiskCustomers: (): Promise<Customer[]> =>
    request<Customer[]>('/customers/high-risk'),

  getChurnPredictions: (): Promise<ChurnPrediction[]> =>
    request<ChurnPrediction[]>('/churn/predictions'),

  getCustomerSegments: (): Promise<CustomerSegmentData[]> =>
    request<CustomerSegmentData[]>('/churn/segments'),

  getSalesData: (): Promise<SalesData[]> =>
    request<SalesData[]>('/sales'),

  getSalesForecast: (): Promise<SalesForecast[]> =>
    request<SalesForecast[]>('/sales/forecast'),

  getProductForecast: (): Promise<ProductForecast[]> =>
    request<ProductForecast[]>('/products/forecast'),

  getDemandForecast: (): Promise<DemandForecast[]> =>
    request<DemandForecast[]>('/demand/forecast'),

  getInventory: (): Promise<InventoryItem[]> =>
    request<InventoryItem[]>('/inventory'),
}