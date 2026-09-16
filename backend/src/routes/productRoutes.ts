// backend/src/routes/productRoutes.ts
// /forecast MUST come before /:id, or Express matches "forecast" as an ID.

import { Router } from 'express';
import * as productController from '../controllers/productController';
import * as productForecastController from '../controllers/productForecastController';

const router = Router();

router.get('/forecast', productForecastController.getProductForecast);
router.get('/', productController.listProducts);
router.get('/:id', productController.getProduct);

export default router;
