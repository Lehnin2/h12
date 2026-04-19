from __future__ import annotations

import base64
from typing import Iterable

import requests

from app.core.config import settings
from app.models.profile import EmergencyContact


class NotificationService:
    twilio_base_url = "https://api.twilio.com/2010-04-01"

    def sms_ready(self) -> bool:
        return (
            settings.sms_notifications_enabled
            and bool(settings.twilio_account_sid)
            and bool(settings.twilio_auth_token)
            and bool(settings.twilio_sms_from_number)
        )

    def _dedupe_numbers(self, numbers: Iterable[str]) -> list[str]:
        unique: list[str] = []
        seen: set[str] = set()
        for number in numbers:
            cleaned = "".join(str(number).strip().split())
            if cleaned and cleaned not in seen:
                unique.append(cleaned)
                seen.add(cleaned)
        return unique

    def _recipient_numbers(self, contacts: list[EmergencyContact]) -> list[str]:
        profile_numbers = [contact.phone for contact in contacts if contact.phone]
        return self._dedupe_numbers([*profile_numbers, *settings.twilio_alert_to_numbers])

    def send_sms(self, to_number: str, body: str) -> dict[str, str]:
        if not self.sms_ready():
            return {
                "status": "disabled",
                "to": to_number,
                "detail": "SMS notifications are disabled or Twilio settings are incomplete.",
            }

        account_sid = settings.twilio_account_sid or ""
        auth_token = settings.twilio_auth_token or ""
        auth_bytes = f"{account_sid}:{auth_token}".encode("utf-8")
        auth_header = base64.b64encode(auth_bytes).decode("ascii")
        try:
            response = requests.post(
                f"{self.twilio_base_url}/Accounts/{account_sid}/Messages.json",
                data={
                    "To": to_number,
                    "From": settings.twilio_sms_from_number,
                    "Body": body,
                },
                headers={"Authorization": f"Basic {auth_header}"},
                timeout=10,
            )
        except requests.RequestException as exc:
            return {
                "status": "failed",
                "to": to_number,
                "detail": str(exc),
            }
        if response.status_code >= 400:
            detail = response.text[:240]
            return {
                "status": "failed",
                "to": to_number,
                "detail": detail or f"Twilio HTTP {response.status_code}",
            }
        payload = response.json()
        return {
            "status": payload.get("status", "queued"),
            "to": to_number,
            "sid": payload.get("sid", ""),
        }

    def send_safety_broadcast(
        self,
        contacts: list[EmergencyContact],
        body: str,
    ) -> list[dict[str, str]]:
        recipients = self._recipient_numbers(contacts)
        if not recipients:
            return [
                {
                    "status": "skipped",
                    "to": "",
                    "detail": "No emergency recipients configured for SMS alerts.",
                }
            ]
        return [self.send_sms(number, body) for number in recipients]


notification_service = NotificationService()
