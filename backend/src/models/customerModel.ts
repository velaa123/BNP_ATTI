// backend/src/models/customerModel.ts
// TypeScript shape of a row in the `customers` table.
// Keep this in sync with database/schema.sql — if a column changes there,
// update it here too, or queries will compile but return mismatched shapes.

export type SubscriptionStatus = 'active' | 'cancelled' | 'paused';

export interface Customer {
  customer_id: string;
  age: number;
  gender: string;
  country: string;
  signup_date: string;        // ISO date string, e.g. "2021-07-01"
  subscription_status: SubscriptionStatus;
  cancellations_count: number;
  purchase_frequency: number;
}

// Query params accepted by the customers list endpoint (Basic tier pagination).
export interface CustomerListParams {
  limit?: number;
  offset?: number;
  country?: string;
  subscription_status?: SubscriptionStatus;
}

// Matches the frontend's Customer type exactly. `name` is set to customer_id
// since no real name field exists in the dataset — NOT a fabricated name,
// just reusing the real identifier.
export interface FrontendCustomer {
  id: string;
  name: string;
  segment: string;
  churnProbability: number;
  risk: 'Low' | 'Medium' | 'High';
}
