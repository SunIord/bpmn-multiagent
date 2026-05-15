"""
ProcessModel — estado intermediário compartilhado entre todos os agentes.

Contrato de dados central do pipeline (ADR-004). Cada agente lê os campos
preenchidos pelos agentes anteriores e escreve nos seus próprios campos.
O objeto cresce incrementalmente ao longo do pipeline.

Fluxo de preenchimento:
    Início          → raw_input, input_type
    ExtractionAgent → activities, start_events, end_events, gateways, actors
    ModelingAgent   → sequences
    BPMNAgent       → bpmn_xml
    ValidationAgent → validation
    RefinementAgent → corrige campos específicos + salva snapshot em history
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any


def _default_validation() -> dict[str, Any]:
    return {"is_valid": False, "errors": [], "warnings": []}


@dataclass
class ProcessModel:
    """
    Estado completo de uma execução do pipeline multiagente.

    Todos os campos com tipos mutáveis usam `field(default_factory=...)`
    para evitar compartilhamento de estado entre instâncias.
    """

    # ── Metadados ─────────────────────────────────────────────────────────────
    process_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    input_type: str = "freetext"   # freetext | structured | noisy
    iteration: int = 0

    # ── Input bruto ───────────────────────────────────────────────────────────
    raw_input: str = ""

    # ── Preenchido pelo ExtractionAgent ───────────────────────────────────────
    activities: list[str] = field(default_factory=list)
    start_events: list[str] = field(default_factory=list)
    end_events: list[str] = field(default_factory=list)
    gateways: list[dict[str, str]] = field(default_factory=list)
    # Cada gateway: {"type": "exclusive"|"parallel"|"inclusive", "condition": "..."}

    actors: list[str] = field(default_factory=list)

    # ── Preenchido pelo ModelingAgent ─────────────────────────────────────────
    sequences: list[dict[str, str]] = field(default_factory=list)
    # Cada sequence: {"source": "...", "target": "...", "condition": "..."}
    # "condition" é opcional — presente apenas em arestas saindo de gateways.

    # ── Preenchido pelo BPMNAgent ─────────────────────────────────────────────
    bpmn_xml: str = ""

    # ── Preenchido pelo ValidationAgent ──────────────────────────────────────
    validation: dict[str, Any] = field(default_factory=_default_validation)
    # Estrutura: {"is_valid": bool, "errors": list[str], "warnings": list[str]}

    # ── Histórico de iterações (loop de refinamento) ──────────────────────────
    history: list[dict[str, Any]] = field(default_factory=list)

    # ── Métodos utilitários ───────────────────────────────────────────────────

    def snapshot(self) -> dict[str, Any]:
        """
        Registra o estado atual no histórico e retorna o snapshot.

        Deve ser chamado pelo RefinementAgent antes de qualquer modificação,
        para permitir rastreabilidade de cada iteração do ciclo de correção.

        Returns:
            Dicionário com o estado atual completo.
        """
        snap = self.to_dict()
        self.history.append(snap)
        return snap

    def to_dict(self) -> dict[str, Any]:
        """
        Serializa o estado atual como dicionário.

        Returns:
            Todos os campos do ProcessModel como dict Python.
        """
        return {
            "process_id": self.process_id,
            "input_type": self.input_type,
            "iteration": self.iteration,
            "raw_input": self.raw_input,
            "activities": list(self.activities),
            "start_events": list(self.start_events),
            "end_events": list(self.end_events),
            "gateways": [dict(gw) for gw in self.gateways],
            "actors": list(self.actors),
            "sequences": [dict(sq) for sq in self.sequences],
            "bpmn_xml": self.bpmn_xml,
            "validation": dict(self.validation),
            "history": self.history,
        }

    def is_complete(self) -> bool:
        """
        Verifica se o estado tem o mínimo necessário para gerar BPMN.

        Returns:
            True se há pelo menos uma atividade, um start e um end event.
        """
        return (
            len(self.activities) > 0
            and len(self.start_events) > 0
            and len(self.end_events) > 0
        )

    def is_valid(self) -> bool:
        """Atalho para verificar o resultado da validação."""
        return bool(self.validation.get("is_valid", False))