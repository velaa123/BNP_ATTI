// backend/src/controllers/anomalyController.ts
import { Request, Response, NextFunction } from 'express';
import * as mlService from '../services/mlService';

export async function getAnomalyReport(req: Request, res: Response, next: NextFunction): Promise<void> {
  try {
    const report = await mlService.getAnomalyReport();
    res.json({ data: report });
  } catch (err) {
    next(err);
  }
}