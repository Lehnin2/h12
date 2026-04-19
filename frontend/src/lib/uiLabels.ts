import type { UiLanguage } from "./uiCopy";

export function recommendationLabel(status: string | undefined, language: UiLanguage = "tn") {
  switch (status) {
    case "ACTIONABLE":
    case "GREEN":
      if (language === "tn") return "البلاصة باهية توة";
      return language === "fr" ? "Zone recommandée" : "Recommended now";
    case "HOLD":
    case "ORANGE":
      if (language === "tn") return "إستنى شوية";
      return language === "fr" ? "Attendre un peu" : "Wait for window";
    case "RED":
      if (language === "tn") return "بلاش خروج توة";
      return language === "fr" ? "Départ déconseillé" : "Not recommended";
    default:
      if (language === "tn") return "توجيه مباشر";
      return language === "fr" ? "Guidage live" : "Live guidance";
  }
}

export function departureLabel(status: string | undefined, language: UiLanguage = "tn") {
  switch (status) {
    case "GO":
      if (language === "tn") return "خروج مزيان";
      return language === "fr" ? "Bon départ" : "Good departure";
    case "CAUTION":
      if (language === "tn") return "خروج بالحذر";
      return language === "fr" ? "Départ avec prudence" : "Depart with caution";
    case "NO_GO":
      if (language === "tn") return "مش وقت خروج";
      return language === "fr" ? "Ne pas partir" : "Do not depart";
    default:
      if (language === "tn") return "تقييم الخروج";
      return language === "fr" ? "Évaluation départ" : "Assessing departure";
  }
}

export function routeLabel(status: string | undefined, language: UiLanguage = "tn") {
  switch (status) {
    case "GO":
      if (language === "tn") return "ثنية مريحة";
      return language === "fr" ? "Route prête" : "Route ready";
    case "CAUTION":
      if (language === "tn") return "ثنية بالحذر";
      return language === "fr" ? "Route prudente" : "Route needs caution";
    case "NO_GO":
      if (language === "tn") return "ثنية مش أمان";
      return language === "fr" ? "Route non conseillée" : "Route not advised";
    default:
      if (language === "tn") return "تقييم الثنية";
      return language === "fr" ? "Évaluation route" : "Route assessment";
  }
}

export function compactSeaLabel(condition: string | undefined, language: UiLanguage = "tn") {
  if (!condition) {
    if (language === "tn") return "حالة البحر...";
    return language === "fr" ? "État de mer..." : "Sea state...";
  }
  const cond = condition.toLowerCase();
  if (language === "tn") {
    if (cond === "calm") return "بحر هادي";
    if (cond === "moderate") return "بحر متوسط";
    if (cond === "rough") return "بحر هائج";
    return `بحر ${cond}`;
  }
  return `Sea ${cond}`;
}
