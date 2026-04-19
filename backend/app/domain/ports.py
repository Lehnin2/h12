from app.models.shared import Port


TARGET_PORTS: list[Port] = [
    Port(
        id="ghannouch",
        name="Port de Ghannouch",
        short_name="Ghannouch",
        lat=33.931,
        lon=10.116,
        risk_bias=0.85,
    ),
    Port(
        id="zarrat",
        name="Port de Zarrat",
        short_name="Zarrat",
        lat=33.679,
        lon=10.495,
        risk_bias=0.32,
    ),
    Port(
        id="teboulbou",
        name="Site de Teboulbou",
        short_name="Teboulbou",
        lat=33.895,
        lon=10.102,
        risk_bias=0.72,
    ),
    Port(
        id="oued_akarit",
        name="Site d'Oued Akarit",
        short_name="Oued Akarit",
        lat=34.017,
        lon=10.020,
        risk_bias=0.38,
    ),
    Port(
        id="mareth",
        name="Port de Mareth",
        short_name="Mareth",
        lat=33.617,
        lon=10.332,
        risk_bias=0.29,
    ),
]

