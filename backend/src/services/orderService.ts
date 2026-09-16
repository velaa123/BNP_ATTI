// backend/src/services/orderService.ts
// All Postgres query logic for orders — joins in product and customer
// context so the frontend gets a complete row without extra lookups.

import { pool } from '../config/database';
import { Order, OrderListParams } from '../models/orderModel';

const BASE_SELECT = `
  SELECT
    o.order_id,
    o.customer_id,
    o.product_id,
    o.quantity,
    o.order_date,
    o.rating,
    p.product_name,
    p.category,
    p.unit_price,
    c.country
  FROM orders o
  JOIN products p ON o.product_id = p.product_id
  JOIN customers c ON o.customer_id = c.customer_id
`;

export async function getOrders(params: OrderListParams): Promise<{ orders: Order[]; total: number }> {
  const limit = params.limit ?? 50;
  const offset = params.offset ?? 0;

  const conditions: string[] = [];
  const values: (string | number)[] = [];
  let paramIndex = 1;

  if (params.customer_id) {
    conditions.push(`o.customer_id = $${paramIndex++}`);
    values.push(params.customer_id);
  }
  if (params.product_id) {
    conditions.push(`o.product_id = $${paramIndex++}`);
    values.push(params.product_id);
  }

  const whereClause = conditions.length > 0 ? `WHERE ${conditions.join(' AND ')}` : '';

  const countResult = await pool.query<{ count: string }>(
    `SELECT COUNT(*) FROM orders o ${whereClause}`,
    values
  );
  const total = parseInt(countResult.rows[0].count, 10);

  const dataResult = await pool.query<Order>(
    `${BASE_SELECT} ${whereClause} ORDER BY o.order_date DESC LIMIT $${paramIndex++} OFFSET $${paramIndex++}`,
    [...values, limit, offset]
  );

  return { orders: dataResult.rows, total };
}

export async function getOrderById(orderId: string): Promise<Order | null> {
  const result = await pool.query<Order>(
    `${BASE_SELECT} WHERE o.order_id = $1`,
    [orderId]
  );
  return result.rows[0] ?? null;
}
