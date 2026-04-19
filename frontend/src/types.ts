export type ZoneColor = "GREEN" | "ORANGE" | "RED" | "BLACK";

export interface Port {
  id: string;
  name: string;
  short_name: string;
  lat: number;
  lon: number;
  risk_bias: number;
}

export interface ZoneCard {
  id: string;
  label: string;
  center_lat: number;
  center_lon: number;
  depth_m: number;
  legal_status: string;
  pollution_risk: number;
  pollution_index: number;
  pollution_source: string | null;
  pollution_data_live: boolean;
  fleet_load: number;
  fish_score: number;
  overall_score: number;
  confidence: number;
  color: ZoneColor;
  satellite_source: string;
  satellite_live: boolean;
  sst_c: number | null;
  chlorophyll_mg_m3: number | null;
  salinity_psu: number | null;
  turbidity_fnu: number | null;
  satellite_current_speed_kmh: number | null;
  satellite_productivity_index: number;
  marine_condition: string;
  marine_fishing_score: number;
  weather_source: string;
  weather_live: boolean;
  active_boats: number;
  recommended_boats: number;
  saturation_ratio: number;
  predicted_pressure: number;
  community_reports: number;
  recommended_species: string[];
  key_reason: string;
}

export interface HeatmapResponse {
  departure_port: string;
  selected_species: string;
  zones: ZoneCard[];
  legend: Record<string, string>;
  pollution_plume_origin: string;
}

export interface RecommendationResponse {
  departure_port: string;
  selected_species: string;
  best_zone: ZoneCard;
  alternatives: ZoneCard[];
  recommendation_status: string;
  minimum_safe_score: number;
  viable_zones_count: number;
  advisory: string;
  rationale: string[];
}

export interface RouteLeg {
  label: string;
  point: { lat: number; lon: number };
  safety_state: string;
}

export interface DeviceLocationSnapshot {
  lat: number;
  lon: number;
  accuracy_m: number | null;
  heading_deg: number | null;
  speed_kmh: number | null;
  captured_at: string;
  source: "live" | "cached";
}

export interface RouteResponse {
  departure_port: string;
  target_zone_id: string;
  direct_distance_km: number;
  optimized_distance_km: number;
  estimated_duration_h: number;
  estimated_fuel_l: number;
  savings_l: number;
  min_depth_m: number;
  max_depth_m: number;
  route_risk_level: string;
  weather_risk_level: string;
  route_readiness: string;
  sea_state_summary: string;
  path: RouteLeg[];
  safety_notes: string[];
}

export interface LunarForecastDay {
  day_label: string;
  phase_name: string;
  illumination_pct: number;
  fishing_rating: number;
}

export interface LunarResponse {
  phase_name: string;
  illumination_pct: number;
  moonrise: string;
  moonset: string;
  best_window: string;
  species_guidance: string[];
  forecast: LunarForecastDay[];
}

export interface SafetyStatusResponse {
  departure_port: string;
  departure_status: string;
  safety_score: number;
  gps_status: string;
  last_sync_mode: string;
  emergency_contacts: string[];
  emergency_message_preview: string;
  blocking_reasons: string[];
  recommended_checks: string[];
  recommended_action: string;
  last_check_in_at: string | null;
  open_incidents: number;
}

export interface SatelliteObservationResponse {
  lat: number;
  lon: number;
  source: string;
  status: string;
  is_live: boolean;
  timestamp: string;
  sst_c: number | null;
  chlorophyll_mg_m3: number | null;
  salinity_psu: number | null;
  turbidity_fnu: number | null;
  suspended_matter_mg_l: number | null;
  current_speed_kmh: number | null;
  current_direction_deg: number | null;
  productivity_index: number;
  turbidity_risk: string;
  advisory: string;
}

export interface MarineWeatherSnapshot {
  timestamp: string;
  air_temperature_c: number | null;
  water_temperature_c: number | null;
  wind_speed_kmh: number | null;
  wind_direction_deg: number | null;
  wave_height_m: number | null;
  current_speed_kmh: number | null;
  gust_kmh: number | null;
  precipitation_mm_per_hour: number | null;
  condition: string;
  fishing_score: number;
  advisory: string;
}

export interface MarineWeatherResponse {
  lat: number;
  lon: number;
  source: string;
  status: string;
  is_live: boolean;
  current: MarineWeatherSnapshot;
  forecast: MarineWeatherSnapshot[];
}

export interface MissionDepartureDecision {
  status: string;
  score: number;
  summary: string;
  reasons: string[];
  actions: string[];
}

export interface MissionSourceFreshness {
  source_key: string;
  source_name: string;
  freshness: string;
  age_minutes: number | null;
  observed_at: string | null;
  is_live: boolean;
  detail: string;
}

export interface MissionHistoryEntry {
  id: string;
  requested_at: string;
  departure_port: string;
  selected_species: string;
  recommended_zone_id: string;
  recommended_zone_label: string;
  departure_status: string;
  mission_score: number;
}

export interface MissionHistoryResponse {
  entries: MissionHistoryEntry[];
}

