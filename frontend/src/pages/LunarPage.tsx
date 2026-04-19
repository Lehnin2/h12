import { useAppContext } from "../app/AppContext";
import { SectionCard } from "../components/SectionCard";
import { StatusPill } from "../components/StatusPill";
import { VoiceAssistButton } from "../components/VoiceAssistButton";
import { uiCopy } from "../lib/uiCopy";
import { buildArabicLunarBriefing } from "../lib/voiceBriefings";

export function LunarPage() {
  const { lunar, uiLanguage } = useAppContext();
  const copy = uiCopy[uiLanguage].lunar;

  return (
    <SectionCard
      eyebrow={copy.eyebrow}
      title={`${lunar?.phase_name ?? copy.loading} · ${lunar?.illumination_pct ?? "--"}%`}
      aside={
        <div className="section-card__controls">
          <VoiceAssistButton
            getText={() => buildArabicLunarBriefing({ lunar })}
          />
          <StatusPill tone="neutral">{copy.offline}</StatusPill>
        </div>
      }
    >
      <p className="body-copy">{lunar?.best_window}</p>
      <ul className="bullet-list">
        {lunar?.species_guidance.map((guide, index) => <li key={`${index}-${guide}`}>{guide}</li>)}
      </ul>
      <div className="tag-row">
        <span className="tag">{copy.rise} {lunar?.moonrise ?? "--"}</span>
        <span className="tag">{copy.set} {lunar?.moonset ?? "--"}</span>
      </div>
      <div className="forecast-row">
        {lunar?.forecast.map((day) => (
          <article key={day.day_label} className="forecast-card">
            <span>{day.day_label}</span>
            <strong>{day.illumination_pct}%</strong>
            <small>{day.phase_name}</small>
          </article>
        ))}
      </div>
    </SectionCard>
  );
}
