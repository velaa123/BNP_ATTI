// backend/src/routes/salesRoutes.ts
import { Router } from 'express';
import * as salesController from '../controllers/salesController';

const router = Router();

router.get('/forecast', salesController.getSalesForecast);
router.get('/', salesController.getSalesHistory);

export default router;