export interface MissionBriefingResponse {
  departure_port: string;
  selected_species: string;
  heatmap: HeatmapResponse;
  recommendation: RecommendationResponse;
  route: RouteResponse;
  satellite: SatelliteObservationResponse;
  weather: MarineWeatherResponse;
  lunar: LunarResponse;
  safety: SafetyStatusResponse;
  departure_decision: MissionDepartureDecision;
  source_freshness: MissionSourceFreshness[];
}

export interface SafetyEventResponse {
  id: string;
  event_type: string;
  status: string;
  lat: number;
  lon: number;
  note: string | null;
  message_preview: string;
  created_at: string;
}

export interface SafetyEventListResponse {
  events: SafetyEventResponse[];
}

export interface SafetyCheckInPayload {
  lat: number;
  lon: number;
  note?: string | null;
  battery_level_pct?: number | null;
  sync_mode?: string;
}

export interface SafetySosPayload {
  lat: number;
  lon: number;
  message?: string | null;
}

export interface CommunityReportCreatePayload {
  lat: number;
  lon: number;
  report_type: "catch" | "pollution" | "hazard" | "illegal_activity" | "current";
  severity: number;
  species?: string | null;
  note?: string | null;
}

export interface CommunityReportSnapshot {
  id: string;
  user_id: string;
  reporter_name: string;
  lat: number;
  lon: number;
  report_type: string;
  severity: number;
  species: string | null;
  note: string | null;
  recorded_at: string;
  zone_id: string | null;
  zone_label: string | null;
}

export interface ZoneReportSummary {
  zone_id: string;
  zone_label: string;
  total_reports: number;
  catch_reports: number;
  pollution_reports: number;
  hazard_reports: number;
  illegal_activity_reports: number;
  current_reports: number;
  productivity_signal: number;
  risk_signal: number;
  advisory: string | null;
}

export interface CommunityReportFeedResponse {
  recent_reports: CommunityReportSnapshot[];
  zone_summaries: ZoneReportSummary[];
}

export interface OfflineCommunityReportQueueItem {
  id: string;
  created_at: string;
  payload: CommunityReportCreatePayload;
}

export interface OfflineSafetyCheckInQueueItem {
  id: string;
  kind: "check-in";
  created_at: string;
  payload: SafetyCheckInPayload;
}

export interface OfflineSafetySosQueueItem {
  id: string;
  kind: "sos";
  created_at: string;
  payload: SafetySosPayload;
}

export type OfflineSafetyQueueItem = OfflineSafetyCheckInQueueItem | OfflineSafetySosQueueItem;

export interface EmergencyContact {
  name: string;
  phone: string;
  relation: string;
}

export interface FishermanProfilePublic {
  avatar_url: string | null;
  id: string;
  email: string;
  is_admin: boolean;
  full_name: string;
  license_number: string | null;
  license_type: string;
  home_port: string;
  boat_name: string;
  boat_length_m: number;
  engine_hp: number;
  fuel_capacity_l: number;
  fuel_consumption_l_per_hour: number;
  fishing_gears: string[];
  target_species: string[];
  emergency_contacts: EmergencyContact[];
}

export interface RegisterPayload {
  email: string;
  password: string;
  full_name: string;
  license_number?: string | null;
  license_type: string;
  home_port: string;
  boat_name: string;
  boat_length_m: number;
  engine_hp: number;
  fuel_capacity_l: number;
  fuel_consumption_l_per_hour: number;
  fishing_gears: string[];
  target_species: string[];
  emergency_contacts: EmergencyContact[];
}

export interface LoginPayload {
  email: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  profile: FishermanProfilePublic;
}

export interface AdminTerritoryMetric {
  label: string;
  value: string;
  tone: string;
  detail?: string | null;
}

export interface AdminPressureZone {
  zone_id: string;
  zone_label: string;
  overall_score: number;
  color: string;
  active_boats: number;
  inbound_missions: number;
  pressure_ratio: number;
  pollution_index: number;
  legal_status: string;
  advisory: string;
}

export interface AdminSourceHealth {
  source_key: string;
  freshness: string;
  detail: string;
  age_minutes: number | null;
}

export interface AdminOverviewResponse {
  generated_at: string;
  admin_email: string;
  territorial_metrics: AdminTerritoryMetric[];
  pressure_zones: AdminPressureZone[];
  recent_safety_events: SafetyEventResponse[];
  recent_reports: CommunityReportSnapshot[];
  recent_missions: MissionHistoryEntry[];
  source_health: AdminSourceHealth[];
}

export interface ChatTurn {
  role: "user" | "assistant";
  content: string;
}

export interface ChatToolSnapshot {
  tool_name: string;
  summary: string;
}

export interface ChatMessageRequest {
  message: string;
  page: string;
  history: ChatTurn[];
}

export interface ChatMessageResponse {
  answer: string;
  answer_ar: string | null;
  voice_text_ar: string | null;
  tools_used: ChatToolSnapshot[];
  suggested_prompts: string[];
  used_llm: boolean;
  page: string;
}
