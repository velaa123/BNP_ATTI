// backend/src/config/database.ts
// PostgreSQL connection pool. Every service imports `pool` from here
// to run queries — no file should call `new Pool()` anywhere else.

import { Pool, types } from 'pg';
import { env } from './env';

// Postgres DATE columns (OID 1082) come back as JS Date objects by default,
// which get UTC-shifted on JSON serialization (res.json() calls toISOString()).
// Returning them as plain strings avoids that timezone bug entirely.
types.setTypeParser(1082, (val) => val);

// Postgres NUMERIC columns (OID 1700) come back as strings by default,
// to avoid floating-point precision loss. Parsing to float here is a
// deliberate tradeoff: fine for display/aggregation, NOT safe if you
// ever need exact decimal precision (e.g. real financial ledger math).
types.setTypeParser(1700, (val) => parseFloat(val));

export const pool = new Pool({
  connectionString: env.databaseUrl,
});

pool.on('error', (err) => {
  // Fires on idle client errors (e.g. DB connection dropped unexpectedly).
  // Logging here prevents an unhandled crash from a background connection issue.
  console.error('Unexpected error on idle PostgreSQL client:', err);
});

export async function testConnection(): Promise<void> {
  try {
    const result = await pool.query('SELECT NOW()');
    console.log('PostgreSQL connected:', result.rows[0].now);
  } catch (err) {
    console.error('PostgreSQL connection failed:', err);
    throw err;
  }
}
