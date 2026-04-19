import { createContext, useContext, useEffect, useState, type ReactNode } from "react";

import {
  fetchAdminOverview,
  fetchCurrentUser,
  fetchMissionBriefing,
  fetchMissionHistory,
  fetchPersonalizedMission,
  fetchRecentReports,
  fetchSafetyEvents,
  fetchSafetyStatus,
  loginUser,
  logoutUser,
  registerUser,
  submitCommunityReport,
  sendSafetyCheckIn,
  triggerSafetySos,
  updateProfile,
} from "../lib/api";
import { clearAuthToken, loadAuthToken, saveAuthToken } from "../lib/authStorage";
import {
  loadOfflineReportsQueue,
  queueOfflineReport,
  saveOfflineReportsQueue,
} from "../lib/offlineReportsQueue";
import {
  loadOfflineSafetyQueue,
  queueOfflineCheckIn,
  queueOfflineSos,
  saveOfflineSafetyQueue,
} from "../lib/offlineSafetyQueue";
import {
  loadCachedDeviceLocation,
  locationAgeMinutes,
  normalizeGeolocationPosition,
  saveDeviceLocation,
} from "../lib/deviceLocation";
import type { UiLanguage } from "../lib/uiCopy";
import type {
  AdminOverviewResponse,
  AuthResponse,
  CommunityReportFeedResponse,
  DeviceLocationSnapshot,
  FishermanProfilePublic,
  HeatmapResponse,
  LoginPayload,
  LunarResponse,
  MissionBriefingResponse,
  MissionHistoryEntry,
  OfflineCommunityReportQueueItem,
  OfflineSafetyQueueItem,
  RecommendationResponse,
  RegisterPayload,
  RouteResponse,
  SafetyEventResponse,
  SafetyStatusResponse,
} from "../types";

/* ── Species & port option lists ────────────────────────────────── */

export const speciesOptions = [
  { value: "poulpe", label: "Poulpe" },
  { value: "crevette_royale", label: "Crevette royale" },
  { value: "rouget", label: "Rouget" },
  { value: "sardine", label: "Sardine" },
];

export const portOptions = [
  { value: "zarrat", label: "Zarrat" },
  { value: "ghannouch", label: "Ghannouch" },
  { value: "teboulbou", label: "Teboulbou" },
  { value: "oued_akarit", label: "Oued Akarit" },
  { value: "mareth", label: "Mareth" },
];

/* ── Helper ─────────────────────────────────────────────────────── */

export function toneFromStatus(status: string | undefined) {
  if (status === "GO" || status === "LOW" || status === "OPEN") return "good" as const;
  if (status === "CAUTION" || status === "MEDIUM" || status === "RESTRICTED") return "warn" as const;
  if (status === "NO_GO" || status === "HIGH" || status === "PROHIBITED") return "danger" as const;
  return "neutral" as const;
}

/* ── Context shape ──────────────────────────────────────────────── */

interface AppContextValue {
  /* Auth */
  token: string | null;
  profile: FishermanProfilePublic | null;
  sessionLoading: boolean;
  handleLogin: (payload: LoginPayload) => Promise<void>;
  handleRegister: (payload: RegisterPayload) => Promise<void>;
  handleLogout: () => Promise<void>;
  handleProfileSave: (payload: Omit<FishermanProfilePublic, "id" | "email" | "is_admin">) => Promise<void>;

  /* Connection & GPS */
  isOnline: boolean;
  deviceLocation: DeviceLocationSnapshot | null;
  locationError: string | null;
  locationAge: number | null;

  /* Guest selectors */
  port: string;
  setPort: (value: string) => void;
  species: string;
  setSpecies: (value: string) => void;

