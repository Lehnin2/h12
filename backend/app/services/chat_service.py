from __future__ import annotations

import json
from typing import Any

import requests

from app.core.config import settings
from app.models.chat import ChatMessageRequest, ChatMessageResponse, ChatToolSnapshot
from app.models.profile import FishermanProfilePublic
from app.services.mission_service import mission_service
from app.services.report_service import report_service


class ChatService:
    def _suggested_prompts(self, page: str) -> list[str]:
        if page == "route":
            return [
                "Pourquoi cette route ?",
                "Où est le risque principal ?",
                "Le fuel est-il suffisant ?",
            ]
        if page == "safety":
            return [
                "Puis-je sortir maintenant ?",
                "Que faire avant départ ?",
                "Explique la safety simplement",
            ]
        if page == "lunar":
            return [
                "Le meilleur moment aujourd'hui ?",
                "La lune favorise quelle espèce ?",
                "Explique-moi la fenêtre de pêche",
            ]
        if page == "profile":
            return [
                "Explique mes données mission",
                "Que disent les pêcheurs ?",
                "Pourquoi la météo compte ici ?",
            ]
        return [
            "Pourquoi cette zone ?",
            "Cette zone est-elle légale ?",
            "Puis-je partir maintenant ?",
            "Que disent les pêcheurs ?",
        ]

    def _build_tool_snapshots(
        self,
        payload: ChatMessageRequest,
        current_user: FishermanProfilePublic,
    ) -> tuple[list[ChatToolSnapshot], dict[str, Any]]:
        message = payload.message.lower()
        briefing = mission_service.build_briefing_for_user(current_user)
        report_feed = report_service.feed(72)

        tools: list[ChatToolSnapshot] = []
        tool_payload: dict[str, Any] = {}

        def add_tool(name: str, summary: str, data: Any) -> None:
            tools.append(ChatToolSnapshot(tool_name=name, summary=summary))
            tool_payload[name] = data

        add_tool(
            "mission_briefing",
            f"Best zone is {briefing.recommendation.best_zone.label} with departure status {briefing.departure_decision.status}.",
            {
                "best_zone": briefing.recommendation.best_zone.model_dump(),
                "advisory": briefing.recommendation.advisory,
                "departure_decision": briefing.departure_decision.model_dump(),
            },
        )

        page = payload.page.lower()
        if page in {"route", "heatmap"} or any(word in message for word in ["route", "fuel", "distance", "path", "trajet"]):
            add_tool(
                "route_summary",
                f"Route readiness is {briefing.route.route_readiness} over {briefing.route.optimized_distance_km} km with {briefing.route.estimated_fuel_l} L expected.",
                briefing.route.model_dump(),
            )

        if page in {"safety", "heatmap"} or any(word in message for word in ["safe", "safety", "danger", "sos", "khrouj", "sortir"]):
            add_tool(
                "safety_status",
                f"Safety status is {briefing.safety.departure_status} with score {briefing.safety.safety_score}.",
                briefing.safety.model_dump(),
            )

        if page in {"heatmap", "profile"} or any(word in message for word in ["legal", "law", "regulation", "licence", "license"]):
            add_tool(
                "regulation_status",
                f"Regulation status at the best zone is {briefing.regulation.overall_status}.",
                briefing.regulation.model_dump(),
            )

        if any(word in message for word in ["weather", "wind", "wave", "sea", "meteo", "météo", "baher"]):
            add_tool(
                "weather_status",
                f"Sea condition is {briefing.weather.current.condition} with fishing score {briefing.weather.current.fishing_score}.",
                briefing.weather.model_dump(),
            )

        if any(word in message for word in ["pollution", "toxic", "eau", "dirty", "plume"]):
            add_tool(
                "pollution_status",
                f"Pollution index at the best zone is {briefing.recommendation.best_zone.pollution_index}/100.",
                {
                    "zone_pollution_index": briefing.recommendation.best_zone.pollution_index,
                    "zone_pollution_source": briefing.recommendation.best_zone.pollution_source,
                    "zone_advisory": briefing.recommendation.best_zone.key_reason,
                },
            )

        if page in {"lunar"} or any(word in message for word in ["moon", "lunar", "timing", "lune"]):
            add_tool(
                "lunar_status",
                f"Lunar phase is {briefing.lunar.phase_name} with best window {briefing.lunar.best_window}.",
                briefing.lunar.model_dump(),
            )

        if any(word in message for word in ["others", "alternative", "else", "zone", "pourquoi", "why"]):
            add_tool(
                "alternative_zones",
                f"There are {len(briefing.recommendation.alternatives)} alternative zones.",
                [zone.model_dump() for zone in briefing.recommendation.alternatives],
            )

        if any(word in message for word in ["reports", "fishermen", "community", "shared", "signalement"]):
            add_tool(
                "community_reports",
                f"There are {len(report_feed.recent_reports)} recent community reports in the last 72 hours.",
                report_feed.model_dump(),
            )

        if not any(tool.tool_name == "route_summary" for tool in tools) and page == "route":
            add_tool(
                "route_summary",
                f"Route readiness is {briefing.route.route_readiness} over {briefing.route.optimized_distance_km} km with {briefing.route.estimated_fuel_l} L expected.",
                briefing.route.model_dump(),
            )

        return tools, tool_payload

    def _fallback_answer(
        self,
        payload: ChatMessageRequest,
        tools: list[ChatToolSnapshot],
        tool_payload: dict[str, Any],
    ) -> ChatMessageResponse:
        mission = tool_payload.get("mission_briefing", {})
        route = tool_payload.get("route_summary", {})
        safety = tool_payload.get("safety_status", {})
        best_zone = mission.get("best_zone", {})
        departure = mission.get("departure_decision", {})

        answer = (
            f"La meilleure zone actuelle est {best_zone.get('label', 'en cours de calcul')}. "
            f"Le statut de départ est {departure.get('status', 'en évaluation')}. "
            f"Le conseil principal est: {mission.get('advisory', 'attends la confirmation mission')}."
        )
        if route:
            answer += f" La route prévue fait {route.get('optimized_distance_km', '--')} km pour environ {route.get('estimated_fuel_l', '--')} L."
        if safety:
            answer += f" Le score safety est {safety.get('safety_score', '--')}."

        answer_ar = (
            f"أفضل منطقة توة هي {best_zone.get('label', 'مازالت تتحسب')}. "
            f"وضعية الخروج {departure.get('status', 'جاري التقييم')}. "
            f"الخلاصة: {mission.get('advisory', 'استنى تأكيد المهمة')}."
        )

        return ChatMessageResponse(
            answer=answer,
            answer_ar=answer_ar,
            voice_text_ar=answer_ar,
            tools_used=tools,
            suggested_prompts=self._suggested_prompts(payload.page),
            used_llm=False,
            page=payload.page,
        )

    def _call_groq(
        self,
        payload: ChatMessageRequest,
        tools: list[ChatToolSnapshot],
        tool_payload: dict[str, Any],
    ) -> ChatMessageResponse | None:
        if not settings.groq_api_key:
            return None

        system_prompt = (
            "You are Guardian of the Gulf, a maritime mission assistant for artisanal fishermen in Gabes. "
            "Answer using only the provided backend tools. Be concise, practical, and decision-first. "
            "Never invent laws, routes, weather, or risks. If data is uncertain, say so. "
            "Return valid JSON with keys: answer, answer_ar, suggested_prompts."
        )
        tool_context = json.dumps(tool_payload, ensure_ascii=False)
        history = [{"role": turn.role, "content": turn.content} for turn in payload.history[-6:]]
        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "system",
                "content": f"Tool context:\n{tool_context}",
            },
            *history,
            {"role": "user", "content": payload.message},
        ]

        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.groq_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.groq_model,
                "messages": messages,
                "temperature": 0.2,
                "response_format": {"type": "json_object"},
            },
            timeout=25,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        parsed = json.loads(content)
        answer = parsed.get("answer")
        answer_ar = parsed.get("answer_ar")
        prompts = parsed.get("suggested_prompts") or self._suggested_prompts(payload.page)
        if not isinstance(prompts, list):
            prompts = self._suggested_prompts(payload.page)
        if not answer:
            return None
        return ChatMessageResponse(
            answer=answer,
            answer_ar=answer_ar,
            voice_text_ar=answer_ar,
            tools_used=tools,
            suggested_prompts=[str(item) for item in prompts[:4]],
            used_llm=True,
            page=payload.page,
        )

    def reply(
        self,
        payload: ChatMessageRequest,
        current_user: FishermanProfilePublic,
    ) -> ChatMessageResponse:
        tools, tool_payload = self._build_tool_snapshots(payload, current_user)
        try:
            llm_response = self._call_groq(payload, tools, tool_payload)
            if llm_response is not None:
                return llm_response
        except Exception:
            pass
        return self._fallback_answer(payload, tools, tool_payload)


chat_service = ChatService()
