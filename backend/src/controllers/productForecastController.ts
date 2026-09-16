// backend/src/controllers/productForecastController.ts
// Separate from productController (raw CRUD) — this handles the
// /api/products/forecast endpoint specifically.

import { Request, Response, NextFunction } from 'express';
import * as mlService from '../services/mlService';

export async function getProductForecast(req: Request, res: Response, next: NextFunction): Promise<void> {
  try {
    const limit = req.query.limit ? parseInt(req.query.limit as string, 10) : 10;
    if (isNaN(limit) || limit < 1 || limit > 100) {
      res.status(400).json({ error: { code: 'INVALID_PARAM', message: 'limit must be a number between 1 and 100' } });
      return;
    }
    const forecast = await mlService.getProductForecastForFrontend(limit);
    res.json({ data: forecast });
  } catch (err) {
    next(err);
  }
}
