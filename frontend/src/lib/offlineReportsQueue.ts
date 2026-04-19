import type { CommunityReportCreatePayload, OfflineCommunityReportQueueItem } from "../types";

const STORAGE_KEY = "guardian_offline_reports_queue";

function makeId(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return `report-${Date.now()}-${Math.round(Math.random() * 1_000_000)}`;
}

export function loadOfflineReportsQueue(): OfflineCommunityReportQueueItem[] {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      return [];
    }
    const parsed = JSON.parse(raw) as OfflineCommunityReportQueueItem[];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

export function saveOfflineReportsQueue(items: OfflineCommunityReportQueueItem[]): void {
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(items));
  } catch {
    // Ignore storage pressure.
  }
}

export function queueOfflineReport(payload: CommunityReportCreatePayload): OfflineCommunityReportQueueItem {
  const item: OfflineCommunityReportQueueItem = {
    id: makeId(),
    created_at: new Date().toISOString(),
    payload,
  };
  const next = [...loadOfflineReportsQueue(), item];
  saveOfflineReportsQueue(next);
  return item;
}

