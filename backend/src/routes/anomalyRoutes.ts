// backend/src/routes/anomalyRoutes.ts
import { Router } from 'express';
import * as anomalyController from '../controllers/anomalyController';

const router = Router();

router.get('/', anomalyController.getAnomalyReport);

export default router;