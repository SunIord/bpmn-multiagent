"""
Orquestrador do pipeline multiagente.

Fluxo:

extract
   ↓
model
   ↓
generate BPMN
   ↓
validate
   ↓
refine (loop se inválido)
   ↓
render
   ↓
END
"""

from __future__ import annotations

import logging

from src.agents.bpmn_agent import BPMNAgent
from src.agents.extraction_agent import ExtractionAgent
from src.agents.modeling_agent import ModelingAgent
from src.agents.refinement_agent import RefinementAgent
from src.agents.validation_agent import ValidationAgent
from src.agents.render_agent import RenderAgent

from src.pipeline.state import ProcessModel

logger = logging.getLogger(__name__)

MAX_ITERATIONS = 3


def run_pipeline(
    text: str,
    input_type: str = "freetext",
) -> ProcessModel:
    """
    Executa o pipeline multiagente completo.

    Args:
        text:
            Texto do processo.

        input_type:
            Tipo de entrada:
            - freetext
            - noisy
            - structured

    Returns:
        ProcessModel final.
    """

    state = ProcessModel(
        raw_input=text,
        input_type=input_type,
    )

    # =========================================================
    # AGENTES
    # =========================================================

    extraction = ExtractionAgent()

    modeling = ModelingAgent()

    bpmn_gen = BPMNAgent()

    validation = ValidationAgent()

    refinement = RefinementAgent()

    render = RenderAgent()

    try:

        # =========================================================
        # EXTRACTION
        # =========================================================

        logger.info(
            "Pipeline: iniciando ExtractionAgent."
        )

        state = extraction.run(state)

        # =========================================================
        # MODELING
        # =========================================================

        logger.info(
            "Pipeline: iniciando ModelingAgent."
        )

        state = modeling.run(state)

        # =========================================================
        # BPMN GENERATION
        # =========================================================

        logger.info(
            "Pipeline: iniciando BPMNAgent."
        )

        state = bpmn_gen.run(state)

        # =========================================================
        # VALIDATION
        # =========================================================

        logger.info(
            "Pipeline: iniciando ValidationAgent."
        )

        state = validation.run(state)

        # =========================================================
        # REFINEMENT LOOP
        # =========================================================

        while (
            not state.validation.get("is_valid")
            and state.iteration < MAX_ITERATIONS
        ):

            logger.warning(
                (
                    "Pipeline: BPMN inválido — "
                    "encaminhando para RefinementAgent "
                    "(iteração %d)."
                ),
                state.iteration,
            )

            state = refinement.run(state)

            logger.info(
                "Pipeline: reavaliando BPMN."
            )

            state = validation.run(state)

        # =========================================================
        # RESULTADO FINAL DA VALIDAÇÃO
        # =========================================================

        if state.validation.get("is_valid"):

            logger.info(
                "Pipeline: BPMN válido."
            )

            # =====================================================
            # RENDER
            # =====================================================

            logger.info(
                "Pipeline: iniciando RenderAgent."
            )

            state = render.run(state)

            logger.info(
                (
                    "Pipeline: renderização concluída "
                    "(PNG + SVG gerados)."
                )
            )

        else:

            logger.warning(
                (
                    "Pipeline: concluído com BPMN inválido "
                    "após %d tentativa(s)."
                ),
                state.iteration,
            )

            logger.warning(
                "Total de erros: %d",
                len(state.validation.get("errors", [])),
            )

            for err in state.validation.get("errors", []):

                logger.warning(
                    "Erro de validação: %s",
                    err,
                )

    except Exception as exc:

        logger.exception(
            "Pipeline: erro inesperado."
        )

        raise RuntimeError(
            (
                "Erro durante execução do pipeline "
                f"multiagente: {exc}"
            )
        ) from exc

    return state