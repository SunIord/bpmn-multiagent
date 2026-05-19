"""
RefinementAgent — quinto agente do pipeline.

Fecha o ciclo de autocorreção: quando o ValidationAgent encontra erros
no BPMN gerado, este agente chama o LLM para corrigir apenas os problemas
apontados, preservando o restante da estrutura XML.

Fluxo de uso (controlado pelo orquestrador):
    ValidationAgent detecta erros
        → RefinementAgent corrige via LLM
        → BPMNAgent NÃO é chamado novamente (o XML já é corrigido diretamente)
        → ValidationAgent reavalia
        → repete até is_valid=True ou iteration >= MAX_ITERATIONS

Entrada:
    ProcessModel.bpmn_xml          — XML com problemas
    ProcessModel.validation.errors — erros identificados
    ProcessModel.validation.warnings — avisos opcionais
    ProcessModel.iteration         — contador da iteração atual

Saída:
    ProcessModel.bpmn_xml  — XML corrigido pelo LLM
    ProcessModel.iteration — incrementado em 1
    ProcessModel.history   — snapshot do estado anterior adicionado
"""

from __future__ import annotations

import logging
import re

from src.agents.base_agent import BaseAgent
from src.llm.provider import LLMProviderError, generate
from src.pipeline.state import ProcessModel

logger = logging.getLogger(__name__)

_XML_START_PATTERN = re.compile(r"(<\?xml[\s\S]*?<definitions[\s\S]+)", re.IGNORECASE)
_DEFINITIONS_PATTERN = re.compile(r"(<definitions[\s\S]+)", re.IGNORECASE)
_MARKDOWN_FENCE = re.compile(r"```(?:xml)?([\s\S]*?)```", re.IGNORECASE)


def _extract_xml(raw: str) -> str:
    """
    Extrai o XML válido de uma resposta bruta do LLM.

    Tenta, em ordem:
    1. Remover blocos de markdown (```xml ... ```) e usar o conteúdo interno.
    2. Localizar <?xml ... como ponto de início.
    3. Localizar <definitions como ponto de início.
    4. Retornar a string original se nenhum padrão for encontrado
       (o ValidationAgent detectará o problema na próxima rodada).

    Args:
        raw: Texto bruto retornado pelo LLM.

    Returns:
        String com o XML extraído e sem markdown residual.
    """
    # 1. Remove blocos de markdown se existirem
    fence_match = _MARKDOWN_FENCE.search(raw)
    if fence_match:
        raw = fence_match.group(1).strip()

    # 2. Tenta localizar o início do XML com declaração
    xml_match = _XML_START_PATTERN.search(raw)
    if xml_match:
        return xml_match.group(1).strip()

    # 3. Tenta localizar <definitions diretamente
    def_match = _DEFINITIONS_PATTERN.search(raw)
    if def_match:
        return def_match.group(1).strip()

    # 4. Retorna como está — o validador vai capturar o problema
    logger.warning(
        "RefinementAgent._extract_xml: não foi possível localizar XML na resposta. "
        "Retornando resposta bruta."
    )
    return raw.strip()


def _format_list(items: list[str], label: str) -> str:
    """
    Formata uma lista de strings como lista numerada para inclusão no prompt.

    Args:
        items: Lista de mensagens.
        label: Rótulo exibido quando a lista está vazia.

    Returns:
        String formatada para leitura do LLM.
    """
    if not items:
        return f"(nenhum {label})"
    return "\n".join(f"{i + 1}. {item}" for i, item in enumerate(items))


class RefinementAgent(BaseAgent):
    """
    Agente de refinamento iterativo de BPMN.

    Usa o LLM para corrigir erros de validação estrutural encontrados pelo
    ValidationAgent. Opera diretamente sobre `bpmn_xml`, sem regenerar
    os elementos do processo a partir do zero.

    Não lança exceções para fora — falhas internas são capturadas e
    registradas em `state.validation["errors"]`.
    """

    def run(self, state: ProcessModel) -> ProcessModel:
        """
        Tenta corrigir o XML BPMN com base nos erros de validação.

        Passos executados:
        1. Verifica se há erros para corrigir — retorna sem modificar se não houver.
        2. Salva snapshot do estado atual em `state.history`.
        3. Incrementa `state.iteration`.
        4. Monta o prompt com o XML atual + erros + warnings.
        5. Chama o LLM e extrai o XML corrigido da resposta.
        6. Atribui o XML corrigido a `state.bpmn_xml`.

        Args:
            state: ProcessModel com `bpmn_xml` e `validation` preenchidos.

        Returns:
            ProcessModel com `bpmn_xml` atualizado, `iteration` incrementado
            e snapshot adicionado em `history`. Se o LLM falhar, `bpmn_xml`
            permanece inalterado e o erro é registrado em `validation.errors`.
        """
        errors: list[str] = state.validation.get("errors", [])
        warnings: list[str] = state.validation.get("warnings", [])

        # Nada a corrigir — retorna sem modificar
        if not errors:
            logger.info(
                "RefinementAgent: validation.errors está vazio, nenhuma correção necessária."
            )
            return state

        # Salva snapshot antes de qualquer modificação
        state.snapshot()
        state.iteration += 1

        logger.info(
            "RefinementAgent: iniciando iteração %d com %d erro(s) a corrigir.",
            state.iteration,
            len(errors),
        )

        # Carrega e monta o prompt
        try:
            template = self._load_prompt("refinement.txt")
        except FileNotFoundError as exc:
            logger.error("RefinementAgent: arquivo de prompt não encontrado: %s", exc)
            state.validation["errors"].append(
                f"RefinementAgent: prompt 'refinement.txt' não encontrado — {exc}"
            )
            return state

        prompt = (
            template
            .replace("{XML_ATUAL}", state.bpmn_xml)
            .replace("{ERROS}", _format_list(errors, "erro"))
            .replace("{WARNINGS}", _format_list(warnings, "warning"))
        )

        # Chama o LLM
        try:
            raw_response = generate(prompt)
        except LLMProviderError as exc:
            logger.error("RefinementAgent: falha na chamada ao LLM: %s", exc)
            state.validation["errors"].append(
                f"RefinementAgent (iteração {state.iteration}): LLM indisponível — {exc}"
            )
            return state
        except Exception as exc:
            logger.exception("RefinementAgent: erro inesperado ao chamar o LLM.")
            state.validation["errors"].append(
                f"RefinementAgent (iteração {state.iteration}): erro inesperado — {exc}"
            )
            return state

        # Extrai o XML da resposta
        corrected_xml = _extract_xml(raw_response)

        if not corrected_xml:
            logger.warning(
                "RefinementAgent: LLM retornou resposta vazia ou sem XML reconhecível."
            )
            state.validation["errors"].append(
                f"RefinementAgent (iteração {state.iteration}): "
                "LLM não retornou XML utilizável."
            )
            return state

        state.bpmn_xml = corrected_xml
        logger.info(
            "RefinementAgent: XML atualizado com sucesso na iteração %d.",
            state.iteration,
        )

        return state