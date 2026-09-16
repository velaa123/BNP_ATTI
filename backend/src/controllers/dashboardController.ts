// backend/src/controllers/dashboardController.ts
import { Request, Response, NextFunction } from 'express';
import * as dashboardService from '../services/dashboardService';

export async function getSummary(req: Request, res: Response, next: NextFunction): Promise<void> {
  try {
    const summary = await dashboardService.getDashboardSummary();
    res.json({ data: summary });
  } catch (err) {
    next(err);
  }
}
