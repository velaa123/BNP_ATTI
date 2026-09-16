// backend/src/services/customerService.ts
// All Postgres query logic for customers. Controllers call these functions
// and never write SQL directly — keeps query logic in one place per resource.

import { pool } from '../config/database';
import { Customer, CustomerListParams } from '../models/customerModel';

export async function getCustomers(params: CustomerListParams): Promise<{ customers: Customer[]; total: number }> {
  const limit = params.limit ?? 50;
  const offset = params.offset ?? 0;

  const conditions: string[] = [];
  const values: (string | number)[] = [];
  let paramIndex = 1;

  if (params.country) {
    conditions.push(`country = $${paramIndex++}`);
    values.push(params.country);
  }
  if (params.subscription_status) {
    conditions.push(`subscription_status = $${paramIndex++}`);
    values.push(params.subscription_status);
  }

  const whereClause = conditions.length > 0 ? `WHERE ${conditions.join(' AND ')}` : '';

  const countResult = await pool.query<{ count: string }>(
    `SELECT COUNT(*) FROM customers ${whereClause}`,
    values
  );
  const total = parseInt(countResult.rows[0].count, 10);

  const dataResult = await pool.query<Customer>(
    `SELECT * FROM customers ${whereClause} ORDER BY customer_id LIMIT $${paramIndex++} OFFSET $${paramIndex++}`,
    [...values, limit, offset]
  );

  return { customers: dataResult.rows, total };
}

export async function getCustomerById(customerId: string): Promise<Customer | null> {
  const result = await pool.query<Customer>(
    'SELECT * FROM customers WHERE customer_id = $1',
    [customerId]
  );
  return result.rows[0] ?? null;
}
