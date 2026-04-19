import { NavLink } from "react-router-dom";
import { useAppContext, toneFromStatus } from "../app/AppContext";
import { AlternativeZones } from "../components/AlternativeZones";
import { MapPanel } from "../components/MapPanel";
import { MissionHeroCard } from "../components/MissionHeroCard";
import { SectionCard } from "../components/SectionCard";
import { StatusPill } from "../components/StatusPill";
import { VoiceAssistButton } from "../components/VoiceAssistButton";
import { uiCopy } from "../lib/uiCopy";
import { departureLabel, routeLabel } from "../lib/uiLabels";
import { buildArabicMissionBriefing } from "../lib/voiceBriefings";

export function HeatmapPage() {
  const {
    heatmap, recommendation, route, mission, deviceLocation,
    profile, loading, uiLanguage,
  } = useAppContext();
  const copy = uiCopy[uiLanguage].heatmap;

  if (loading && !heatmap) {
    return <HeatmapSkeleton />;
  }

  const bestZone = recommendation?.best_zone;
  const departureDecision = mission?.departure_decision ?? null;

  return (
    <>
      <section className="heatmap-hero">
        <MapPanel
          zones={heatmap?.zones ?? []}
          recommendation={recommendation}
          route={route}
          currentLocation={deviceLocation}
          uiLanguage={uiLanguage}
        />
        <div className="heatmap-hero__summary">
          <MissionHeroCard
            bestZone={bestZone}
            recommendation={recommendation}
            route={route}
            departureDecision={departureDecision}
            profile={profile}
            uiLanguage={uiLanguage}
          />
        </div>
      </section>

      <div className="heatmap-support-grid">
        <SectionCard
          icon="safety"
          eyebrow={copy.departureDecision}
          title={departureLabel(departureDecision?.status, uiLanguage)}
          aside={
            <div className="section-card__controls">
              <VoiceAssistButton
                getText={() => buildArabicMissionBriefing({
                  bestZone,
                  recommendation,
                  route,
                  departureDecision,
                  profile,
                })}
              />
              <StatusPill tone={toneFromStatus(departureDecision?.status)}>{departureDecision ? `${departureDecision.score}/100` : "Live"}</StatusPill>
            </div>
          }
        >
          <p className="body-copy">{departureDecision?.summary ?? "We are checking whether today is a real go, caution, or no-go mission."}</p>
          <div className="hero-metrics hero-metrics--compact">
            <div><span>Decision</span><strong>{departureLabel(departureDecision?.status, uiLanguage)}</strong></div>
            <div><span>Safety score</span><strong>{departureDecision?.score ?? "--"}</strong></div>
            <div><span>Route readiness</span><strong>{routeLabel(route?.route_readiness, uiLanguage)}</strong></div>
          </div>
          <ul className="bullet-list">
            {(departureDecision?.reasons ?? []).slice(0, 3).map((item, index) => <li key={`${index}-${item}`}>{item}</li>)}
          </ul>
        </SectionCard>

        <SectionCard
          icon="environmental"
          eyebrow={copy.missionSupport}
          title={copy.supportTitle}
          aside={<StatusPill tone="neutral">Live overview</StatusPill>}
        >
          <div className="hero-metrics hero-metrics--compact">
            <div><span>{copy.productivity}</span><strong>{bestZone?.satellite_productivity_index ?? "--"}/100</strong></div>
            <div><span>{copy.salinity}</span><strong>{bestZone?.salinity_psu ?? "--"} PSU</strong></div>
            <div><span>{copy.slope}</span><strong>{bestZone?.depth_m != null ? `${bestZone?.depth_m} m zone` : "--"}</strong></div>
          </div>
          <div className="tag-row">
            {(departureDecision?.actions ?? []).slice(0, 3).map((item, index) => <span key={`${index}-${item}`} className="tag tag--sand">{item}</span>)}
          </div>
        </SectionCard>
      </div>

      {loading ? <StatusPill tone="neutral">{copy.refreshing}</StatusPill> : null}

      <SectionCard icon="heatmap" eyebrow={copy.missionDetails} title={copy.detailsTitle} aside={<StatusPill tone="neutral">Open if needed</StatusPill>}>
        <div className="details-stack">
          <details className="details-card" open>
            <summary>{copy.rationale}</summary>
            <ul className="bullet-list">
              {recommendation?.rationale.map((item, index) => <li key={`${index}-${item}`}>{item}</li>)}
            </ul>
          </details>

          <details className="details-card">
            <summary>{copy.alternatives}</summary>
            <AlternativeZones recommendation={recommendation} />
          </details>

          <details className="details-card">
            <summary>{copy.zoneStack}</summary>
            <div className="zone-stack">
              {heatmap?.zones.map((zone) => (
                <div key={zone.id} className="zone-row">
                  <div className={`zone-dot zone-dot--${zone.color.toLowerCase()}`} />
                  <div className="zone-row__content">
                    <strong>{zone.label}</strong>
                    <span>
                      {zone.key_reason} · boats {zone.active_boats} · inbound {zone.recommended_boats} · salinity {zone.salinity_psu ?? "--"} PSU · turbidity {zone.turbidity_fnu ?? "--"} FNU · copernicus {zone.satellite_productivity_index}/100
                    </span>
                  </div>
                  <strong>{zone.overall_score}</strong>
                </div>
              ))}
            </div>
          </details>

          <details className="details-card">
            <summary>{copy.nextActions}</summary>
            <div className="mission-actions">
              <NavLink to="/route" className="primary-action">{copy.routeBriefing}</NavLink>
              <NavLink to="/safety" className="secondary-action">{copy.safetyControls}</NavLink>
            </div>
          </details>
        </div>
      </SectionCard>
    </>
  );
}

function HeatmapSkeleton() {
  return (
    <div className="skeleton-page">
      <div className="skeleton skeleton-hero" />
      <div className="heatmap-support-grid">
        <div className="skeleton skeleton-card" />
        <div className="skeleton skeleton-card" />
      </div>
      <div className="skeleton skeleton-card skeleton-card--large" />
    </div>
  );
}
