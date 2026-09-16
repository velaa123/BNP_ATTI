// backend/src/controllers/productController.ts
// HTTP handlers for product endpoints (raw product CRUD).

import { Request, Response, NextFunction } from 'express';
import * as productService from '../services/productService';

export async function listProducts(req: Request, res: Response, next: NextFunction): Promise<void> {
  try {
    const limit = req.query.limit ? parseInt(req.query.limit as string, 10) : undefined;
    const offset = req.query.offset ? parseInt(req.query.offset as string, 10) : undefined;
    const category = req.query.category as string | undefined;

    if (limit !== undefined && (isNaN(limit) || limit < 1 || limit > 500)) {
      res.status(400).json({ error: { code: 'INVALID_PARAM', message: 'limit must be a number between 1 and 500' } });
      return;
    }
    if (offset !== undefined && (isNaN(offset) || offset < 0)) {
      res.status(400).json({ error: { code: 'INVALID_PARAM', message: 'offset must be a non-negative number' } });
      return;
    }

    const { products, total } = await productService.getProducts({ limit, offset, category });

    res.json({
      data: products,
      pagination: { limit: limit ?? 50, offset: offset ?? 0, total },
    });
  } catch (err) {
    next(err);
  }
}

export async function getProduct(req: Request, res: Response, next: NextFunction): Promise<void> {
  try {
    const id = req.params.id as string;
    const product = await productService.getProductById(id);

    if (!product) {
      res.status(404).json({ error: { code: 'NOT_FOUND', message: `Product ${id} not found` } });
      return;
    }

    res.json({ data: product });
  } catch (err) {
    next(err);
  }
}