  /* Mission data */
  loading: boolean;
  mission: MissionBriefingResponse | null;
  heatmap: HeatmapResponse | null;
  recommendation: RecommendationResponse | null;
  route: RouteResponse | null;
  lunar: LunarResponse | null;
  safety: SafetyStatusResponse | null;
  missionHistory: MissionHistoryEntry[];
  safetyEvents: SafetyEventResponse[];
  adminOverview: AdminOverviewResponse | null;
  adminLoading: boolean;

  /* Safety actions */
  safetyBusy: boolean;
  safetyMessage: string | null;
  pendingSafetyQueue: OfflineSafetyQueueItem[];
  queueSyncBusy: boolean;
  handleSafetyAction: (kind: "check-in" | "sos") => Promise<void>;

  /* Community reports */
  reportsFeed: CommunityReportFeedResponse;
  reportsBusy: boolean;
  reportMessage: string | null;
  pendingReportsQueue: OfflineCommunityReportQueueItem[];
  reportsQueueSyncBusy: boolean;
  handleQuickReport: (type: "catch" | "pollution" | "hazard" | "illegal_activity" | "current") => Promise<void>;
  uiLanguage: UiLanguage;
  setUiLanguage: (value: UiLanguage) => void;
}

const AppContext = createContext<AppContextValue | null>(null);

export function useAppContext() {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error("useAppContext must be used within AppProvider");
  return ctx;
}

/* ── Provider ───────────────────────────────────────────────────── */

