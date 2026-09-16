// backend/src/controllers/salesController.ts
import { Request, Response, NextFunction } from 'express';
import * as mlService from '../services/mlService';

export async function getSalesHistory(req: Request, res: Response, next: NextFunction): Promise<void> {
  try {
    const history = await mlService.getSalesHistory();
    res.json({ data: history });
  } catch (err) {
    next(err);
  }
}

export async function getSalesForecast(req: Request, res: Response, next: NextFunction): Promise<void> {
  try {
    const forecast = await mlService.getSalesForecastForFrontend();
    res.json({ data: forecast });
  } catch (err) {
    next(err);
  }
}
