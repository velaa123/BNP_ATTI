// backend/src/config/env.ts
// Loads and validates environment variables. Fails fast and loudly
// if something required is missing, rather than letting `undefined`
// silently propagate into database connections or API calls.

import dotenv from 'dotenv';
import path from 'path';

dotenv.config({ path: path.resolve(__dirname, '../../.env') });

interface EnvConfig {
  port: number;
  databaseUrl: string;
  mlApiUrl: string;
  frontendUrl: string;
  nodeEnv: 'development' | 'production' | 'test';
}

function requireEnv(key: string): string {
  const value = process.env[key];
  if (!value || value.trim() === '') {
    throw new Error(
      `Missing required environment variable: ${key}. ` +
      `Check that backend/.env exists and contains ${key}=...`
    );
  }
  return value;
}

function parseNodeEnv(value: string | undefined): EnvConfig['nodeEnv'] {
  if (value === 'production' || value === 'test') return value;
  return 'development';
}

export const env: EnvConfig = {
  port: parseInt(requireEnv('PORT'), 10),
  databaseUrl: requireEnv('DATABASE_URL'),
  mlApiUrl: requireEnv('ML_API_URL'),
  frontendUrl: requireEnv('FRONTEND_URL'),
  nodeEnv: parseNodeEnv(process.env.NODE_ENV),
};

if (isNaN(env.port)) {
  throw new Error(`PORT must be a valid number, got: ${process.env.PORT}`);
}
