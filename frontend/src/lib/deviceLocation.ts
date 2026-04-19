import type { DeviceLocationSnapshot } from "../types";

const STORAGE_KEY = "guardian_last_device_location";

export function loadCachedDeviceLocation(): DeviceLocationSnapshot | null {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      return null;
    }
    const parsed = JSON.parse(raw) as DeviceLocationSnapshot | null;
    if (!parsed || typeof parsed.lat !== "number" || typeof parsed.lon !== "number") {
      return null;
    }
    return { ...parsed, source: "cached" };
  } catch {
    return null;
  }
}

export function saveDeviceLocation(snapshot: DeviceLocationSnapshot): void {
  try {
    window.localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({
        ...snapshot,
        source: "cached",
      }),
    );
  } catch {
    // Ignore storage pressure on constrained devices.
  }
}

export function normalizeGeolocationPosition(
  position: GeolocationPosition,
): DeviceLocationSnapshot {
  return {
    lat: position.coords.latitude,
    lon: position.coords.longitude,
    accuracy_m: Number.isFinite(position.coords.accuracy) ? position.coords.accuracy : null,
    heading_deg: position.coords.heading == null || Number.isNaN(position.coords.heading)
      ? null
      : position.coords.heading,
    speed_kmh: position.coords.speed == null || Number.isNaN(position.coords.speed)
      ? null
      : Math.max(0, position.coords.speed * 3.6),
    captured_at: new Date(position.timestamp).toISOString(),
    source: "live",
  };
}

export function locationAgeMinutes(snapshot: DeviceLocationSnapshot | null): number | null {
  if (!snapshot) {
    return null;
  }
  return Math.max(
    0,
    Math.round((Date.now() - new Date(snapshot.captured_at).getTime()) / 60000),
  );
}

export function formatLocationLabel(snapshot: DeviceLocationSnapshot | null): string {
  if (!snapshot) {
    return "Location unavailable";
  }
  return `${snapshot.lat.toFixed(4)}, ${snapshot.lon.toFixed(4)}`;
}
