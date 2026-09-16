// backend/src/controllers/orderController.ts
// HTTP handlers for order endpoints.

import { Request, Response, NextFunction } from 'express';
import * as orderService from '../services/orderService';

export async function listOrders(req: Request, res: Response, next: NextFunction): Promise<void> {
  try {
    const limit = req.query.limit ? parseInt(req.query.limit as string, 10) : undefined;
    const offset = req.query.offset ? parseInt(req.query.offset as string, 10) : undefined;
    const customerId = req.query.customer_id as string | undefined;
    const productId = req.query.product_id as string | undefined;

    if (limit !== undefined && (isNaN(limit) || limit < 1 || limit > 500)) {
      res.status(400).json({ error: { code: 'INVALID_PARAM', message: 'limit must be a number between 1 and 500' } });
      return;
    }
    if (offset !== undefined && (isNaN(offset) || offset < 0)) {
      res.status(400).json({ error: { code: 'INVALID_PARAM', message: 'offset must be a non-negative number' } });
      return;
    }

    const { orders, total } = await orderService.getOrders({
      limit,
      offset,
      customer_id: customerId,
      product_id: productId,
    });

    res.json({
      data: orders,
      pagination: { limit: limit ?? 50, offset: offset ?? 0, total },
    });
  } catch (err) {
    next(err);
  }
}

export async function getOrder(req: Request, res: Response, next: NextFunction): Promise<void> {
  try {
    const id = req.params.id as string;
    const order = await orderService.getOrderById(id);

    if (!order) {
      res.status(404).json({ error: { code: 'NOT_FOUND', message: `Order ${id} not found` } });
      return;
    }

    res.json({ data: order });
  } catch (err) {
    next(err);
  }
}
