// backend/src/models/orderModel.ts
// TypeScript shape of an order row, joined with product and customer context.
// Keep in sync with database/schema.sql (orders, products, customers tables).

export interface Order {
  order_id: string;
  customer_id: string;
  product_id: string;
  quantity: number;
  order_date: string;      // plain date string, see database.ts type parser
  rating: number;
  product_name: string;    // joined from products
  category: string;        // joined from products
  unit_price: number;      // joined from products
  country: string;         // joined from customers
}

export interface OrderListParams {
  limit?: number;
  offset?: number;
  customer_id?: string;
  product_id?: string;
}
