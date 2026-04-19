PROTECTED_AREAS: list[dict[str, object]] = [
    {"name": "Bahiret El Bibane", "status": "Site Ramsar (2007)", "lat": 33.5, "lon": 11.0},
    {
        "name": "Complexe des Zones Humides de Sebkhret Oum Ez-Zessar et Sebkhret El Grine",
        "status": "Site Ramsar (2013)",
        "lat": 33.7,
        "lon": 10.8,
    },
    {
        "name": "Complexe des Zones Humides des Chott El Guetayate et Sebkhret Dhreia et Oueds Akarit, Rekhama et Meleh",
        "status": "Site Ramsar (2012)",
        "lat": 34.0,
        "lon": 10.0,
    },
    {"name": "Djerba Bin El Ouedian", "status": "Site Ramsar (2007)", "lat": 33.8, "lon": 10.9},
    {"name": "Djerba Guellala", "status": "Site Ramsar (2007)", "lat": 33.7, "lon": 10.9},
    {"name": "Djerba Ras Rmel", "status": "Site Ramsar (2007)", "lat": 33.9, "lon": 10.9},
    {"name": "Lague de Boughrara", "status": "Site Ramsar (2012)", "lat": 33.6, "lon": 10.7},
    {"name": "Iles Kerkennah", "status": "Site Ramsar (2012)", "lat": 34.7, "lon": 11.0},
    {
        "name": "Iles Kneiss",
        "status": "Réserve Naturelle (1993), ASPIM (2001), Site Ramsar (2007)",
        "lat": 34.4,
        "lon": 10.3,
    },
    {"name": "Iles Kuriat", "status": "Proposed AMCP", "lat": 35.8, "lon": 10.9},
]

LICENSE_ALLOWED_GEARS: dict[str, set[str]] = {
    "artisanal": {"ligne", "palangre", "charfia", "nasse", "filet_trémail"},
    "côtier": {
        "ligne",
        "palangre",
        "charfia",
        "nasse",
        "filet_trémail",
        "filets tournants",
        "senne tournante",
    },
    "hauturier": {
        "ligne",
        "palangre",
        "charfia",
        "nasse",
        "filet_trémail",
        "filets tournants",
        "senne tournante",
        "filets traînants",
    },
}

GEAR_BANS: dict[str, str] = {
    "kiss": "Benthic or semi-pelagic trawl gear is prohibited.",
    "senne (hlig et tilla)": "Beach drag nets are prohibited.",
    "armes à feu": "Firearms are prohibited for fishing.",
    "explosifs": "Explosives are prohibited for fishing.",
    "produits chimiques": "Chemical products are prohibited for fishing.",
    "trouble_eau": "Disturbing the water to capture fish is prohibited.",
    "barrages_oueds": "Blocking wadi entrances and exits is prohibited.",
    "gangave_croix_st_andre": "This coral fishing gear is prohibited.",
}

SPECIES_SEASONS: dict[str, dict[str, object]] = {
    "poulpe": {
        "mode": "allowed_only",
        "windows": [("15-10", "15-05")],
        "reference": "Poulpes allowed only from 15-10 to 15-05.",
    },
    "crevette_royale": {
        "mode": "allowed_only",
        "windows": [("16-10", "30-11"), ("15-05", "30-06")],
        "required_gear": "filets traînants",
        "reference": "Crevette du Golfe de Gabès allowed only in campaign windows with trawling gear.",
    },
    "langoustes": {
        "mode": "prohibited",
        "windows": [("15-09", "28-02")],
        "reference": "Langoustes prohibited from 15-09 to 28-02.",
    },
    "homards": {
        "mode": "prohibited",
        "windows": [("15-09", "28-02")],
        "reference": "Homards prohibited from 15-09 to 28-02.",
    },
    "cigales": {
        "mode": "prohibited",
        "windows": [("15-09", "28-02")],
        "reference": "Cigales prohibited from 15-09 to 28-02.",
    },
    "maia": {
        "mode": "prohibited",
        "windows": [("15-09", "28-02")],
        "reference": "Maia prohibited from 15-09 to 28-02.",
    },
}

ZONE_MAP_RULES: list[dict[str, object]] = [
    {
        "id": "light_blue_trawl",
        "image_name": "carte_tunisie_bleu.PNG",
        "target_rgb": (190, 190, 255),
        "tolerance": 70,
        "applies_to_gears": {"filets traînants"},
        "effect": "PROHIBITED",
        "message": "Trawling nets are prohibited in this light-blue legal zone.",
    },
    {
        "id": "blue_fire_fishing",
        "image_name": "carte_tunisie_bleu_foncee.PNG",
        "target_rgb": (40, 40, 200),
        "tolerance": 80,
        "applies_to_gears": {"feu"},
        "effect": "PROHIBITED",
        "message": "Fire fishing is prohibited in this blue zone.",
    },
    {
        "id": "purple_trawl",
        "image_name": "carte_tunisie_mauve.PNG",
        "target_rgb": (170, 50, 170),
        "tolerance": 90,
        "applies_to_gears": {"filets traînants"},
        "effect": "PROHIBITED",
        "message": "Trawling nets are prohibited in this purple control zone.",
    },
    {
        "id": "orange_navigation",
        "image_name": "carte_true_gulf_gabes.PNG",
        "target_rgb": (235, 150, 60),
        "tolerance": 90,
        "applies_to_gears": set(),
        "effect": "RESTRICTED",
        "message": "This Gabès orange corridor is a navigation caution area.",
    },
    {
        "id": "green_control",
        "image_name": "carte_true_gulf_tunis.PNG",
        "target_rgb": (60, 180, 80),
        "tolerance": 90,
        "applies_to_gears": {"filets traînants"},
        "effect": "RESTRICTED",
        "message": "This green corridor is a controlled zone for trawling operations.",
    },
]

