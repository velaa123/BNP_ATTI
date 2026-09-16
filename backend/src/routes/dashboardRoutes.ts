// backend/src/routes/dashboardRoutes.ts
import { Router } from 'express';
import * as dashboardController from '../controllers/dashboardController';

const router = Router();

router.get('/summary', dashboardController.getSummary);

export default router;
