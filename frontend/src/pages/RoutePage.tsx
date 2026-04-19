import { useAppContext, toneFromStatus } from "../app/AppContext";
import { SectionCard } from "../components/SectionCard";
import { StatusPill } from "../components/StatusPill";
import { VoiceAssistButton } from "../components/VoiceAssistButton";
import { uiCopy } from "../lib/uiCopy";
import { routeLabel } from "../lib/uiLabels";
import { buildArabicRouteBriefing } from "../lib/voiceBriefings";

export function RoutePage() {
  const { route, mission, uiLanguage } = useAppContext();
  const copy = uiCopy[uiLanguage].route;

  return (
    <SectionCard
      icon="route"
      eyebrow={copy.eyebrow}
      title={`${route?.optimized_distance_km ?? "--"} km ${copy.optimizedLane}`}
      aside={
        <div className="section-card__controls">
          <VoiceAssistButton
            getText={() => buildArabicRouteBriefing({
              route,
              departurePort: mission?.departure_port,
            })}
          />
          <StatusPill tone={toneFromStatus(route?.route_readiness ?? route?.route_risk_level)}>
            {route?.route_readiness ? routeLabel(route?.route_readiness, uiLanguage) : copy.fuelAware}
          </StatusPill>
        </div>
      }
    >
      <div className="route-metrics">
        <div><span>{copy.optimized}</span><strong>{route?.optimized_distance_km ?? "--"} km</strong></div>
        <div><span>{copy.estimatedFuel}</span><strong>{route?.estimated_fuel_l ?? "--"} L</strong></div>
        <div><span>{copy.fuelSaved}</span><strong>{route?.savings_l ?? "--"} L</strong></div>
      </div>
      <div className="tag-row">
        <span className="tag">{copy.depthMin} {route?.min_depth_m ?? "--"} m</span>
        <span className="tag">{copy.depthMax} {route?.max_depth_m ?? "--"} m</span>
        <span className="tag">{copy.weatherRisk} {route?.weather_risk_level ?? "--"}</span>
        <span className="tag">{mission?.departure_port ?? "Mission"} {copy.corridor}</span>
      </div>
      <p className="body-copy">{route?.sea_state_summary}</p>
      <ul className="bullet-list">
        {route?.safety_notes.map((item, index) => <li key={`${index}-${item}`}>{item}</li>)}
      </ul>
    </SectionCard>
  );
}
