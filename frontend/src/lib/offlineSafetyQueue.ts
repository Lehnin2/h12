import type { OfflineSafetyQueueItem, SafetyCheckInPayload, SafetySosPayload } from "../types";

const STORAGE_KEY = "guardian_offline_safety_queue";

function makeId(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return `safety-${Date.now()}-${Math.round(Math.random() * 1_000_000)}`;
}

export function loadOfflineSafetyQueue(): OfflineSafetyQueueItem[] {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      return [];
    }
    const parsed = JSON.parse(raw) as OfflineSafetyQueueItem[];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

export function saveOfflineSafetyQueue(items: OfflineSafetyQueueItem[]): void {
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(items));
  } catch {
    // Ignore storage pressure on constrained devices.
  }
}

export function queueOfflineCheckIn(payload: SafetyCheckInPayload): OfflineSafetyQueueItem {
  const item: OfflineSafetyQueueItem = {
    id: makeId(),
    kind: "check-in",
    created_at: new Date().toISOString(),
    payload,
  };
  const next = [...loadOfflineSafetyQueue(), item];
  saveOfflineSafetyQueue(next);
  return item;
}

export function queueOfflineSos(payload: SafetySosPayload): OfflineSafetyQueueItem {
  const item: OfflineSafetyQueueItem = {
    id: makeId(),
    kind: "sos",
    created_at: new Date().toISOString(),
    payload,
  };
  const next = [...loadOfflineSafetyQueue(), item];
  saveOfflineSafetyQueue(next);
  return item;
}

