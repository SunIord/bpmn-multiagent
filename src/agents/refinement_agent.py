"""
RefinementAgent — quinto agente do pipeline (v2).

Nova estratégia (Sprint 3): em vez de editar XML diretamente (o que causava
corrupção com modelos locais), o agente re-extrai os elementos do processo
e re-modela as sequências usando prompts específicos de refinamento.
Depois sinaliza ao orquestrador que o XML deve ser regenerado pelo BPMNAgent
(determinístico, sem LLM).

Fluxo:
    1. Validação detecta erros → RefinementAgent é acionado
    2. Re-extrai elementos com extraction_refinement.txt (LLM)
    3. Re-modela sequências com modeling_refinement.txt (LLM)
    4. Define state.bpmn_xml = "" (sinaliza que precisa regenerar)
    5. Orquestrador chama BPMNAgent (lxml determinístico)
    6. Validação reavalia → repete se necessário
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List

from src.agents.base_agent import BaseAgent
from src.llm.provider import LLMProviderError, generate
from src.pipeline.state import ProcessModel

logger = logging.getLogger(__name__)

# Padrões para extrair JSON da resposta do LLM
_JSON_FENCE_PATTERN = re.compile(r"```(?:json)?\s*([\s\S]*?)```", re.IGNORECASE)
_MAX_WORDS_ACTIVITY = 10
_LEGAL_TERMS = [
    "artigo", "art.", "lei", "lei nº", "parágrafo", "§", "inciso",
    "prazo", "taxa", "alíquota", "código", "resolução", "portaria",
    "decreto", "instrução normativa", "diário oficial",
]


def _extract_json(raw: str) -> str:
    """
    Extrai o JSON de uma resposta bruta do LLM, removendo markdown residual.

    Args:
        raw: Resposta bruta do LLM.

    Returns:
        String contendo apenas o objeto JSON.
    """
    text = raw.strip()

    # Remove blocos de código markdown
    fence_match = _JSON_FENCE_PATTERN.search(text)
    if fence_match:
        return fence_match.group(1).strip()

    # Tenta localizar o primeiro '{' e o último '}'
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start : end + 1]

    return text


def _format_list(items: List[str], label: str) -> str:
    """Formata uma lista de strings como lista numerada."""
    if not items:
        return f"(nenhum {label})"
    return "\n".join(f"{i + 1}. {item}" for i, item in enumerate(items))


def _format_elements(state: ProcessModel) -> str:
    """Formata os elementos atuais do estado para exibição no prompt."""
    lines = []
    lines.append("Eventos de início:")
    lines.append(_format_list(state.start_events, "start_event"))
    lines.append("\nAtividades:")
    lines.append(_format_list(state.activities, "atividade"))
    lines.append("\nGateways:")
    if state.gateways:
        lines.append(
            _format_list(
                [f"{gw.get('condition', '')} (tipo: {gw.get('type', 'exclusive')})" for gw in state.gateways],
                "gateway",
            )
        )
    else:
        lines.append("(nenhum gateway)")
    lines.append("\nEventos de fim:")
    lines.append(_format_list(state.end_events, "end_event"))
    lines.append("\nAtores:")
    lines.append(_format_list(state.actors, "ator"))
    return "\n".join(lines)


def _format_sequences(state: ProcessModel) -> str:
    """Formata as sequências atuais para exibição no prompt."""
    if not state.sequences:
        return "(nenhuma sequência)"
    result = []
    for i, seq in enumerate(state.sequences, 1):
        cond = seq.get("condition", "")
        cond_str = f" ({cond})" if cond else ""
        result.append(f"{i}. {seq.get('source', '?')} → {seq.get('target', '?')}{cond_str}")
    return "\n".join(result)


def _validate_and_clean_activities(activities: List[str]) -> List[str]:
    """
    Aplica validação semântica pós-extração:
    - Remove atividades com mais de MAX_WORDS_ACTIVITY palavras (trunca)
    - Remove atividades que contenham termos legais
    - Remove duplicatas preservando a ordem
    """
    cleaned = []
    seen = set()
    for name in activities:
        name = name.strip()
        if not name:
            continue
        # Trunca se tiver mais de N palavras
        words = name.split()
        if len(words) > _MAX_WORDS_ACTIVITY:
            name = " ".join(words[:_MAX_WORDS_ACTIVITY])
        # Verifica termos legais
        lower_name = name.lower()
        if any(term in lower_name for term in _LEGAL_TERMS):
            logger.warning(f"RefinementAgent: removendo atividade com termo legal: '{name}'")
            continue
        # Remove duplicatas
        if name.lower() not in seen:
            seen.add(name.lower())
            cleaned.append(name)
    return cleaned


class RefinementAgent(BaseAgent):
    """
    Agente de refinamento iterativo (v2).

    Em vez de editar XML, re-extrai elementos e re-modela sequências
    usando prompts dedicados, deixando a geração de XML para o BPMNAgent
    determinístico.
    """

    def run(self, state: ProcessModel) -> ProcessModel:
        """
        Corrige o processo com base nos erros de validação.

        Args:
            state: ProcessModel com bpmn_xml e validation preenchidos.

        Returns:
            ProcessModel com elementos/sequências corrigidos e bpmn_xml vazio
            (sinalizando que o BPMNAgent deve regenerar).
        """
        errors: list[str] = state.validation.get("errors", [])
        if not errors:
            logger.info("RefinementAgent: sem erros, nada a corrigir.")
            return state

        # Snapshot antes de modificar
        state.snapshot()
        state.iteration += 1
        logger.warning("RefinementAgent: iteração %d com %d erro(s).", state.iteration, len(errors))

        # ── 1. Re-extração de elementos (não bloqueia se falhar) ────────────
        try:
            self._refine_extraction(state, errors)
            logger.info("RefinementAgent: re-extração OK.")
        except Exception as exc:
            logger.error("RefinementAgent: re-extração falhou (%s). Continuando com elementos atuais.", exc)

        # ── 2. Re-modelagem de sequências (sempre executa) ──────────────────
        try:
            self._refine_modeling(state, errors)
            logger.info("RefinementAgent: re-modelagem OK.")
        except Exception as exc:
            logger.error("RefinementAgent: re-modelagem falhou (%s). Continuando sem novas sequências.", exc)

        # ── 3. Invalida XML antigo (orquestrador chamará BPMNAgent) ─────────
        state.bpmn_xml = ""
        logger.info("RefinementAgent: bpmn_xml limpo para regeneração.")
        return state

    # ── Métodos auxiliares ──────────────────────────────────────────────────

    def _refine_extraction(self, state: ProcessModel, errors: List[str]) -> None:
        """Re-extrai elementos usando extraction_refinement.txt."""
        template = self._load_prompt("extraction_refinement.txt")
        prompt = (
            template
            .replace("{TEXTO_ORIGINAL}", state.raw_input)
            .replace("{ERROS}", _format_list(errors, "erro"))
            .replace("{ELEMENTOS_ATUAIS}", _format_elements(state))
        )

        raw = generate(prompt)
        data = json.loads(_extract_json(raw))

        # Atualiza estado com novos elementos (formato antigo: list[str])
        state.activities = [str(a) for a in data.get("activities", [])]
        state.start_events = [str(s) for s in data.get("start_events", [])]
        state.end_events = [str(e) for e in data.get("end_events", [])]
        state.actors = [str(a) for a in data.get("actors", [])]

        # Gateways
        state.gateways = [
            {"type": str(gw.get("type", "exclusive")), "condition": str(gw.get("condition", ""))}
            for gw in data.get("gateways", [])
            if isinstance(gw, dict)
        ]

        # Validação semântica pós-extração
        # state.activities = _validate_and_clean_activities(state.activities)

        # Remove activities que estão como start_events (evita IDs duplicados)
        start_set = set(state.start_events)
        state.activities = [a for a in state.activities if a not in start_set]

        logger.info(
            "RefinementAgent: re-extração concluída — %d atividades, %d start, %d end, %d gateways.",
            len(state.activities), len(state.start_events), len(state.end_events), len(state.gateways),
        )

    def _refine_modeling(self, state: ProcessModel, errors: List[str]) -> None:
        """Re-modela sequências usando modeling_refinement.txt."""
        template = self._load_prompt("modeling_refinement.txt")
        prompt = (
            template
            .replace("{TEXTO_ORIGINAL}", state.raw_input)
            .replace("{ERROS}", _format_list(errors, "erro"))
            .replace("{ELEMENTOS_ATUAIS}", _format_elements(state))
            .replace("{SEQUENCIAS_ATUAIS}", _format_sequences(state))
        )

        raw = generate(prompt)
        logger.debug("RefinementAgent._refine_modeling raw LLM:\n%s", raw)

        try:
            data = json.loads(_extract_json(raw))
        except json.JSONDecodeError as exc:
            logger.error("RefinementAgent: JSON inválido na re-modelagem (%s). raw=%r", exc, raw[:300])
            raise

        raw_sequences = data.get("sequences", [])
        logger.debug("RefinementAgent: raw_sequences extraído: %r", raw_sequences)

        parsed = [
            {
                "source": str(seq.get("source", "")),
                "target": str(seq.get("target", "")),
                "condition": (
                    str(seq.get("condition", ""))
                    if seq.get("condition") and str(seq.get("condition")).lower() != "null"
                    else ""
                ),
            }
            for seq in raw_sequences
            if isinstance(seq, dict) and seq.get("source") and seq.get("target")
        ]

        if not parsed:
            logger.warning(
                "RefinementAgent: LLM retornou sequences vazio — mantendo sequências anteriores. "
                "raw_sequences=%r",
                raw_sequences,
            )
            return

        state.sequences = parsed
        logger.info("RefinementAgent: re-modelagem concluída — %d sequências.", len(state.sequences))
