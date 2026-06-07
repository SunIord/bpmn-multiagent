"""
ExtractionAgent — primeiro agente do pipeline.

Recebe o texto bruto do processo e extrai os elementos semânticos:
atividades, eventos de início/fim, gateways e atores. Produz um
ProcessModel parcialmente preenchido para o ModelingAgent consumir.
"""

from __future__ import annotations

import json
import re

from src.agents.base_agent import BaseAgent
from src.llm.provider import generate
from src.pipeline.state import ProcessModel


def _extract_json(raw: str) -> str:
    """
    Remove markdown residual e isola o objeto JSON da resposta do LLM.

    Modelos menores frequentemente envolvem o JSON em blocos ```json … ```
    mesmo quando instruídos a não fazê-lo. Esta função é tolerante a isso.

    Args:
        raw: Resposta bruta do LLM.

    Returns:
        String contendo apenas o objeto JSON, sem fences de markdown.
    """
    text = raw.strip()

    # Remove blocos de código markdown: ```json ... ``` ou ``` ... ```
    fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fence_match:
        text = fence_match.group(1).strip()
        return text

    # Tenta localizar o primeiro '{' e o último '}' para extrair só o objeto
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        text = text[start : end + 1]

    return text


class ExtractionAgent(BaseAgent):
    """
    Agente de extração semântica de processos de negócio.

    Lê `state.raw_input`, chama o LLM com o prompt de extração e popula
    os campos `activities`, `start_events`, `end_events`, `gateways` e
    `actors` do ProcessModel.
    """

    def run(self, state: ProcessModel) -> ProcessModel:
        """
        Executa a extração de elementos do processo.

        Args:
            state: ProcessModel com `raw_input` preenchido.

        Returns:
            ProcessModel com `activities`, `start_events`, `end_events`,
            `gateways` e `actors` preenchidos.

        Raises:
            ValueError: Se a resposta do LLM não puder ser interpretada como JSON.
        """
        template = self._load_prompt("extraction.txt")
        prompt = template.replace("{TEXTO}", state.raw_input.strip())

        raw_response = generate(prompt, model="qwen2.5")
        json_str = _extract_json(raw_response)

        try:
            data: dict = json.loads(json_str)
        except json.JSONDecodeError as exc:
            preview = raw_response[:300]
            raise ValueError(
                f"ExtractionAgent: JSON inválido retornado pelo LLM.\n"
                f"Erro: {exc}\n"
                f"Resposta (primeiros 300 chars): {preview}"
            ) from exc

        # ── Parse de activities (compatível com ambos os formatos) ──
        raw_activities = data.get("activities", [])
        activities: list[str] = []
        actors_from_activities: list[str] = []

        for item in raw_activities:
            if isinstance(item, str):
                # Formato antigo: string simples
                name = item.strip()
                if name:
                    activities.append(name)
            elif isinstance(item, dict):
                # Formato novo: {"name": "...", "actor": "..."}
                name = str(item.get("name", "")).strip()
                actor = str(item.get("actor", "")).strip()
                if name:
                    activities.append(name)
                    if actor:
                        actors_from_activities.append(actor)

        # ── Parse de start_events e end_events ──
        start_events = [str(s).strip() for s in data.get("start_events", []) if str(s).strip()]
        end_events = [str(e).strip() for e in data.get("end_events", []) if str(e).strip()]

        # ── Remove de activities qualquer item cujo nome já está em start_events ──
        start_event_names = set(start_events)
        activities = [a for a in activities if a not in start_event_names]

        # ── Parse de atores ──
        actors = [str(a).strip() for a in data.get("actors", []) if str(a).strip()]
        # Adiciona atores vindos das atividades
        for a in actors_from_activities:
            if a not in actors:
                actors.append(a)

        # ── Gateways ──
        raw_gateways = data.get("gateways", [])
        gateways = [
            {
                "type": str(gw.get("type", "exclusive")),
                "condition": str(gw.get("condition", "")),
            }
            for gw in raw_gateways
            if isinstance(gw, dict)
        ]

        # ── Popula o estado ──
        state.activities = activities
        state.start_events = start_events
        state.end_events = end_events
        state.actors = actors
        state.gateways = gateways

        return state