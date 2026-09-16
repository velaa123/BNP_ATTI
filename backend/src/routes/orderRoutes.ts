// backend/src/routes/orderRoutes.ts
import { Router } from 'express';
import * as orderController from '../controllers/orderController';

const router = Router();

router.get('/', orderController.listOrders);
router.get('/:id', orderController.getOrder);

export default router;
