"""
ModelingAgent — segundo agente do pipeline.

Recebe os elementos extraídos pelo ExtractionAgent e define as conexões
(sequenceFlows) entre eles, produzindo o campo `sequences` do ProcessModel.
Não chama o LLM para extrair novos elementos — apenas raciocina sobre o fluxo.
"""

from __future__ import annotations

import json
import re
import difflib

from src.agents.base_agent import BaseAgent
from src.llm.provider import generate
from src.pipeline.state import ProcessModel


def _extract_json(raw: str) -> str:
    """
    Isola o objeto JSON da resposta do LLM, removendo markdown residual.

    Args:
        raw: Resposta bruta do LLM.

    Returns:
        String contendo apenas o objeto JSON.
    """
    text = raw.strip()

    fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fence_match:
        return fence_match.group(1).strip()

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start : end + 1]

    return text


def _format_list(items: list[str]) -> str:
    """Formata uma lista de strings como itens numerados para o prompt."""
    if not items:
        return "(nenhum)"
    return "\n".join(f"  - {item}" for item in items)


def _format_gateways(gateways: list[dict[str, str]]) -> str:
    """Formata a lista de gateways para o prompt."""
    if not gateways:
        return "(nenhum)"
    return "\n".join(
        f"  - \"{gw.get('condition', '')}\" (tipo: {gw.get('type', 'exclusive')})"
        for gw in gateways
    )


def _fuzzy_match(name: str, candidates: list[str], cutoff: float = 0.6) -> str | None:
    if not candidates:
        return None
    if name in candidates:
        return name
    matches = difflib.get_close_matches(name, candidates, n=1, cutoff=cutoff)
    return matches[0] if matches else None


class ModelingAgent(BaseAgent):
    """
    Agente de modelagem de fluxo de processo.

    Lê os elementos do ProcessModel (preenchidos pelo ExtractionAgent),
    monta um prompt estruturado com esses dados + o texto original, e
    chama o LLM para definir as sequências de fluxo entre os elementos.
    """

    def run(self, state: ProcessModel) -> ProcessModel:
        """
        Define as sequências de fluxo entre os elementos do processo.

        Args:
            state: ProcessModel com `activities`, `start_events`, `end_events`,
                   `gateways` e `raw_input` preenchidos pelo ExtractionAgent.

        Returns:
            ProcessModel com o campo `sequences` preenchido.

        Raises:
            ValueError: Se a resposta do LLM não puder ser interpretada como JSON.
        """
        template = self._load_prompt("modeling.txt")

        prompt = (
            template
            .replace("{TEXTO_ORIGINAL}", state.raw_input.strip())
            .replace("{START_EVENTS}", _format_list(state.start_events))
            .replace("{ACTIVITIES}", _format_list([a["name"] for a in state.activities]))
            .replace("{GATEWAYS}", _format_gateways(state.gateways))
            .replace("{END_EVENTS}", _format_list(state.end_events))
        )

        raw_response = generate(prompt)
        json_str = _extract_json(raw_response)

        try:
            data: dict = json.loads(json_str)
        except json.JSONDecodeError as exc:
            preview = raw_response[:300]
            raise ValueError(
                f"ModelingAgent: JSON inválido retornado pelo LLM.\n"
                f"Erro: {exc}\n"
                f"Resposta (primeiros 300 chars): {preview}"
            ) from exc

        raw_sequences = data.get("sequences", [])
        
        activity_names = [a["name"] for a in state.activities]
        all_elements = (
            state.start_events + activity_names + 
            [gw.get("condition", "") for gw in state.gateways] + 
            state.end_events
        )
        
        normalized_sequences = []
        for seq in raw_sequences:
            if not isinstance(seq, dict):
                continue
            source = str(seq.get("source", ""))
            target = str(seq.get("target", ""))
            if not source or not target:
                continue
            
            matched_source = _fuzzy_match(source, all_elements)
            matched_target = _fuzzy_match(target, all_elements)
            
            normalized_sequences.append({
                "source": matched_source or source,
                "target": matched_target or target,
                "condition": (
                    str(seq["condition"])
                    if seq.get("condition") and str(seq.get("condition")).lower() != "null"
                    else ""
                ),
            })
        
        state.sequences = [
            seq for seq in normalized_sequences
            if seq["source"] in all_elements and seq["target"] in all_elements
        ]

        return state