export function AppProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(() => loadAuthToken());
  const [uiLanguage, setUiLanguageState] = useState<UiLanguage>(() => {
    const stored = window.localStorage.getItem("guardian-ui-language");
    return stored === "en" ? "en" : "fr";
  });
  const [profile, setProfile] = useState<FishermanProfilePublic | null>(null);
  const [isOnline, setIsOnline] = useState(() => window.navigator.onLine);
  const [port, setPort] = useState("zarrat");
  const [species, setSpecies] = useState("poulpe");
  const [heatmap, setHeatmap] = useState<HeatmapResponse | null>(null);
  const [recommendation, setRecommendation] = useState<RecommendationResponse | null>(null);
  const [route, setRoute] = useState<RouteResponse | null>(null);
  const [lunar, setLunar] = useState<LunarResponse | null>(null);
  const [safety, setSafety] = useState<SafetyStatusResponse | null>(null);
  const [mission, setMission] = useState<MissionBriefingResponse | null>(null);
  const [missionHistory, setMissionHistory] = useState<MissionHistoryEntry[]>([]);
  const [safetyEvents, setSafetyEvents] = useState<SafetyEventResponse[]>([]);
  const [adminOverview, setAdminOverview] = useState<AdminOverviewResponse | null>(null);
  const [adminLoading, setAdminLoading] = useState(false);
  const [safetyMessage, setSafetyMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [sessionLoading, setSessionLoading] = useState(true);
  const [safetyBusy, setSafetyBusy] = useState(false);
  const [pendingSafetyQueue, setPendingSafetyQueue] = useState<OfflineSafetyQueueItem[]>(() => loadOfflineSafetyQueue());
  const [queueSyncBusy, setQueueSyncBusy] = useState(false);
  const [reportsFeed, setReportsFeed] = useState<CommunityReportFeedResponse>({ recent_reports: [], zone_summaries: [] });
  const [pendingReportsQueue, setPendingReportsQueue] = useState<OfflineCommunityReportQueueItem[]>(() => loadOfflineReportsQueue());
  const [reportsBusy, setReportsBusy] = useState(false);
  const [reportMessage, setReportMessage] = useState<string | null>(null);
  const [reportsQueueSyncBusy, setReportsQueueSyncBusy] = useState(false);
  const [deviceLocation, setDeviceLocation] = useState<DeviceLocationSnapshot | null>(() => loadCachedDeviceLocation());
  const [locationError, setLocationError] = useState<string | null>(null);

  const locationAge = locationAgeMinutes(deviceLocation);
  const bestZone = recommendation?.best_zone;

  useEffect(() => {
    window.localStorage.setItem("guardian-ui-language", uiLanguage);
  }, [uiLanguage]);

  /* ── Online / Offline ── */
  useEffect(() => {
    const on = () => setIsOnline(true);
    const off = () => setIsOnline(false);
    window.addEventListener("online", on);
    window.addEventListener("offline", off);
    return () => { window.removeEventListener("online", on); window.removeEventListener("offline", off); };
  }, []);

  /* ── GPS ── */
  useEffect(() => {
    if (!("geolocation" in navigator)) { setLocationError("GPS not available on this device."); return; }
    const watchId = navigator.geolocation.watchPosition(
      (pos) => { const s = normalizeGeolocationPosition(pos); setDeviceLocation(s); saveDeviceLocation(s); setLocationError(null); },
      (err) => { setLocationError(err.code === err.PERMISSION_DENIED ? "Location permission denied. Using last known fix when available." : "Live GPS fix unavailable. Using last known position when available."); },
      { enableHighAccuracy: true, maximumAge: 30000, timeout: 15000 },
    );
    return () => { navigator.geolocation.clearWatch(watchId); };
  }, []);

  /* ── Session hydration ── */
  useEffect(() => {
    let mounted = true;
    async function hydrate() {
      if (!token) { setSessionLoading(false); return; }
      try { const u = await fetchCurrentUser(token); if (mounted) setProfile(u); }
      catch { clearAuthToken(); if (mounted) { setToken(null); setProfile(null); } }
      finally { if (mounted) setSessionLoading(false); }
    }
    void hydrate();
    return () => { mounted = false; };
  }, [token]);

  /* ── Operator context (history, events, reports) ── */
  useEffect(() => {
    let mounted = true;
    async function load() {
      if (!token || !profile) { if (mounted) { setMissionHistory([]); setSafetyEvents([]); setReportsFeed({ recent_reports: [], zone_summaries: [] }); } return; }
      try {
        const [h, e, s, r] = await Promise.all([fetchMissionHistory(token), fetchSafetyEvents(token), fetchSafetyStatus(token), fetchRecentReports()]);
        if (!mounted) return;
        setMissionHistory(h.entries); setSafetyEvents(e.events); setSafety(s); setReportsFeed(r);
      }
      catch { if (mounted) { setMissionHistory([]); setSafetyEvents([]); setReportsFeed({ recent_reports: [], zone_summaries: [] }); } }
    }
    void load();
    return () => { mounted = false; };
  }, [token, profile]);

  useEffect(() => {
    let mounted = true;
    async function loadAdminOverview() {
      if (!token || !profile?.is_admin) {
        if (mounted) {
          setAdminOverview(null);
          setAdminLoading(false);
        }
        return;
      }
      setAdminLoading(true);
      try {
        const overview = await fetchAdminOverview(token);
        if (mounted) {
          setAdminOverview(overview);
        }
      } catch {
        if (mounted) {
          setAdminOverview(null);
        }
      } finally {
        if (mounted) {
          setAdminLoading(false);
        }
      }
    }
    void loadAdminOverview();
    return () => {
      mounted = false;
    };
  }, [token, profile?.is_admin, missionHistory.length, reportsFeed.recent_reports.length, safetyEvents.length]);

  /* ── Mission loading ── */
  useEffect(() => {
    let mounted = true;
    async function loadMission() {
      if (sessionLoading) return;
      setLoading(true);
      try {
        const briefing = token && profile ? await fetchPersonalizedMission(token) : await fetchMissionBriefing(port, species);
        if (!mounted) return;
        setMission(briefing); setHeatmap(briefing.heatmap); setRecommendation(briefing.recommendation);
        setRoute(briefing.route); setLunar(briefing.lunar); setSafety(briefing.safety);
      } catch {
        const fp = profile?.home_port ?? port;
        const fs = profile?.target_species[0] ?? species;
        const fb = await fetchMissionBriefing(fp, fs);
        if (!mounted) return;
        setMission(fb); setHeatmap(fb.heatmap); setRecommendation(fb.recommendation);
        setRoute(fb.route); setLunar(fb.lunar); setSafety(fb.safety);
      } finally { if (mounted) setLoading(false); }
    }
    void loadMission();
    return () => { mounted = false; };
  }, [port, species, token, profile, sessionLoading]);

  /* ── Flush offline safety queue ── */
  useEffect(() => {
    let cancelled = false;
    async function flush() {
      if (!token || !isOnline || pendingSafetyQueue.length === 0 || queueSyncBusy) return;
      setQueueSyncBusy(true);
      try {
        const remaining: OfflineSafetyQueueItem[] = [];
        const synced: SafetyEventResponse[] = [];
        for (const item of pendingSafetyQueue) {
          if (cancelled) return;
          try { const ev = item.kind === "check-in" ? await sendSafetyCheckIn(token, item.payload) : await triggerSafetySos(token, item.payload); synced.push(ev); }
          catch { remaining.push(item); }
        }
        if (cancelled) return;
        saveOfflineSafetyQueue(remaining); setPendingSafetyQueue(remaining);
        if (synced.length > 0) {
          setSafetyEvents(cur => [...synced.reverse(), ...cur].slice(0, 12));
          const rs = await fetchSafetyStatus(token);
          if (!cancelled) { setSafety(rs); setSafetyMessage(remaining.length === 0 ? "Offline safety events synced successfully." : `${synced.length} safety event(s) synced. ${remaining.length} still pending.`); }
        }
      } finally { if (!cancelled) setQueueSyncBusy(false); }
    }
    void flush();
    return () => { cancelled = true; };
  }, [token, isOnline, pendingSafetyQueue.length, queueSyncBusy]);

  /* ── Flush offline reports queue ── */
  useEffect(() => {
    let cancelled = false;
    async function flush() {
      if (!token || !isOnline || pendingReportsQueue.length === 0 || reportsQueueSyncBusy) return;
      setReportsQueueSyncBusy(true);
      try {
        const remaining: OfflineCommunityReportQueueItem[] = [];
        let cnt = 0;
        for (const item of pendingReportsQueue) {
          if (cancelled) return;
          try { await submitCommunityReport(token, item.payload); cnt++; }
          catch { remaining.push(item); }
        }
        if (cancelled) return;
        saveOfflineReportsQueue(remaining); setPendingReportsQueue(remaining);
        if (cnt > 0) {
          const fresh = await fetchRecentReports();
          if (!cancelled) { setReportsFeed(fresh); setReportMessage(remaining.length === 0 ? "Offline community reports synced successfully." : `${cnt} report(s) synced. ${remaining.length} still pending.`); }
        }
      } finally { if (!cancelled) setReportsQueueSyncBusy(false); }
    }
    void flush();
    return () => { cancelled = true; };
  }, [token, isOnline, pendingReportsQueue.length, reportsQueueSyncBusy]);

  /* ── Action handlers ── */

  async function handleAuthResult(action: Promise<AuthResponse>) {
    const r = await action;
    saveAuthToken(r.access_token); setToken(r.access_token); setProfile(r.profile);
  }

  async function handleProfileSave(payload: Omit<FishermanProfilePublic, "id" | "email" | "is_admin">) {
    if (!token) return;
    const updated = await updateProfile(token, payload);
    setProfile(updated);
  }

  async function handleLogout() {
    if (token) await logoutUser(token);
    clearAuthToken(); setToken(null); setProfile(null);
  }

  async function handleSafetyAction(kind: "check-in" | "sos") {
    if (!token || !profile) return;
    const loc = deviceLocation;
    const lat = loc?.lat ?? bestZone?.center_lat ?? 33.679;
    const lon = loc?.lon ?? bestZone?.center_lon ?? 10.495;
    const checkInPayload = { lat, lon, note: `Mission check-in near ${bestZone?.label ?? "recommended zone"}`, sync_mode: loc?.source === "live" ? "gps_live" : loc?.source === "cached" ? "gps_cached" : "zone_fallback", battery_level_pct: 78 };
    const sosPayload = { lat, lon, message: `Emergency signal from ${profile.boat_name} near ${bestZone?.label ?? "mission corridor"}` };

    if (!isOnline) {
      const q = kind === "check-in" ? queueOfflineCheckIn(checkInPayload) : queueOfflineSos(sosPayload);
      setPendingSafetyQueue(c => [...c, q]);
      setSafetyMessage(kind === "check-in" ? "No network. Check-in saved locally and will sync when the signal returns." : "No network. SOS saved locally and will sync when the signal returns.");
      return;
    }
    setSafetyBusy(true); setSafetyMessage(null);
    try {
      const ev = kind === "check-in" ? await sendSafetyCheckIn(token, checkInPayload) : await triggerSafetySos(token, sosPayload);
      setSafetyEvents(c => [ev, ...c].slice(0, 8));
      const rs = await fetchSafetyStatus(token); setSafety(rs);
      setSafetyMessage(kind === "check-in" ? "Safety check-in recorded and synced to the mission trail." : "SOS event created. Emergency preview is ready for relay.");
    } catch {
      const q = kind === "check-in" ? queueOfflineCheckIn(checkInPayload) : queueOfflineSos(sosPayload);
      setPendingSafetyQueue(c => [...c, q]);
      setSafetyMessage(kind === "check-in" ? "Signal is unstable. Check-in saved locally and queued for retry." : "Signal is unstable. SOS saved locally and queued for retry.");
    } finally { setSafetyBusy(false); }
  }

  async function handleQuickReport(reportType: "catch" | "pollution" | "hazard" | "illegal_activity" | "current") {
    if (!token || !profile) return;
    const loc = deviceLocation;
    const lat = loc?.lat ?? bestZone?.center_lat ?? 33.679;
    const lon = loc?.lon ?? bestZone?.center_lon ?? 10.495;
    const payload = {
      lat, lon, report_type: reportType,
      severity: reportType === "pollution" || reportType === "hazard" || reportType === "illegal_activity" ? 4 : 3,
      species: reportType === "catch" ? (mission?.selected_species ?? profile.target_species[0] ?? null) : null,
      note: `${reportType} reported near ${bestZone?.label ?? "mission zone"}`,
    };

    if (!isOnline) {
      const q = queueOfflineReport(payload);
      setPendingReportsQueue(c => [...c, q]);
      setReportMessage("No network. Community report saved locally and will sync when the signal returns.");
      return;
    }
    setReportsBusy(true); setReportMessage(null);
    try {
      await submitCommunityReport(token, payload);
      const r = await fetchRecentReports(); setReportsFeed(r);
      setReportMessage("Community report recorded and shared with the zone engine.");
    } catch {
      const q = queueOfflineReport(payload);
      setPendingReportsQueue(c => [...c, q]);
      setReportMessage("Signal is unstable. Community report saved locally and queued for retry.");
    } finally { setReportsBusy(false); }
  }

  const value: AppContextValue = {
    token, profile, sessionLoading,
    handleLogin: (p: LoginPayload) => handleAuthResult(loginUser(p)),
    handleRegister: (p: RegisterPayload) => handleAuthResult(registerUser(p)),
    handleLogout, handleProfileSave,
    isOnline, deviceLocation, locationError, locationAge,
    port, setPort, species, setSpecies,
    loading, mission, heatmap, recommendation, route, lunar, safety, missionHistory, safetyEvents, adminOverview, adminLoading,
    safetyBusy, safetyMessage, pendingSafetyQueue, queueSyncBusy, handleSafetyAction,
    reportsFeed, reportsBusy, reportMessage, pendingReportsQueue, reportsQueueSyncBusy, handleQuickReport,
    uiLanguage,
    setUiLanguage: setUiLanguageState,
  };

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}
