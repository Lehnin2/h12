from pydantic import BaseModel


class SatelliteObservationResponse(BaseModel):
    lat: float
    lon: float
    source: str
    status: str
    is_live: bool
    timestamp: str
    sst_c: float | None = None
    chlorophyll_mg_m3: float | None = None
    salinity_psu: float | None = None
    turbidity_fnu: float | None = None
    suspended_matter_mg_l: float | None = None
    current_speed_kmh: float | None = None
    current_direction_deg: float | None = None
    productivity_index: int
    turbidity_risk: str
    advisory: str


class SatelliteZoneResponse(BaseModel):
    zone_id: str
    zone_label: str
    observation: SatelliteObservationResponse
