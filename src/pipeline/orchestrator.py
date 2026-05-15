"""
Orquestrador do pipeline multiagente.

Controla a execução dos agentes. Na Sprint 1, o fluxo é linear e sequencial:
extração → modelagem → geração BPMN. Não utiliza LangGraph porque o grafo
simples não justifica a complexidade extra de serialização.
"""

from __future__ import annotations

from src.agents.bpmn_agent import BPMNAgent
from src.agents.extraction_agent import ExtractionAgent
from src.agents.modeling_agent import ModelingAgent
from src.pipeline.state import ProcessModel


def run_pipeline(text: str) -> ProcessModel:
    """
    Executa o pipeline multiagente completo sobre um texto de processo.

    Args:
        text: Descrição do processo em linguagem natural.

    Returns:
        ProcessModel com todos os campos preenchidos, incluindo `bpmn_xml`.

    Raises:
        RuntimeError: Se qualquer agente do pipeline falhar.
    """
    state = ProcessModel(raw_input=text, input_type="freetext")

    extraction = ExtractionAgent()
    modeling = ModelingAgent()
    bpmn_gen = BPMNAgent()

    try:
        state = extraction.run(state)
        state = modeling.run(state)
        state = bpmn_gen.run(state)
    except Exception as exc:
        raise RuntimeError(
            f"Erro durante a execução do pipeline multiagente: {exc}"
        ) from exc

    return state