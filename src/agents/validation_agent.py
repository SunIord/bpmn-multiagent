"""
ValidationAgent — quarto agente do pipeline.

Aplica regras de validação estrutural sobre o XML BPMN gerado pelo BPMNAgent.
Este agente NÃO usa LLM — é 100% determinístico.
As regras vivem em src/validation/rules.py e podem ser adicionadas sem
modificar este arquivo.

Entrada:  ProcessModel.bpmn_xml
Saída:    ProcessModel.validation  {is_valid, errors, warnings}
"""

from __future__ import annotations

import logging

from src.agents.base_agent import BaseAgent
from src.pipeline.state import ProcessModel
from src.validation.rules import validate_all

logger = logging.getLogger(__name__)


class ValidationAgent(BaseAgent):
    """
    Agente de validação estrutural de BPMN.

    Lê `state.bpmn_xml`, aplica todas as regras de `validate_all` e
    preenche `state.validation` com o resultado. Não lança exceções —
    qualquer problema interno é capturado e registrado em `errors`.
    """

    def run(self, state: ProcessModel) -> ProcessModel:
        """
        Valida o XML BPMN contido no estado do pipeline.

        Args:
            state: ProcessModel com `bpmn_xml` preenchido pelo BPMNAgent.

        Returns:
            ProcessModel com `validation` preenchido:
            - is_valid: True apenas se não houver erros.
            - errors:   Lista de problemas que invalidam o BPMN.
            - warnings: Lista de avisos não críticos.
        """
        # Guarda variação se bpmn_xml estiver vazio
        if not state.bpmn_xml or not state.bpmn_xml.strip():
            logger.warning("ValidationAgent: bpmn_xml está vazio, abortando validação.")
            state.validation = {
                "is_valid": False,
                "errors": ["bpmn_xml está vazio — o BPMNAgent não produziu saída."],
                "warnings": [],
            }
            return state

        try:
            result = validate_all(state.bpmn_xml)
            errors = result.get("errors", [])
            warnings = result.get("warnings", [])

            state.validation = {
                "is_valid": len(errors) == 0,
                "errors": errors,
                "warnings": warnings,
            }

            if errors:
                logger.warning(
                    "ValidationAgent: BPMN inválido — %d erro(s), %d aviso(s).",
                    len(errors),
                    len(warnings),
                )
            else:
                logger.info(
                    "ValidationAgent: BPMN válido com %d aviso(s).", len(warnings)
                )

        except Exception as exc:
            # Nunca deixar o pipeline quebrar por falha interna da validação
            logger.exception("ValidationAgent: erro inesperado durante a validação.")
            state.validation = {
                "is_valid": False,
                "errors": [f"Erro interno no ValidationAgent: {exc}"],
                "warnings": [],
            }

        return state