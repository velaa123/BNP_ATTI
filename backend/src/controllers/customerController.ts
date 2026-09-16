// backend/src/controllers/customerController.ts
// HTTP handlers for customer endpoints. Parses/validates request input,
// delegates to customerService, and shapes the HTTP response.
// No SQL, no business logic — that lives in the service layer.

import { Request, Response, NextFunction } from 'express';
import * as customerService from '../services/customerService';
import * as mlService from '../services/mlService';
import { SubscriptionStatus } from '../models/customerModel';

const VALID_STATUSES: SubscriptionStatus[] = ['active', 'cancelled', 'paused'];

export async function listCustomers(req: Request, res: Response, next: NextFunction): Promise<void> {
  try {
    const limit = req.query.limit ? parseInt(req.query.limit as string, 10) : undefined;
    const offset = req.query.offset ? parseInt(req.query.offset as string, 10) : undefined;
    const country = req.query.country as string | undefined;
    const subscriptionStatusRaw = req.query.subscription_status as string | undefined;

    if (limit !== undefined && (isNaN(limit) || limit < 1 || limit > 500)) {
      res.status(400).json({ error: { code: 'INVALID_PARAM', message: 'limit must be a number between 1 and 500' } });
      return;
    }
    if (offset !== undefined && (isNaN(offset) || offset < 0)) {
      res.status(400).json({ error: { code: 'INVALID_PARAM', message: 'offset must be a non-negative number' } });
      return;
    }
    if (subscriptionStatusRaw && !VALID_STATUSES.includes(subscriptionStatusRaw as SubscriptionStatus)) {
      res.status(400).json({
        error: { code: 'INVALID_PARAM', message: `subscription_status must be one of: ${VALID_STATUSES.join(', ')}` },
      });
      return;
    }

    const { customers, total } = await customerService.getCustomers({
      limit,
      offset,
      country,
      subscription_status: subscriptionStatusRaw as SubscriptionStatus | undefined,
    });

    res.json({
      data: customers,
      pagination: {
        limit: limit ?? 50,
        offset: offset ?? 0,
        total,
      },
    });
  } catch (err) {
    next(err);
  }
}

export async function getCustomer(req: Request, res: Response, next: NextFunction): Promise<void> {
  try {
    const id = req.params.id as string;
    const customer = await customerService.getCustomerById(id);

    if (!customer) {
      res.status(404).json({ error: { code: 'NOT_FOUND', message: `Customer ${id} not found` } });
      return;
    }

    res.json({ data: customer });
  } catch (err) {
    next(err);
  }
}

export async function getHighRiskCustomers(req: Request, res: Response, next: NextFunction): Promise<void> {
  try {
    const limit = req.query.limit ? parseInt(req.query.limit as string, 10) : 10;

    if (isNaN(limit) || limit < 1 || limit > 100) {
      res.status(400).json({ error: { code: 'INVALID_PARAM', message: 'limit must be a number between 1 and 100' } });
      return;
    }

    const customers = await mlService.getHighRiskCustomersForFrontend(limit);
    res.json({ data: customers });
  } catch (err) {
    next(err);
  }
}
