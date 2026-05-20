"""
Orquestrador do pipeline multiagente com LangGraph.

Controla a execução dos agentes usando um grafo de estados.
Fluxo (Sprint 2):
    extract → model → generate → validate ─── válido ──────────► END
                                       │
                                    inválido + iteration < 3
                                       │
                                     refine
                                       │
                                       └──► validate (loop)
                                       │
                                    inválido + iteration >= 3
                                       │
                                       └──► END (com erros)

O RefinementAgent corrige o XML diretamente, sem reexecutar o BPMNAgent.
"""

from __future__ import annotations

import logging
from typing import TypedDict, Any

from langgraph.graph import END, StateGraph

from src.agents.bpmn_agent import BPMNAgent
from src.agents.extraction_agent import ExtractionAgent
from src.agents.modeling_agent import ModelingAgent
from src.agents.refinement_agent import RefinementAgent
from src.agents.validation_agent import ValidationAgent
from src.pipeline.state import ProcessModel

logger = logging.getLogger(__name__)

MAX_ITERATIONS = 3


def _should_refine(state: ProcessModel) -> str:
    """Decide o próximo passo após a validação."""
    is_valid = state.validation.get("is_valid", False)
    iteration = state.iteration

    if is_valid or iteration >= MAX_ITERATIONS:
        logger.info(
            "Pipeline: ciclo de refinamento encerrado (válido=%s, iteração=%d).",
            is_valid,
            iteration,
        )
        return "end"

    logger.info(
        "Pipeline: BPMN inválido — encaminhando para RefinementAgent (iteração %d).",
        iteration,
    )
    return "refine"


def run_pipeline(text: str, input_type: str = "freetext") -> ProcessModel:
    """
    Executa o pipeline multiagente completo sobre um texto de processo.
    """
    state = ProcessModel(raw_input=text, input_type=input_type)

    extraction = ExtractionAgent()
    modeling = ModelingAgent()
    bpmn_gen = BPMNAgent()
    validation = ValidationAgent()
    refinement = RefinementAgent()

    try:
        # Etapas obrigatórias (executam uma única vez)
        logger.info("Pipeline: iniciando ExtractionAgent.")
        state = extraction.run(state)

        logger.info("Pipeline: iniciando ModelingAgent.")
        state = modeling.run(state)

        logger.info("Pipeline: iniciando BPMNAgent.")
        state = bpmn_gen.run(state)

        # Ciclo de validação e refinamento
        logger.info("Pipeline: iniciando ValidationAgent.")
        state = validation.run(state)

        while not state.validation.get("is_valid") and state.iteration < MAX_ITERATIONS:
            logger.warning(
                "Pipeline: BPMN inválido — encaminhando para RefinementAgent (iteração %d).",
                state.iteration,
            )
            state = refinement.run(state)
            logger.info("Pipeline: reavaliando com ValidationAgent.")
            state = validation.run(state)

        if state.validation.get("is_valid"):
            logger.info("Pipeline: concluído com BPMN válido.")
        else:
            logger.warning(
                "Pipeline: concluído com BPMN inválido após %d tentativas — %d erro(s).",
                state.iteration,
                len(state.validation.get("errors", [])),
            )

    except Exception as exc:
        raise RuntimeError(
            f"Erro durante a execução do pipeline multiagente: {exc}"
        ) from exc

    return state