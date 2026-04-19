const CACHE_PREFIX = "guardian_cache_v1:";

export function readOfflineCache<T>(key: string): T | null {
  try {
    const raw = window.localStorage.getItem(`${CACHE_PREFIX}${key}`);
    if (!raw) {
      return null;
    }
    return JSON.parse(raw) as T;
  } catch {
    return null;
  }
}

export function writeOfflineCache<T>(key: string, value: T): void {
  try {
    window.localStorage.setItem(`${CACHE_PREFIX}${key}`, JSON.stringify(value));
  } catch {
    // Ignore storage failures on constrained devices.
  }
}

