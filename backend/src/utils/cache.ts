// backend/src/utils/cache.ts
// Simple in-memory TTL cache. Not distributed, not persistent — resets on
// server restart. That's fine here: this data only changes when someone
// edits the database or replaces a CSV file, neither of which happens
// mid-demo, and Redis would be overkill for this scale.

interface CacheEntry<T> {
  value: T;
  expiresAt: number;
}

const store = new Map<string, CacheEntry<unknown>>();

export async function withCache<T>(
  key: string,
  ttlMs: number,
  compute: () => Promise<T>
): Promise<T> {
  const existing = store.get(key);
  const now = Date.now();

  if (existing && existing.expiresAt > now) {
    return existing.value as T;
  }

  const value = await compute();
  store.set(key, { value, expiresAt: now + ttlMs });
  return value;
}

// Call this if underlying data changes and you want fresh results
// immediately, rather than waiting for TTL expiry (not currently wired
// into any endpoint, but here for when a "refresh data" feature exists).
export function clearCache(key?: string): void {
  if (key) {
    store.delete(key);
  } else {
    store.clear();
  }
}