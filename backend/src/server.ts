// backend/src/server.ts
// Entry point. Verifies the database is reachable before starting
// the HTTP server — fails fast and loudly if Postgres isn't up.

import app from './app';
import { env } from './config/env';
import { testConnection } from './config/database';

async function start(): Promise<void> {
  try {
    await testConnection();

    app.listen(env.port, () => {
      console.log(`Backend server running on http://localhost:${env.port}`);
      console.log(`Environment: ${env.nodeEnv}`);
    });
  } catch (err) {
    console.error('Failed to start server — database connection could not be established.');
    process.exit(1);
  }
}

start();
