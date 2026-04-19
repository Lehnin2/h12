import {
  fallbackHeatmap,
  fallbackLunar,
  fallbackMission,
  fallbackRecommendation,
  fallbackRoute,
  fallbackSafety,
} from "../data/fallback";
import { readOfflineCache, writeOfflineCache } from "./offlineCache";
import type {
  AdminOverviewResponse,
  AuthResponse,
  CommunityReportCreatePayload,
  CommunityReportFeedResponse,
  ChatMessageRequest,
  ChatMessageResponse,
  FishermanProfilePublic,
  HeatmapResponse,
  LoginPayload,
  LunarResponse,
  MissionBriefingResponse,
  MissionHistoryResponse,
  RegisterPayload,
  RecommendationResponse,
  RouteResponse,
  SafetyCheckInPayload,
  SafetyEventListResponse,
  SafetyEventResponse,
  SafetySosPayload,
  SafetyStatusResponse,
} from "../types";

import { API_BASE } from "./config";

async function requestJson<T>(path: string, fallback: T, cacheKey?: string): Promise<T> {
  try {
    const response = await fetch(`${API_BASE}${path}`);
    if (!response.ok) {
      return cacheKey ? readOfflineCache<T>(cacheKey) ?? fallback : fallback;
    }
    const payload = (await response.json()) as T;
    if (cacheKey) {
      writeOfflineCache(cacheKey, payload);
    }
    return payload;
  } catch {
    return cacheKey ? readOfflineCache<T>(cacheKey) ?? fallback : fallback;
  }
}

async function requestJsonWithOptions<T>(
  path: string,
  options: RequestInit,
  fallback?: T,
  cacheKey?: string,
): Promise<T> {
  try {
    const response = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...(options.headers ?? {}),
      },
    });
    if (!response.ok) {
      if (cacheKey) {
        const cached = readOfflineCache<T>(cacheKey);
        if (cached !== null) {
          return cached;
        }
      }
      if (fallback !== undefined) {
        return fallback;
      }
      throw new Error(`Request failed with status ${response.status}`);
    }
    const payload = (await response.json()) as T;
    if (cacheKey) {
      writeOfflineCache(cacheKey, payload);
    }
    return payload;
  } catch (error) {
    if (cacheKey) {
      const cached = readOfflineCache<T>(cacheKey);
      if (cached !== null) {
        return cached;
      }
    }
    if (fallback !== undefined) {
      return fallback;
    }
    throw error;
  }
}

export function fetchHeatmap(port: string, species: string): Promise<HeatmapResponse> {
  return requestJson(
    `/zones/heatmap?departure_port=${encodeURIComponent(port)}&species=${encodeURIComponent(species)}`,
    fallbackHeatmap,
    `heatmap:${port}:${species}`,
  );
}

export function fetchRecommendation(
  port: string,
  species: string,
): Promise<RecommendationResponse> {
  return requestJson(
    `/zones/recommend?departure_port=${encodeURIComponent(port)}&species=${encodeURIComponent(species)}`,
    fallbackRecommendation,
    `recommendation:${port}:${species}`,
  );
}

export function fetchRoute(port: string, targetZoneId: string): Promise<RouteResponse> {
  return requestJson(
    `/route/optimize?departure_port=${encodeURIComponent(port)}&target_zone_id=${encodeURIComponent(targetZoneId)}`,
    fallbackRoute,
    `route:${port}:${targetZoneId}`,
  );
}

export function fetchLunar(species: string): Promise<LunarResponse> {
  return requestJson(`/lunar/today?species=${encodeURIComponent(species)}`, fallbackLunar, `lunar:${species}`);
}

export function fetchSafety(port: string): Promise<SafetyStatusResponse> {
  return requestJson(
    `/safety/status?departure_port=${encodeURIComponent(port)}`,
    fallbackSafety,
    `safety:${port}`,
  );
}

export function fetchMissionBriefing(
  port: string,
  species: string,
): Promise<MissionBriefingResponse> {
  return requestJson(
    `/mission/briefing?departure_port=${encodeURIComponent(port)}&species=${encodeURIComponent(species)}`,
    fallbackMission,
    `mission:${port}:${species}`,
  );
}

export function fetchPersonalizedMission(token: string): Promise<MissionBriefingResponse> {
  return requestJsonWithOptions<MissionBriefingResponse>(
    "/mission/briefing/me",
    {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    },
    undefined,
    "mission:me",
  );
}

export function fetchMissionHistory(token: string): Promise<MissionHistoryResponse> {
  return requestJsonWithOptions<MissionHistoryResponse>(
    "/mission/history/me",
    {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    },
    undefined,
    "mission_history:me",
  );
}

export function fetchRecentReports(): Promise<CommunityReportFeedResponse> {
  return requestJson(
    "/reports/recent?within_hours=72",
    {
      recent_reports: [],
      zone_summaries: [],
    },
    "reports:recent",
  );
}

export function fetchAdminOverview(token: string): Promise<AdminOverviewResponse> {
  return requestJsonWithOptions<AdminOverviewResponse>(
    "/admin/overview",
    {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    },
  );
}

export function registerUser(payload: RegisterPayload): Promise<AuthResponse> {
  return requestJsonWithOptions<AuthResponse>(
    "/auth/register",
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
  );
}

export function loginUser(payload: LoginPayload): Promise<AuthResponse> {
  return requestJsonWithOptions<AuthResponse>(
    "/auth/login",
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
  );
}

export function fetchCurrentUser(token: string): Promise<FishermanProfilePublic> {
  return requestJsonWithOptions<FishermanProfilePublic>(
    "/auth/me",
    {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    },
    undefined,
    "profile:me",
  );
}

export function updateProfile(
  token: string,
  payload: Omit<RegisterPayload, "email" | "password">,
): Promise<FishermanProfilePublic> {
  return requestJsonWithOptions<FishermanProfilePublic>(
    "/auth/profile",
    {
      method: "PUT",
      headers: {
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(payload),
    },
  );
}

export async function logoutUser(token: string): Promise<void> {
  await requestJsonWithOptions(
    "/auth/logout",
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    },
  );
}

export function fetchSafetyStatus(token: string): Promise<SafetyStatusResponse> {
  return requestJsonWithOptions<SafetyStatusResponse>(
    "/safety/status/me",
    {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    },
    undefined,
    "safety:me",
  );
}

export function fetchSafetyEvents(token: string): Promise<SafetyEventListResponse> {
  return requestJsonWithOptions<SafetyEventListResponse>(
    "/safety/events/me",
    {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    },
    undefined,
    "safety_events:me",
  );
}

export function sendSafetyCheckIn(
  token: string,
  payload: SafetyCheckInPayload,
): Promise<SafetyEventResponse> {
  return requestJsonWithOptions<SafetyEventResponse>(
    "/safety/check-in",
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(payload),
    },
  );
}

export function triggerSafetySos(
  token: string,
  payload: SafetySosPayload,
): Promise<SafetyEventResponse> {
  return requestJsonWithOptions<SafetyEventResponse>(
    "/safety/sos",
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(payload),
    },
  );
}

export function submitCommunityReport(
  token: string,
  payload: CommunityReportCreatePayload,
): Promise<{ status: string }> {
  return requestJsonWithOptions<{ status: string }>(
    "/reports/submit",
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(payload),
    },
  );
}

export function sendChatMessage(
  token: string,
  payload: ChatMessageRequest,
): Promise<ChatMessageResponse> {
  return requestJsonWithOptions<ChatMessageResponse>(
    "/chat/message",
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(payload),
    },
  );
}
