// backend/src/controllers/churnController.ts
import { Request, Response, NextFunction } from 'express';
import * as mlService from '../services/mlService';

export async function listChurnPredictions(req: Request, res: Response, next: NextFunction): Promise<void> {
  try {
    const predictions = await mlService.getChurnPredictions();
    res.json({ data: predictions, count: predictions.length });
  } catch (err) {
    next(err);
  }
}

export async function getTopRiskCustomers(req: Request, res: Response, next: NextFunction): Promise<void> {
  try {
    const limit = req.query.limit ? parseInt(req.query.limit as string, 10) : 10;

    if (isNaN(limit) || limit < 1 || limit > 100) {
      res.status(400).json({ error: { code: 'INVALID_PARAM', message: 'limit must be a number between 1 and 100' } });
      return;
    }

    const topRisk = await mlService.getTopRiskCustomers(limit);
    res.json({ data: topRisk });
  } catch (err) {
    next(err);
  }
}

export async function listCustomerSegments(req: Request, res: Response, next: NextFunction): Promise<void> {
  try {
    const segments = await mlService.getCustomerSegments();
    res.json({ data: segments, count: segments.length });
  } catch (err) {
    next(err);
  }
}
