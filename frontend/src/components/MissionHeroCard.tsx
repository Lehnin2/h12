import { NavLink } from "react-router-dom";

import type {
  FishermanProfilePublic,
  MissionDepartureDecision,
  RecommendationResponse,
  RouteResponse,
  ZoneCard,
} from "../types";
import type { UiLanguage } from "../lib/uiCopy";
import { compactSeaLabel, departureLabel, recommendationLabel, routeLabel } from "../lib/uiLabels";
import { StatusPill } from "./StatusPill";
import { toneFromStatus } from "../app/AppContext";
import { UiIcon } from "./UiIcon";

interface MissionHeroCardProps {
  bestZone: ZoneCard | undefined;
  recommendation: RecommendationResponse | null;
  route: RouteResponse | null;
  departureDecision: MissionDepartureDecision | null;
  profile: FishermanProfilePublic | null;
  uiLanguage: UiLanguage;
}

export function MissionHeroCard({
  bestZone,
  recommendation,
  route,
  departureDecision,
  uiLanguage,
}: MissionHeroCardProps) {
  return (
    <article className="mission-hero-card">
      <div className="mission-hero-card__top">
        <div className="section-card__title-group">
          <div className="section-card__icon">
            <UiIcon name="route" duotone />
          </div>
          <div>
            <p className="mission-hero-card__eyebrow">Best zone now</p>
            <h2>{bestZone?.label ?? "Loading zone intelligence"}</h2>
          </div>
        </div>
        <StatusPill tone={recommendation?.recommendation_status === "ACTIONABLE" ? "good" : "warn"}>
          {recommendationLabel(recommendation?.recommendation_status ?? bestZone?.color, uiLanguage)}
        </StatusPill>
      </div>

      <div className="mission-hero-card__decision">
        <span>Departure Window</span>
        <strong>{departureLabel(departureDecision?.status, uiLanguage)}</strong>
        <small>{recommendation?.advisory ?? bestZone?.key_reason ?? "Calculating safe mission window."}</small>
      </div>

      <div className="mission-hero-card__metrics">
        <div>
          <span>Route</span>
          <strong>{route?.optimized_distance_km ?? "--"} km</strong>
        </div>
        <div>
          <span>Fuel</span>
          <strong>{route?.estimated_fuel_l ?? "--"} L</strong>
        </div>
        <div>
          <span>Depth</span>
          <strong>{bestZone?.depth_m ?? "--"} m</strong>
        </div>
        <div>
          <span>Sea</span>
          <strong>{compactSeaLabel(bestZone?.marine_condition, uiLanguage)}</strong>
        </div>
      </div>

      <div className="mission-actions">
        <NavLink to="/route" className="primary-action">Start route</NavLink>
        <NavLink to="/safety" className="secondary-action">Open safety</NavLink>
      </div>
    </article>
  );
}
