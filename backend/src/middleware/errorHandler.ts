// backend/src/middleware/errorHandler.ts
// Centralized error handler. Every controller calls next(err) on failure;
// this is the single place that turns any error into a consistent response shape.

import { Request, Response, NextFunction } from 'express';

export function errorHandler(
  err: Error,
  req: Request,
  res: Response,
  next: NextFunction
): void {
  console.error(`[${req.method} ${req.path}] Error:`, err.message);

  res.status(500).json({
    error: {
      code: 'INTERNAL_ERROR',
      message: 'An unexpected error occurred. Please try again.',
    },
  });
}
