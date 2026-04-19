import os
from pathlib import Path

from pydantic import BaseModel, Field


def _load_env_file() -> None:
    env_path = Path(__file__).resolve().parents[2] / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("\"'")
        if key and key not in os.environ:
            os.environ[key] = value


_load_env_file()


class Settings(BaseModel):
    app_name: str = "Guardian of the Gulf API"
    version: str = "0.1.0"
    api_prefix: str = "/api/v1"
    groq_api_key: str | None = os.getenv("GROQ_API_KEY")
    groq_model: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    stormglass_api_key: str | None = os.getenv("STORMGLASS_API_KEY")
    copernicusmarine_username: str | None = os.getenv("COPERNICUSMARINE_SERVICE_USERNAME")
    copernicusmarine_password: str | None = os.getenv("COPERNICUSMARINE_SERVICE_PASSWORD")
    twilio_account_sid: str | None = os.getenv("TWILIO_ACCOUNT_SID")
    twilio_auth_token: str | None = os.getenv("TWILIO_AUTH_TOKEN")
    twilio_sms_from_number: str | None = os.getenv("TWILIO_SMS_FROM_NUMBER")
    twilio_whatsapp_from_number: str | None = os.getenv("TWILIO_WHATSAPP_FROM_NUMBER")
    
    vapi_api_key: str | None = os.getenv("VAPI_API_KEY", "9d15fa78-9a58-48da-b315-7d85d4a5e4e9")
    vapi_assistant_id: str | None = os.getenv("VAPI_ASSISTANT_ID", "5c347374-19a5-40ca-ab52-48bf3a8e0d19")
    vapi_phone_number_id: str | None = os.getenv("VAPI_PHONE_NUMBER_ID", "567ad886-d125-49e6-875b-2bb365130f3f")
    vapi_emergency_number: str | None = os.getenv("VAPI_EMERGENCY_NUMBER", "+21621750868")

    sms_notifications_enabled: bool = os.getenv("SMS_NOTIFICATIONS_ENABLED", "false").lower() == "true"
    twilio_alert_to_numbers: list[str] = Field(
        default_factory=lambda: [
            item.strip()
            for item in os.getenv("TWILIO_ALERT_TO_NUMBERS", "").split(",")
            if item.strip()
        ]
    )
    copernicus_sst_dataset_id: str = os.getenv(
        "COPERNICUS_SST_DATASET_ID",
        "SST_MED_SST_L4_NRT_OBSERVATIONS_010_004_a_V2",
    )
    copernicus_chl_dataset_id: str = os.getenv(
        "COPERNICUS_CHL_DATASET_ID",
        "cmems_obs-oc_med_bgc-plankton_nrt_l3-multi-1km_P1D",
    )
    copernicus_turbidity_dataset_id: str = os.getenv(
        "COPERNICUS_TURBIDITY_DATASET_ID",
        "cmems_obs_oc_med_bgc_tur-spm-chl_nrt_l4-hr-mosaic_P1D-m",
    )
    copernicus_salinity_dataset_id: str = os.getenv(
        "COPERNICUS_SALINITY_DATASET_ID",
        "cmems_mod_med_phy-sal_anfc_4.2km-2D_PT1H-m",
    )
    copernicus_currents_dataset_id: str = os.getenv(
        "COPERNICUS_CURRENTS_DATASET_ID",
        "cmems_mod_med_phy-cur_anfc_4.2km-2D_PT1H-m",
    )
    sonar_model_path: str = os.getenv(
        "SONAR_MODEL_PATH",
        str(Path(__file__).resolve().parents[3] / "sonar_best_model.pkl"),
    )
    sonar_scaler_path: str = os.getenv(
        "SONAR_SCALER_PATH",
        str(Path(__file__).resolve().parents[3] / "sonar_scaler.pkl"),
    )
    sonar_empirical_max_energy: float = float(
        os.getenv("SONAR_EMPIRICAL_MAX_ENERGY", "19.0")
    )
    sqlite_db_path: str = str(
        Path(__file__).resolve().parents[2] / "data" / "guardian_of_gulf.db"
    )
    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:4173",
            "http://127.0.0.1:4173",
        ]
    )
    admin_seed_email: str = os.getenv("ADMIN_SEED_EMAIL", "admin@gulf.local").strip().lower()
    admin_seed_password: str = os.getenv("ADMIN_SEED_PASSWORD", "GuardianAdmin123!")
    admin_seed_enabled: bool = os.getenv("ADMIN_SEED_ENABLED", "true").lower() == "true"
    admin_emails: list[str] = Field(
        default_factory=lambda: [
            item.strip().lower()
            for item in os.getenv("ADMIN_EMAILS", "admin@gulf.local").split(",")
            if item.strip()
        ]
    )


settings = Settings()


def is_admin_email(email: str) -> bool:
    normalized = email.strip().lower()
    return normalized in set(settings.admin_emails) | {settings.admin_seed_email}
