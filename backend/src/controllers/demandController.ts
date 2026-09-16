// backend/src/controllers/demandController.ts
import { Request, Response, NextFunction } from 'express';
import * as mlService from '../services/mlService';

export async function getDemandForecast(req: Request, res: Response, next: NextFunction): Promise<void> {
  try {
    const forecast = await mlService.getDemandForecastForFrontend();
    res.json({ data: forecast });
  } catch (err) {
    next(err);
  }
}
