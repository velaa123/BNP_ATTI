// backend/src/routes/churnRoutes.ts
import { Router } from 'express';
import * as churnController from '../controllers/churnController';

const router = Router();

router.get('/predictions', churnController.listChurnPredictions);
router.get('/top-risk', churnController.getTopRiskCustomers);
router.get('/segments', churnController.listCustomerSegments);

export default router;
