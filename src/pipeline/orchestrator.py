"""
Orquestrador do pipeline multiagente.

Controla a execução dos agentes em fluxo linear e sequencial.
Fluxo atual (Sprint 2):
    extract → model → generate → validate → END

O ValidationAgent é executado após a geração do BPMN. Se a validação
falhar, o estado é retornado com os erros registrados em
`state.validation` — o pipeline não quebra; o chamador decide o que fazer.
O loop de refinamento (RefinementAgent) será adicionado na Sprint 2.
"""

from __future__ import annotations

import logging

from src.agents.bpmn_agent import BPMNAgent
from src.agents.extraction_agent import ExtractionAgent
from src.agents.modeling_agent import ModelingAgent
from src.agents.validation_agent import ValidationAgent
from src.pipeline.state import ProcessModel

logger = logging.getLogger(__name__)


def run_pipeline(text: str, input_type: str = "freetext") -> ProcessModel:
    """
    Executa o pipeline multiagente completo sobre um texto de processo.

    Args:
        text:       Descrição do processo em linguagem natural.
        input_type: Tipo de entrada — "freetext", "structured" ou "noisy".

    Returns:
        ProcessModel com todos os campos preenchidos, incluindo
        `bpmn_xml` e `validation`. Se a validação falhar, o estado
        ainda é retornado com `validation.is_valid == False` e os
        erros em `validation.errors`.

    Raises:
        RuntimeError: Se qualquer agente lançar uma exceção não tratada.
    """
    state = ProcessModel(raw_input=text, input_type=input_type)

    extraction = ExtractionAgent()
    modeling = ModelingAgent()
    bpmn_gen = BPMNAgent()
    validation = ValidationAgent()

    try:
        logger.info("Pipeline: iniciando ExtractionAgent.")
        state = extraction.run(state)

        logger.info("Pipeline: iniciando ModelingAgent.")
        state = modeling.run(state)

        logger.info("Pipeline: iniciando BPMNAgent.")
        state = bpmn_gen.run(state)

        logger.info("Pipeline: iniciando ValidationAgent.")
        state = validation.run(state)

        if state.validation.get("is_valid"):
            logger.info("Pipeline: concluído com BPMN válido.")
        else:
            logger.warning(
                "Pipeline: concluído com BPMN inválido — %d erro(s).",
                len(state.validation.get("errors", [])),
            )

    except Exception as exc:
        raise RuntimeError(
            f"Erro durante a execução do pipeline multiagente: {exc}"
        ) from exc

    return state