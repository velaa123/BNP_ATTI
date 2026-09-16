// backend/src/routes/demandRoutes.ts
import { Router } from 'express';
import * as demandController from '../controllers/demandController';

const router = Router();

router.get('/forecast', demandController.getDemandForecast);

export default router;
