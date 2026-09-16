// backend/src/controllers/inventoryController.ts
import { Request, Response, NextFunction } from 'express';
import * as mlService from '../services/mlService';

export async function getInventory(req: Request, res: Response, next: NextFunction): Promise<void> {
  try {
    const inventory = await mlService.getInventoryForFrontend();
    res.json({ data: inventory });
  } catch (err) {
    next(err);
  }
}
