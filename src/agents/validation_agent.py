"""
ValidationAgent — quarto agente do pipeline.

Responsável por validar estruturalmente o BPMN XML gerado pelo BPMNAgent.

Este agente:
- NÃO usa LLM
- NÃO altera o BPMN
- executa validações determinísticas
- registra logs detalhados
- salva XML inválido para debug
- produz relatório estruturado de validação

Entrada:
    state.bpmn_xml

Saída:
    state.validation = {
        is_valid,
        errors,
        warnings
    }
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from datetime import datetime

from src.agents.base_agent import BaseAgent
from src.pipeline.state import ProcessModel
from src.validation.rules import validate_all

logger = logging.getLogger(__name__)


class ValidationAgent(BaseAgent):
    """
    Agente responsável por validar BPMN XML.

    Aplica regras estruturais definidas em:
        src.validation.rules.validate_all

    Nunca lança exceções para o pipeline.
    Qualquer erro interno é convertido em validation.errors.
    """

    DEBUG_DIR = Path("outputs/debug")

    def run(self, state: ProcessModel) -> ProcessModel:
        """
        Executa validação estrutural do BPMN.

        Args:
            state:
                ProcessModel contendo state.bpmn_xml

        Returns:
            ProcessModel atualizado com:
                state.validation
        """

        logger.info("ValidationAgent: iniciando validação BPMN.")

        # =====================================================
        # BPMN vazio
        # =====================================================

        if not state.bpmn_xml or not state.bpmn_xml.strip():

            logger.error("ValidationAgent: BPMN XML vazio.")

            state.validation = {
                "is_valid": False,
                "errors": [
                    "bpmn_xml está vazio — BPMNAgent não produziu saída."
                ],
                "warnings": [],
            }

            return state

        try:

            # =====================================================
            # Executa todas as regras
            # =====================================================

            result = validate_all(state.bpmn_xml)

            errors = result.get("errors", [])
            warnings = result.get("warnings", [])

            is_valid = len(errors) == 0

            state.validation = {
                "is_valid": is_valid,
                "errors": errors,
                "warnings": warnings,
            }

            # =====================================================
            # LOGS
            # =====================================================

            if is_valid:

                logger.info(
                    "ValidationAgent: BPMN válido com %d warning(s).",
                    len(warnings),
                )

            else:

                logger.warning(
                    "ValidationAgent: BPMN inválido — %d erro(s), %d aviso(s).",
                    len(errors),
                    len(warnings),
                )

                # Mostra todos os erros
                for idx, err in enumerate(errors, start=1):
                    logger.error("Erro %d: %s", idx, err)

                # Mostra warnings
                for idx, warn in enumerate(warnings, start=1):
                    logger.warning("Warning %d: %s", idx, warn)

                # Salva XML inválido
                self._save_invalid_bpmn(state.bpmn_xml)

                # Salva relatório detalhado
                self._save_validation_report(
                    errors=errors,
                    warnings=warnings,
                )

        except Exception as exc:

            logger.exception(
                "ValidationAgent: erro inesperado durante validação."
            )

            state.validation = {
                "is_valid": False,
                "errors": [
                    f"Erro interno no ValidationAgent: {exc}"
                ],
                "warnings": [],
            }

        return state

    # =========================================================
    # DEBUG HELPERS
    # =========================================================

    def _save_invalid_bpmn(self, xml: str) -> None:
        """
        Salva XML inválido para debug posterior.
        """

        try:

            self.DEBUG_DIR.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            filepath = (
                self.DEBUG_DIR /
                f"invalid_bpmn_{timestamp}.bpmn"
            )

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(xml)

            logger.info(
                "ValidationAgent: XML inválido salvo em %s",
                filepath,
            )

        except Exception:

            logger.exception(
                "ValidationAgent: falha ao salvar XML inválido."
            )

    def _save_validation_report(
        self,
        errors: list[str],
        warnings: list[str],
    ) -> None:
        """
        Salva relatório estruturado da validação.
        """

        try:

            self.DEBUG_DIR.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            filepath = (
                self.DEBUG_DIR /
                f"validation_report_{timestamp}.json"
            )

            report = {
                "is_valid": len(errors) == 0,
                "errors": errors,
                "warnings": warnings,
            }

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(
                    report,
                    f,
                    indent=2,
                    ensure_ascii=False,
                )

            logger.info(
                "ValidationAgent: relatório salvo em %s",
                filepath,
            )

        except Exception:

            logger.exception(
                "ValidationAgent: falha ao salvar relatório."
            )