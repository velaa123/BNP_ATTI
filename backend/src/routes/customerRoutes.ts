// backend/src/routes/customerRoutes.ts
// Maps HTTP routes to customerController handlers.
// /high-risk MUST come before /:id, or Express matches "high-risk" as an ID.

import { Router } from 'express';
import * as customerController from '../controllers/customerController';

const router = Router();

router.get('/high-risk', customerController.getHighRiskCustomers);
router.get('/', customerController.listCustomers);
router.get('/:id', customerController.getCustomer);

export default router;
