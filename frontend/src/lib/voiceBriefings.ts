import type {
  DeviceLocationSnapshot,
  FishermanProfilePublic,
  MissionDepartureDecision,
  LunarResponse,
  RecommendationResponse,
  RouteResponse,
  SafetyStatusResponse,
  ZoneCard,
} from "../types";

function arabicDeparture(status: string | undefined) {
  switch (status) {
    case "GO":
      return "الخروج مناسب";
    case "CAUTION":
      return "اخرج بحذر";
    case "NO_GO":
      return "ما تخرجش توة";
    default:
      return "جاري تقييم الخروج";
  }
}

function cleanSea(condition: string | undefined) {
  if (!condition) return "حالة البحر غير واضحة";
  return `حالة البحر ${condition}`;
}

export function buildArabicMissionBriefing(params: {
  bestZone: ZoneCard | undefined;
  recommendation: RecommendationResponse | null;
  route: RouteResponse | null;
  departureDecision: MissionDepartureDecision | null;
  profile: FishermanProfilePublic | null;
}) {
  const { bestZone, recommendation, route, departureDecision, profile } = params;
  return [
    "هذا ملخص الرحلة.",
    bestZone ? `أحسن منطقة اليوم هي ${bestZone.label}.` : "أحسن منطقة مازالت تتحسب.",
    `وضعية الخروج: ${arabicDeparture(departureDecision?.status)}.`,
    route?.optimized_distance_km != null ? `المسافة تقريباً ${route.optimized_distance_km} كيلومتر.` : null,
    route?.estimated_fuel_l != null ? `الوقود المتوقع ${route.estimated_fuel_l} لتر.` : null,
    bestZone?.depth_m != null ? `العمق في المنطقة ${bestZone.depth_m} متر.` : null,
    bestZone ? `${cleanSea(bestZone.marine_condition)}.` : null,
    bestZone?.pollution_index != null ? `مؤشر التلوث ${bestZone.pollution_index} على مية.` : null,
    recommendation?.advisory ?? null,
    profile?.boat_name ? `الباتو المسجل هو ${profile.boat_name}.` : null,
  ].filter(Boolean).join(" ");
}

export function buildArabicSafetyBriefing(params: {
  safety: SafetyStatusResponse | null;
  deviceLocation: DeviceLocationSnapshot | null;
  pendingSafetyCount: number;
  profile: FishermanProfilePublic | null;
}) {
  const { safety, deviceLocation, pendingSafetyCount, profile } = params;
  return [
    "هذا ملخص السلامة.",
    `وضعية الخروج: ${arabicDeparture(safety?.departure_status)}.`,
    safety?.gps_status ? `${safety.gps_status}.` : null,
    deviceLocation ? `الموقع الحالي تقريباً ${deviceLocation.lat.toFixed(4)} شمال و ${deviceLocation.lon.toFixed(4)} شرق.` : null,
    pendingSafetyCount > 0 ? `عندك ${pendingSafetyCount} إجراءات سلامة محفوظة وتستنى في المزامنة.` : "ما عندك حتى إجراء سلامة في الانتظار.",
    safety?.recommended_action ? `${safety.recommended_action}.` : null,
    safety?.blocking_reasons.length ? `أهم أسباب المنع: ${safety.blocking_reasons.slice(0, 2).join(" ثم ")}.` : null,
    profile?.emergency_contacts[0]?.name ? `أول contact للنجدة هو ${profile.emergency_contacts[0].name}.` : null,
  ].filter(Boolean).join(" ");
}

export function buildArabicRouteBriefing(params: {
  route: RouteResponse | null;
  departurePort: string | undefined;
}) {
  const { route, departurePort } = params;
  return [
    "هذا ملخص الطريق.",
    departurePort ? `الانطلاق من ${departurePort}.` : null,
    route?.optimized_distance_km != null ? `المسافة المحسوبة ${route.optimized_distance_km} كيلومتر.` : null,
    route?.estimated_duration_h != null ? `المدة المتوقعة ${route.estimated_duration_h} ساعة.` : null,
    route?.estimated_fuel_l != null ? `الوقود المتوقع ${route.estimated_fuel_l} لتر.` : null,
    route?.min_depth_m != null ? `أقل عمق في المسار ${route.min_depth_m} متر.` : null,
    route?.max_depth_m != null ? `أقصى عمق في المسار ${route.max_depth_m} متر.` : null,
    route?.sea_state_summary ? `${route.sea_state_summary}.` : null,
    route?.safety_notes.length ? `أهم ملاحظات السلامة: ${route.safety_notes.slice(0, 2).join(" ثم ")}.` : null,
  ].filter(Boolean).join(" ");
}

export function buildArabicLunarBriefing(params: {
  lunar: LunarResponse | null;
}) {
  const { lunar } = params;
  return [
    "هذا ملخص القمر والصيد.",
    lunar?.phase_name ? `طور القمر الحالي هو ${lunar.phase_name}.` : null,
    lunar?.illumination_pct != null ? `نسبة الإضاءة ${lunar.illumination_pct} بالمية.` : null,
    lunar?.best_window ? `أفضل وقت للصيد: ${lunar.best_window}.` : null,
    lunar?.moonrise ? `طلوع القمر ${lunar.moonrise}.` : null,
    lunar?.moonset ? `غروب القمر ${lunar.moonset}.` : null,
    lunar?.species_guidance.length ? `نصيحة اليوم: ${lunar.species_guidance.slice(0, 2).join(" ثم ")}.` : null,
  ].filter(Boolean).join(" ");
}
