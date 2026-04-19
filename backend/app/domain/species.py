SPECIES_PROFILES: dict[str, dict[str, float | str]] = {
    "crevette_royale": {
        "preferred_depth_min": 18.0,
        "preferred_depth_max": 42.0,
        "lunar_mode": "late_night",
        "value_score": 0.95,
    },
    "poulpe": {
        "preferred_depth_min": 12.0,
        "preferred_depth_max": 28.0,
        "lunar_mode": "quarter_friendly",
        "value_score": 0.88,
    },
    "rouget": {
        "preferred_depth_min": 10.0,
        "preferred_depth_max": 24.0,
        "lunar_mode": "dawn",
        "value_score": 0.74,
    },
    "sardine": {
        "preferred_depth_min": 8.0,
        "preferred_depth_max": 18.0,
        "lunar_mode": "dark_night",
        "value_score": 0.7,
    },
}

