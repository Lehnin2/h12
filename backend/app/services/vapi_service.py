import requests
from app.core.config import settings

def trigger_vapi_sos_call(boat_name: str, lat: float, lon: float, message: str, phone_number: str) -> bool:
    """
    Triggers an outbound Vapi AI call using the user-provided snippet.
    Maps maritime SOS data into the expected Vapi variables.
    """
    if not settings.vapi_api_key or not settings.vapi_assistant_id or not settings.vapi_phone_number_id:
        print("⚠️ Vapi configuration missing. Skipping AI voice call.")
        return False

    url = "https://api.vapi.ai/call"
    headers = {
        "Authorization": f"Bearer {settings.vapi_api_key}",
        "Content-Type": "application/json"
    }

    # The user provided Vapi assistant expects symbol, price, score, reasoning, and risk.
    # We map our maritime SOS parameters into these slots.
    assistant_overrides = {
        "variableValues": {
            "symbol": str(boat_name),
            "price": str(lat),
            "score": str(int(lon)),
            "reasoning": str(message),
            "risk": "SOS CRITICAL"
        }
    }

    payload = {
        "assistantId": settings.vapi_assistant_id,
        "phoneNumberId": settings.vapi_phone_number_id,
        "customer": {"number": phone_number},
        "assistantOverrides": assistant_overrides
    }

    try:
        print(f"☎️ Dialing {phone_number} for {boat_name} SOS...")
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        if response.status_code == 201:
            print("✅ Vapi SOS Call Initiated!")
            return True
        else:
            print(f"❌ Vapi Error: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Vapi Connection Error: {e}")
        return False
