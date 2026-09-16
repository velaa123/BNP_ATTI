// backend/src/services/productService.ts
// All Postgres query logic for products.

import { pool } from '../config/database';
import { Product, ProductListParams } from '../models/productModel';

export async function getProducts(params: ProductListParams): Promise<{ products: Product[]; total: number }> {
  const limit = params.limit ?? 50;
  const offset = params.offset ?? 0;

  const conditions: string[] = [];
  const values: (string | number)[] = [];
  let paramIndex = 1;

  if (params.category) {
    conditions.push(`category = $${paramIndex++}`);
    values.push(params.category);
  }

  const whereClause = conditions.length > 0 ? `WHERE ${conditions.join(' AND ')}` : '';

  const countResult = await pool.query<{ count: string }>(
    `SELECT COUNT(*) FROM products ${whereClause}`,
    values
  );
  const total = parseInt(countResult.rows[0].count, 10);

  const dataResult = await pool.query<Product>(
    `SELECT * FROM products ${whereClause} ORDER BY product_id LIMIT $${paramIndex++} OFFSET $${paramIndex++}`,
    [...values, limit, offset]
  );

  return { products: dataResult.rows, total };
}

export async function getProductById(productId: string): Promise<Product | null> {
  const result = await pool.query<Product>(
    'SELECT * FROM products WHERE product_id = $1',
    [productId]
  );
  return result.rows[0] ?? null;
}
