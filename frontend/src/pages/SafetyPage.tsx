import { useAppContext, toneFromStatus } from "../app/AppContext";
import { SectionCard } from "../components/SectionCard";
import { StatusPill } from "../components/StatusPill";
import { UiIcon } from "../components/UiIcon";
import { VoiceAssistButton } from "../components/VoiceAssistButton";
import { formatLocationLabel } from "../lib/deviceLocation";
import { uiCopy } from "../lib/uiCopy";
import { departureLabel } from "../lib/uiLabels";
import { buildArabicSafetyBriefing } from "../lib/voiceBriefings";

export function SafetyPage() {
  const {
    safety, safetyBusy, safetyMessage, pendingSafetyQueue, queueSyncBusy,
    handleSafetyAction, safetyEvents, deviceLocation, locationError, locationAge,
    species, mission, missionHistory, profile, uiLanguage,
  } = useAppContext();
  const copy = uiCopy[uiLanguage].safetyPage;

  return (
    <>
      <SectionCard
        icon="safety"
        eyebrow={copy.eyebrow}
        title={copy.title}
        aside={
          <div className="section-card__controls">
            <VoiceAssistButton
              getText={() => buildArabicSafetyBriefing({
                safety,
                deviceLocation,
                pendingSafetyCount: pendingSafetyQueue.length,
                profile,
              })}
            />
            <StatusPill tone={toneFromStatus(safety?.departure_status)}>{departureLabel(safety?.departure_status, uiLanguage)}</StatusPill>
          </div>
        }
      >
        <div className="safety-cockpit">
          <div className="safety-cockpit__main">
            <div className={`safety-hero safety-hero--${toneFromStatus(safety?.departure_status)}`}>
              <p className="safety-hero__eyebrow">{copy.departureSafety}</p>
              <h3>{departureLabel(safety?.departure_status, uiLanguage)}</h3>
              <p>{safety?.recommended_action ?? "Checking route, sea state, and legal corridor."}</p>
              <div className="safety-hero__chips">
                <span className="tag">Score {safety?.safety_score ?? "--"}</span>
                <span className="tag">Mode {safety?.last_sync_mode ?? "Offline cache"}</span>
                <span className="tag">{mission?.selected_species ?? species}</span>
                <span className="tag">Open incidents {safety?.open_incidents ?? 0}</span>
              </div>
            </div>

            <div className="safety-grid">
              <div className="mission-signal-card">
                <span><UiIcon name="gps" duotone className="inline-icon" />{copy.gps}</span>
                <strong>{formatLocationLabel(deviceLocation)}</strong>
                <small>{locationAge == null ? "Fix age unknown" : `Fix age ${locationAge} min`}</small>
              </div>
              <div className="mission-signal-card">
                <span>{copy.checkin}</span>
                <strong>{safety?.last_check_in_at ? new Date(safety.last_check_in_at).toLocaleTimeString() : "No check-in yet"}</strong>
                <small>{safety?.gps_status ?? "GPS status unavailable"}</small>
              </div>
              <div className="mission-signal-card">
                <span><UiIcon name="queue" duotone className="inline-icon" />{copy.queue}</span>
                <strong>{pendingSafetyQueue.length} pending action(s)</strong>
                <small>{pendingSafetyQueue.length ? "Will sync when the signal returns" : "No pending safety retry"}</small>
              </div>
              <div className="mission-signal-card">
                <span>{copy.boatPort}</span>
                <strong>{profile?.boat_name ?? "Boat pending"}</strong>
                <small>{mission?.departure_port ?? profile?.home_port ?? "Port pending"}</small>
              </div>
            </div>

            {locationError ? <p className="body-copy">{locationError}</p> : null}

            {safety?.blocking_reasons.length ? (
              <div className="safety-panel">
                <p className="safety-panel__title">{copy.blocking}</p>
                <ul className="bullet-list">
                  {safety.blocking_reasons.map((item, index) => <li key={`${index}-${item}`}>{item}</li>)}
                </ul>
              </div>
            ) : null}

            <div className="safety-panel">
              <p className="safety-panel__title">{copy.preview}</p>
              <div className="safety-box">
                <strong>{safety?.emergency_message_preview}</strong>
              </div>
            </div>

            <div className="safety-panel">
              <p className="safety-panel__title">{copy.checks}</p>
              <ul className="bullet-list">
                {(safety?.recommended_checks ?? []).slice(0, 4).map((item, index) => (
                  <li key={`${index}-${item}`}>{item}</li>
                ))}
              </ul>
            </div>
          </div>

          <aside className="safety-cockpit__actions">
            <div className="safety-panel">
              <p className="safety-panel__title"><UiIcon name="contacts" duotone className="inline-icon inline-icon--title" />{copy.contacts}</p>
              <div className="safety-contact-list">
                {(profile?.emergency_contacts ?? []).length ? (
                  profile?.emergency_contacts.map((contact) => (
                    <div key={`${contact.name}-${contact.phone}`} className="safety-contact-card">
                      <strong>{contact.name}</strong>
                      <span>{contact.relation}</span>
                      <small>{contact.phone}</small>
                    </div>
                  ))
                ) : (
                  <p className="body-copy">{copy.noContacts}</p>
                )}
              </div>
            </div>

            {safetyMessage ? <p className="body-copy">{safetyMessage}</p> : null}

            {pendingSafetyQueue.length ? (
              <div className="tag-row">
                {pendingSafetyQueue.slice(0, 3).map((item) => (
                  <span key={item.id} className="tag tag--sand">pending {item.kind} {new Date(item.created_at).toLocaleTimeString()}</span>
                ))}
              </div>
            ) : null}

            <div className="mission-actions mission-actions--stack">
              <button className="auth-submit action-button action-button--icon" type="button" onClick={() => void handleSafetyAction("check-in")} disabled={safetyBusy || queueSyncBusy}>
                <UiIcon name="queue" duotone className="action-button__icon" />
                {safetyBusy || queueSyncBusy ? "Syncing..." : copy.sendCheckIn}
              </button>
              <button className="sos-button action-button action-button--icon" type="button" onClick={() => void handleSafetyAction("sos")} disabled={safetyBusy || queueSyncBusy}>
                <UiIcon name="safety" duotone className="action-button__icon" />
                {copy.triggerSos}
              </button>
            </div>

            <div className="safety-panel">
              <p className="safety-panel__title">{copy.reminder}</p>
              <p className="body-copy">{copy.reminderBody}</p>
            </div>
          </aside>
        </div>
      </SectionCard>

      <SectionCard eyebrow={copy.historyEyebrow} title={copy.historyTitle} aside={<StatusPill tone="neutral">History</StatusPill>}>
        <div className="zone-stack">
          {missionHistory.slice(0, 5).map((entry) => (
            <div key={entry.id} className="zone-row">
              <div className={`zone-dot zone-dot--${toneFromStatus(entry.departure_status) === "good" ? "green" : toneFromStatus(entry.departure_status) === "warn" ? "orange" : "red"}`} />
              <div className="zone-row__content">
                <strong>{entry.recommended_zone_label}</strong>
                <span>{entry.selected_species} · {new Date(entry.requested_at).toLocaleString()}</span>
              </div>
              <strong>{entry.mission_score}</strong>
            </div>
          ))}
        </div>
        {safetyEvents.length ? (
          <div className="tag-row">
            {safetyEvents.slice(0, 3).map((event) => (
              <span key={event.id} className="tag tag--sand">{event.event_type} {new Date(event.created_at).toLocaleTimeString()}</span>
            ))}
          </div>
        ) : null}
      </SectionCard>
    </>
  );
}
