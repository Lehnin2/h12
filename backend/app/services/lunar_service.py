from datetime import UTC, datetime, timedelta

from app.models.lunar import LunarForecastDay, LunarResponse


class LunarService:
    phase_sequence = [
        ("New Moon", 12.0, 5),
        ("Waxing Crescent", 23.0, 4),
        ("First Quarter", 39.0, 4),
        ("Waxing Gibbous", 61.0, 3),
        ("Full Moon", 91.0, 2),
        ("Waning Gibbous", 74.0, 3),
        ("Last Quarter", 48.0, 4),
    ]

    def get_today(self, species: str) -> LunarResponse:
        now = datetime.now(UTC)
        cycle_index = now.timetuple().tm_yday % len(self.phase_sequence)
        phase_name, illumination_pct, rating = self.phase_sequence[cycle_index]

        if species == "sardine" and illumination_pct < 30:
            best_window = "Night fishing window is excellent"
            species_guidance = [
                "Sardine schools are more active in darker surface conditions.",
                "Keep fast near-surface routes and short drift loops.",
            ]
        elif species == "crevette_royale":
            best_window = "Late night to dawn is favorable"
            species_guidance = [
                "Crevette royale benefits from moderate lunar cover and deeper lanes.",
                "Favor calm zones with 18-40m depth.",
            ]
        else:
            best_window = "Dawn and early morning remain the safest productive window"
            species_guidance = [
                "Octopus and rouget perform best with stable conditions and moderate illumination.",
                "Combine lunar timing with low wave sectors.",
            ]

        forecast: list[LunarForecastDay] = []
        for offset in range(4):
            idx = (cycle_index + offset) % len(self.phase_sequence)
            label, illum, day_rating = self.phase_sequence[idx]
            forecast.append(
                LunarForecastDay(
                    day_label=(now + timedelta(days=offset)).strftime("%a %d %b"),
                    phase_name=label,
                    illumination_pct=illum,
                    fishing_rating=day_rating,
                )
            )

        return LunarResponse(
            phase_name=phase_name,
            illumination_pct=illumination_pct,
            moonrise="20:14",
            moonset="06:32",
            best_window=best_window,
            species_guidance=species_guidance,
            forecast=forecast,
        )

    def lunar_factor(self, species: str) -> float:
        today = self.get_today(species)
        illumination = today.illumination_pct
        if species == "sardine":
            return 1.16 if illumination < 30 else 0.91
        if species == "crevette_royale":
            return 1.08 if 20 <= illumination <= 70 else 0.96
        return 1.1 if 30 <= illumination <= 55 else 0.98


lunar_service = LunarService()

