// backend/src/app.ts
// Express app assembly: middleware, route mounting, error handling.
// Does NOT call .listen() — see server.ts for that.

import express, { Application } from 'express';
import cors from 'cors';
import { env } from './config/env';
import { errorHandler } from './middleware/errorHandler';
import customerRoutes from './routes/customerRoutes';
import productRoutes from './routes/productRoutes';
import orderRoutes from './routes/orderRoutes';
import churnRoutes from './routes/churnRoutes';
import dashboardRoutes from './routes/dashboardRoutes';
import salesRoutes from './routes/salesRoutes';
import demandRoutes from './routes/demandRoutes';
import inventoryRoutes from './routes/inventoryRoutes';

const app: Application = express();

app.use(cors({ origin: env.frontendUrl }));
app.use(express.json());

app.get('/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

app.use('/api/customers', customerRoutes);
app.use('/api/products', productRoutes);
app.use('/api/orders', orderRoutes);
app.use('/api/churn', churnRoutes);
app.use('/api/dashboard', dashboardRoutes);
app.use('/api/sales', salesRoutes);
app.use('/api/demand', demandRoutes);
app.use('/api/inventory', inventoryRoutes);

// Error handler must be registered LAST — after all routes,
// so it catches errors from anything above it.
app.use(errorHandler);

export default app;
