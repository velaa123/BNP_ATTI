// backend/src/routes/inventoryRoutes.ts
import { Router } from 'express';
import * as inventoryController from '../controllers/inventoryController';

const router = Router();

router.get('/', inventoryController.getInventory);

export default router;
