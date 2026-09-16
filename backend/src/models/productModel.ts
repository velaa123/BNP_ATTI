// backend/src/models/productModel.ts
// TypeScript shape of a row in the `products` table.
// Keep in sync with database/schema.sql.

export interface Product {
  product_id: string;
  product_name: string;
  category: string;
  unit_price: number;
}

export interface ProductListParams {
  limit?: number;
  offset?: number;
  category?: string;
}
