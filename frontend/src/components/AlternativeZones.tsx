import type { RecommendationResponse } from "../types";

interface AlternativeZonesProps {
  recommendation: RecommendationResponse | null;
}

export function AlternativeZones({ recommendation }: AlternativeZonesProps) {
  return (
    <div className="alternatives">
      {recommendation?.alternatives.map((zone) => (
        <article key={zone.id} className="alternative-card">
          <div className={`zone-dot zone-dot--${zone.color.toLowerCase()}`} />
          <div className="alternative-card__body">
            <strong>{zone.label}</strong>
            <span>{zone.depth_m}m depth · {zone.overall_score} score</span>
            <small>{zone.key_reason}</small>
          </div>
        </article>
      ))}
    </div>
  );
}

