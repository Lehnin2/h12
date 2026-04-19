import { useAppContext, toneFromStatus } from "../app/AppContext";
import { SectionCard } from "../components/SectionCard";
import { StatusPill } from "../components/StatusPill";

function toneFromFreshness(freshness: string) {
  if (freshness === "fresh" || freshness === "fresh_cached" || freshness === "static") {
    return "good" as const;
  }
  if (freshness === "aging") {
    return "warn" as const;
  }
  return "danger" as const;
}

export function AdminPage() {
  const { adminOverview, adminLoading } = useAppContext();

  if (adminLoading && !adminOverview) {
    return (
      <SectionCard eyebrow="Admin" title="Loading territorial board">
        <p className="body-copy">Aggregating fleet pressure, safety incidents, mission history, and source health.</p>
      </SectionCard>
    );
  }

  if (!adminOverview) {
    return (
      <SectionCard eyebrow="Admin" title="Territorial board unavailable">
        <p className="body-copy">Admin overview is not available yet for this session.</p>
      </SectionCard>
    );
  }

  return (
    <>
      <SectionCard
        eyebrow="Admin territorial board"
        title="Gulf of Gabes control room"
        aside={<StatusPill tone="neutral">{new Date(adminOverview.generated_at).toLocaleTimeString()}</StatusPill>}
      >
        <p className="body-copy">
          This view is reserved for cooperative or territorial operators who need to see pressure, incidents,
          and data health across the full mission area.
        </p>
        <div className="hero-metrics">
          {adminOverview.territorial_metrics.map((metric) => (
            <div key={metric.label}>
              <span>{metric.label}</span>
              <strong>{metric.value}</strong>
              {metric.detail ? <small>{metric.detail}</small> : null}
            </div>
          ))}
        </div>
      </SectionCard>

      <div className="dashboard-grid">
        <SectionCard eyebrow="Pressure zones" title="Where intervention matters now">
          <div className="zone-stack">
            {adminOverview.pressure_zones.map((zone) => (
              <div key={zone.zone_id} className="zone-row">
                <div className={`zone-dot zone-dot--${zone.color.toLowerCase()}`} />
                <div className="zone-row__content">
                  <strong>{zone.zone_label}</strong>
                  <span>
                    pressure {zone.pressure_ratio} · boats {zone.active_boats} · inbound {zone.inbound_missions} ·
                    pollution {zone.pollution_index}/100 · {zone.legal_status.toLowerCase()}
                  </span>
                </div>
                <strong>{zone.overall_score}</strong>
              </div>
            ))}
          </div>
        </SectionCard>

        <SectionCard eyebrow="Source health" title="Decision system freshness">
          <div className="zone-stack">
            {adminOverview.source_health.map((source) => (
              <div key={source.source_key} className="zone-row">
                <div className={`zone-dot zone-dot--${toneFromFreshness(source.freshness) === "good" ? "green" : toneFromFreshness(source.freshness) === "warn" ? "orange" : "red"}`} />
                <div className="zone-row__content">
                  <strong>{source.source_key}</strong>
                  <span>{source.detail}</span>
                </div>
                <strong>{source.age_minutes == null ? source.freshness : `${source.age_minutes}m`}</strong>
              </div>
            ))}
          </div>
        </SectionCard>

        <SectionCard eyebrow="Safety incidents" title="Latest alerts and check-ins">
          <div className="zone-stack">
            {adminOverview.recent_safety_events.map((event) => (
              <div key={event.id} className="zone-row">
                <div className={`zone-dot zone-dot--${toneFromStatus(event.status) === "good" ? "green" : toneFromStatus(event.status) === "warn" ? "orange" : "red"}`} />
                <div className="zone-row__content">
                  <strong>{event.event_type}</strong>
                  <span>
                    {event.message_preview} · {new Date(event.created_at).toLocaleString()}
                  </span>
                </div>
                <strong>{event.status}</strong>
              </div>
            ))}
          </div>
        </SectionCard>

        <SectionCard eyebrow="Community reports" title="Field signals from fishermen">
          <div className="zone-stack">
            {adminOverview.recent_reports.map((report) => (
              <div key={report.id} className="zone-row">
                <div className={`zone-dot zone-dot--${report.report_type === "catch" ? "green" : report.report_type === "current" ? "orange" : "red"}`} />
                <div className="zone-row__content">
                  <strong>{report.zone_label ?? report.report_type}</strong>
                  <span>
                    {report.report_type} · severity {report.severity} · {report.reporter_name}
                    {report.note ? ` · ${report.note}` : ""}
                  </span>
                </div>
                <strong>{new Date(report.recorded_at).toLocaleTimeString()}</strong>
              </div>
            ))}
          </div>
        </SectionCard>
      </div>

      <SectionCard eyebrow="Mission history" title="Latest territorial recommendations">
        <div className="zone-stack">
          {adminOverview.recent_missions.map((mission) => (
            <div key={mission.id} className="zone-row">
              <div className={`zone-dot zone-dot--${toneFromStatus(mission.departure_status) === "good" ? "green" : toneFromStatus(mission.departure_status) === "warn" ? "orange" : "red"}`} />
              <div className="zone-row__content">
                <strong>{mission.recommended_zone_label}</strong>
                <span>
                  {mission.selected_species} · {mission.departure_port} · {new Date(mission.requested_at).toLocaleString()}
                </span>
              </div>
              <strong>{mission.mission_score}</strong>
            </div>
          ))}
        </div>
      </SectionCard>
    </>
  );
}
