import { motion, AnimatePresence } from "framer-motion";
import { useAppContext, toneFromStatus } from "../app/AppContext";
import { ProfilePanel } from "../components/ProfilePanel";
import { SectionCard } from "../components/SectionCard";
import { StatusPill } from "../components/StatusPill";
import { UiIcon } from "../components/UiIcon";
import { uiCopy } from "../lib/uiCopy";

export function ProfilePage() {
  const {
    profile, handleProfileSave, handleLogout,
    mission, reportsFeed, reportsBusy, reportMessage, pendingReportsQueue,
    reportsQueueSyncBusy, handleQuickReport, uiLanguage,
  } = useAppContext();
  const copy = uiCopy[uiLanguage].profilePage;

  const satellite = mission?.satellite ?? null;
  const weather = mission?.weather ?? null;
  const sourceFreshness = mission?.source_freshness ?? [];
  const recentCommunityReports = reportsFeed.recent_reports.slice(0, 5);

  if (!profile) return null;

  if (!mission) {
    return <ProfileSkeleton />;
  }

  return (
    <>
      <ProfilePanel profile={profile} onSave={handleProfileSave} onLogout={handleLogout} />

      <SectionCard
        icon="chat"
        eyebrow={copy.reports}
        title={copy.fieldIntel}
        aside={<StatusPill tone={pendingReportsQueue.length ? "warn" : "neutral"}>{pendingReportsQueue.length ? copy.pending(pendingReportsQueue.length) : copy.shared}</StatusPill>}
      >
        <p className="body-copy">{copy.reportsBody}</p>
        <div className="report-actions">
          <button className="report-button report-button--good" type="button" disabled={reportsBusy || reportsQueueSyncBusy} onClick={() => void handleQuickReport("catch")}><UiIcon name="catch" duotone className="report-button__icon" />{copy.catch}</button>
          <button className="report-button report-button--danger" type="button" disabled={reportsBusy || reportsQueueSyncBusy} onClick={() => void handleQuickReport("pollution")}><UiIcon name="pollution" duotone className="report-button__icon" />{copy.pollution}</button>
          <button className="report-button report-button--warn" type="button" disabled={reportsBusy || reportsQueueSyncBusy} onClick={() => void handleQuickReport("hazard")}><UiIcon name="hazard" duotone className="report-button__icon" />{copy.hazard}</button>
          <button className="report-button" type="button" disabled={reportsBusy || reportsQueueSyncBusy} onClick={() => void handleQuickReport("current")}><UiIcon name="current" duotone className="report-button__icon" />{copy.current}</button>
          <button className="report-button" type="button" disabled={reportsBusy || reportsQueueSyncBusy} onClick={() => void handleQuickReport("illegal_activity")}><UiIcon name="illegal" duotone className="report-button__icon" />{copy.illegal}</button>
        </div>
        <AnimatePresence>
          {reportMessage ? (
            <motion.div
              initial={{ opacity: 0, scale: 0.9, y: 10 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.9, y: 10 }}
              className="success-toast"
            >
              <UiIcon name="catch" duotone className="success-toast__icon" />
              <span>{reportMessage}</span>
            </motion.div>
          ) : null}
        </AnimatePresence>
        {pendingReportsQueue.length ? (
          <div className="tag-row">
            {pendingReportsQueue.slice(0, 3).map((item) => (
              <span key={item.id} className="tag tag--sand">pending {item.payload.report_type} {new Date(item.created_at).toLocaleTimeString()}</span>
            ))}
          </div>
        ) : null}
        <div className="zone-stack">
          {recentCommunityReports.map((report) => (
            <div key={report.id} className="zone-row">
              <div className={`zone-dot zone-dot--${report.report_type === "catch" ? "green" : report.report_type === "pollution" || report.report_type === "hazard" || report.report_type === "illegal_activity" ? "red" : "orange"}`} />
              <div className="zone-row__content">
                <strong className="zone-row__title">
                  <UiIcon
                    name={
                      report.report_type === "catch" ? "catch"
                        : report.report_type === "pollution" ? "pollution"
                          : report.report_type === "hazard" ? "hazard"
                            : report.report_type === "current" ? "current"
                              : "illegal"
                    }
                    duotone
                    className="inline-icon"
                  />
                  {report.zone_label ?? report.report_type}
                </strong>
                <span>{report.report_type} · severity {report.severity} · {report.reporter_name}{report.note ? ` · ${report.note}` : ""}</span>
              </div>
              <strong>{new Date(report.recorded_at).toLocaleTimeString()}</strong>
            </div>
          ))}
        </div>
      </SectionCard>

      <SectionCard
        icon="satellite"
        eyebrow={copy.satellite}
        title={`${satellite?.productivity_index ?? "--"}/100 ${copy.productivity}`}
        aside={<StatusPill tone={satellite?.is_live ? "good" : "neutral"}>{satellite?.is_live ? copy.live : copy.cached}</StatusPill>}
      >
        <div className="hero-metrics hero-metrics--compact">
          <div><span>SST</span><strong>{satellite?.sst_c ?? "--"} C</strong></div>
          <div><span>Chlorophyll</span><strong>{satellite?.chlorophyll_mg_m3 ?? "--"} mg/m3</strong></div>
          <div><span>Surface current</span><strong>{satellite?.current_speed_kmh ?? "--"} km/h</strong></div>
          <div><span>Salinity</span><strong>{satellite?.salinity_psu ?? "--"} PSU</strong></div>
          <div><span>Turbidity</span><strong>{satellite?.turbidity_fnu ?? "--"} FNU</strong></div>
        </div>
        <div className="tag-row">
          <span className="tag">Risk {satellite?.turbidity_risk ?? "--"}</span>
          <span className="tag">SPM {satellite?.suspended_matter_mg_l ?? "--"} mg/L</span>
          <span className="tag">{satellite?.source ?? "Copernicus"}</span>
        </div>
        <p className="body-copy">{satellite?.advisory}</p>
      </SectionCard>

      <SectionCard
        icon="environmental"
        eyebrow={copy.weather}
        title={`${weather?.current.condition ?? "--"} ${copy.seaState}`}
        aside={<StatusPill tone={weather?.is_live ? "good" : "neutral"}>{weather?.is_live ? copy.live : copy.cached}</StatusPill>}
      >
        <div className="hero-metrics hero-metrics--compact">
          <div><span>Wind</span><strong>{weather?.current.wind_speed_kmh ?? "--"} km/h</strong></div>
          <div><span>Wave</span><strong>{weather?.current.wave_height_m ?? "--"} m</strong></div>
          <div><span>Readiness</span><strong>{weather?.current.fishing_score ?? "--"}/100</strong></div>
        </div>
        <p className="body-copy">{weather?.current.advisory}</p>
      </SectionCard>

      <SectionCard icon="admin" eyebrow={copy.freshness} title={copy.transparency} aside={<StatusPill tone="neutral">{copy.traceable}</StatusPill>}>
        <div className="zone-stack">
          {sourceFreshness.map((source) => (
            <div key={source.source_key} className="zone-row">
              <div className={`zone-dot zone-dot--${source.freshness === "fresh" || source.freshness === "fresh_cached" || source.freshness === "static" ? "green" : source.freshness === "aging" ? "orange" : "red"}`} />
              <div className="zone-row__content">
                <strong>{source.source_key}</strong>
                <span>{source.detail} · {source.source_name}</span>
              </div>
              <strong>{source.age_minutes == null ? source.freshness : `${source.age_minutes}m`}</strong>
            </div>
          ))}
        </div>
      </SectionCard>
    </>
  );
}

function ProfileSkeleton() {
  return (
    <div className="skeleton-page">
      <div className="skeleton skeleton-profile-header" />
      <div className="skeleton skeleton-card" />
      <div className="skeleton skeleton-card" />
      <div className="skeleton skeleton-card skeleton-card--large" />
    </div>
  );
}
