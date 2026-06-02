"""
Orquestrador do pipeline multiagente.

Controla a execução dos agentes com ciclo de refinamento.
Fluxo (Sprint 3):
    extract → model → generate → validate ─── válido ──────────► END
                                       │
                                    inválido + iteration < 3
                                       │
                                     refine (re-extrai + re-modela)
                                       │
                                     bpmn_xml = "" → generate (BPMNAgent determinístico)
                                       │
                                     validate (loop)
                                       │
                                    inválido + iteration >= 3
                                       │
                                       └──► END (com erros)

O RefinementAgent (v2) não edita mais o XML diretamente. Em vez disso:
- Re-extrai elementos e re-modela sequências via LLM
- Limpa state.bpmn_xml para sinalizar que precisa regenerar
- O BPMNAgent (determinístico, lxml) gera o XML limpo
"""

from __future__ import annotations

import logging

from src.agents.bpmn_agent import BPMNAgent
from src.agents.extraction_agent import ExtractionAgent
from src.agents.modeling_agent import ModelingAgent
from src.agents.refinement_agent import RefinementAgent
from src.agents.validation_agent import ValidationAgent
from src.pipeline.state import ProcessModel

logger = logging.getLogger(__name__)

MAX_ITERATIONS = 3


def run_pipeline(text: str, input_type: str = "freetext") -> ProcessModel:
    """
    Executa o pipeline multiagente completo sobre um texto de processo.

    Args:
        text:       Descrição do processo em linguagem natural.
        input_type: Tipo de entrada — "freetext", "structured" ou "noisy".

    Returns:
        ProcessModel com todos os campos preenchidos, incluindo
        `bpmn_xml` e `validation`. Se a validação falhar após 3 tentativas
        de refinamento, o estado é retornado com `validation.is_valid == False`.

    Raises:
        RuntimeError: Se qualquer agente lançar uma exceção não tratada.
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

            # Se o RefinementAgent limpou o XML, regenera com BPMNAgent (determinístico)
            if not state.bpmn_xml:
                logger.info("Pipeline: RefinementAgent invalidou o XML. Regenerando com BPMNAgent.")
                state = bpmn_gen.run(state)
            else:
                logger.warning(
                    "Pipeline: RefinementAgent não limpou bpmn_xml. Pulando regeneração."
                )

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