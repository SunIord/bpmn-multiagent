"""
BPMNAgent — terceiro agente do pipeline.

Recebe a estrutura lógica do processo (atividades, eventos, gateways e
sequências) e gera deterministicamente o XML BPMN 2.0 usando lxml.
Este agente NÃO chama o LLM — a serialização é inteiramente determinística,
conforme decisão arquitetural ADR-003.
"""

from __future__ import annotations

import logging
from typing import Dict

from lxml import etree

from src.agents.base_agent import BaseAgent
from src.pipeline.state import ProcessModel

logger = logging.getLogger(__name__)


class BPMNAgent(BaseAgent):
    """
    Agente de geração de XML BPMN 2.0.

    Lê os campos estruturais do ProcessModel (preenchidos pelo ExtractionAgent
    e ModelingAgent) e constrói o XML BPMN 2.0 usando a biblioteca lxml.
    """

    # Namespaces BPMN 2.0 obrigatórios
    NSMAP: Dict[str | None, str] = {
        None: "http://www.omg.org/spec/BPMN/20100524/MODEL",
        "bpmndi": "http://www.omg.org/spec/BPMN/20100524/DI",
        "dc": "http://www.omg.org/spec/DD/20100524/DC",
        "di": "http://www.omg.org/spec/DD/20100524/DI",
    }

    def run(self, state: ProcessModel) -> ProcessModel:
        """
        Gera o XML BPMN 2.0 a partir dos elementos e sequências do processo.

        Args:
            state: ProcessModel com os campos `activities`, `start_events`,
                   `end_events`, `gateways` e `sequences` preenchidos.

        Returns:
            ProcessModel com o campo `bpmn_xml` preenchido com o XML gerado.
        """
        # Cria o elemento raiz <definitions> com namespaces
        root = etree.Element("definitions", nsmap=self.NSMAP)
        process = etree.SubElement(root, "process", id="Process_1")

        # Mapeamento nome → ID para referências cruzadas
        id_map: Dict[str, str] = {}
        counters: Dict[str, int] = {
            "startEvent": 0,
            "task": 0,
            "exclusiveGateway": 0,
            "endEvent": 0,
        }

        # --- Cria elementos BPMN ---

        # Eventos de início
        for name in state.start_events:
            elem_id = self._make_id("startEvent", counters, id_map, name)
            etree.SubElement(process, "startEvent", id=elem_id, name=name)

        # Atividades (tarefas)
        for name in state.activities:
            elem_id = self._make_id("task", counters, id_map, name)
            etree.SubElement(process, "task", id=elem_id, name=name)

        # Gateways (exclusivos)
        for gw in state.gateways:
            # Usa a condição como nome do gateway
            gw_name = gw.get("condition", "Decisão")
            elem_id = self._make_id("exclusiveGateway", counters, id_map, gw_name)
            etree.SubElement(process, "exclusiveGateway", id=elem_id, name=gw_name)

        # Eventos de fim
        for name in state.end_events:
            elem_id = self._make_id("endEvent", counters, id_map, name)
            etree.SubElement(process, "endEvent", id=elem_id, name=name)

        # --- Cria Sequence Flows ---
        flow_counter = 0
        for seq in state.sequences:
            flow_counter += 1
            source_name = seq.get("source", "")
            target_name = seq.get("target", "")
            condition = seq.get("condition", "")

            # Verifica se os elementos referenciados existem
            source_id = id_map.get(source_name)
            if source_id is None:
                logger.warning(
                    "SequenceFlow '%d': source '%s' não encontrado nos elementos — ignorado.",
                    flow_counter,
                    source_name,
                )
                continue

            target_id = id_map.get(target_name)
            if target_id is None:
                logger.warning(
                    "SequenceFlow '%d': target '%s' não encontrado nos elementos — ignorado.",
                    flow_counter,
                    target_name,
                )
                continue

            # Atributos do sequenceFlow
            flow_attrs: Dict[str, str] = {
                "id": f"flow_{flow_counter}",
                "sourceRef": source_id,
                "targetRef": target_id,
            }
            # Adiciona o nome da condição se houver (ex.: "sim", "não")
            if condition:
                flow_attrs["name"] = condition

            etree.SubElement(process, "sequenceFlow", **flow_attrs)

        # Serializa a árvore XML
        state.bpmn_xml = '<?xml version="1.0" encoding="UTF-8"?>\n' + etree.tostring(
            root,
            pretty_print=True,
            encoding="unicode",
        )

        return state

    @staticmethod
    def _make_id(
        element_type: str,
        counters: Dict[str, int],
        id_map: Dict[str, str],
        name: str,
    ) -> str:
        """
        Gera um ID único para um elemento BPMN e atualiza o mapeamento.

        Args:
            element_type: Tipo do elemento (ex.: "task", "startEvent").
            counters: Dicionário de contadores por tipo.
            id_map: Dicionário nome → ID.
            name: Nome descritivo do elemento.

        Returns:
            ID único no formato "tipo_numero" (ex.: "task_1").
        """
        # Se o nome já foi mapeado, reutiliza o ID (evita duplicatas)
        if name in id_map:
            return id_map[name]

        counters[element_type] += 1
        elem_id = f"{element_type}_{counters[element_type]}"
        id_map[name] = elem_id
        return elem_id