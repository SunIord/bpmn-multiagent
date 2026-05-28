"""
BPMNAgent — terceiro agente do pipeline.

Recebe a estrutura lógica do processo (atividades, eventos, gateways e
sequências) e gera deterministicamente o XML BPMN 2.0 usando lxml.

Agora o agente também gera:
- BPMNDI
- BPMNShape
- BPMNEdge
- Bounds
- Waypoints

permitindo que o BPMN seja desenhado automaticamente em ferramentas
como Camunda Modeler e BPMN.io.
"""

from __future__ import annotations

import logging
from typing import Dict, Any

from lxml import etree

from src.agents.base_agent import BaseAgent
from src.pipeline.state import ProcessModel

logger = logging.getLogger(__name__)


class BPMNAgent(BaseAgent):

    # Namespaces BPMN 2.0
    NSMAP: Dict[str | None, str] = {
        None: "http://www.omg.org/spec/BPMN/20100524/MODEL",
        "bpmndi": "http://www.omg.org/spec/BPMN/20100524/DI",
        "dc": "http://www.omg.org/spec/DD/20100524/DC",
        "di": "http://www.omg.org/spec/DD/20100524/DI",
    }

    BPMNDI_NS = "http://www.omg.org/spec/BPMN/20100524/DI"
    DC_NS = "http://www.omg.org/spec/DD/20100524/DC"
    DI_NS = "http://www.omg.org/spec/DD/20100524/DI"

    def run(self, state: ProcessModel) -> ProcessModel:

        improvePrompt
        # =========================================================
        # ROOT DEFINITIONS
        # =========================================================

        Args:
            state: ProcessModel com os campos `activities`, `start_events`,
                `end_events`, `gateways`, `sequences` e `actors` preenchidos.
         main

        root = etree.Element("definitions", nsmap=self.NSMAP)

        process = etree.SubElement(
            root,
            "process",
            id="Process_1",
            isExecutable="false",
        )

        # =========================================================
        # ESTRUTURAS AUXILIARES
        # =========================================================

        id_map: Dict[str, str] = {}

        counters: Dict[str, int] = {
            "startEvent": 0,
            "task": 0,
            "exclusiveGateway": 0,
            "endEvent": 0,
        }

        # Guarda posição visual dos elementos
        positions: Dict[str, Dict[str, Any]] = {}

        # Coordenadas iniciais
        current_x = 100
        current_y = 200

        # =========================================================
        # START EVENTS
        # =========================================================

        # --- Cria elementos BPMN que não vão nas lanes ---
        # Eventos de início
        for name in state.start_events:

            elem_id = self._make_id(
                "startEvent",
                counters,
                id_map,
                name,
            )

            etree.SubElement(
                process,
                "startEvent",
                id=elem_id,
                name=name,
            )

            positions[elem_id] = {
                "x": current_x,
                "y": current_y,
                "width": 36,
                "height": 36,
            }

            current_x += 150

        # =========================================================
        # TASKS
        # =========================================================

        for name in state.activities:

            elem_id = self._make_id(
                "task",
                counters,
                id_map,
                name,
            )

            etree.SubElement(
                process,
                "task",
                id=elem_id,
                name=name,
            )

            positions[elem_id] = {
                "x": current_x,
                "y": current_y,
                "width": 100,
                "height": 80,
            }

            current_x += 180

        # =========================================================
        # GATEWAYS
        # =========================================================

        for gw in state.gateways:
        # Gateways (exclusivos)
        for gw in state.gateways:
            gw_name = gw.get("condition", "Decisão")
            elem_id = self._make_id("exclusiveGateway", counters, id_map, gw_name)
            etree.SubElement(process, "exclusiveGateway", id=elem_id, name=gw_name)

            gw_name = gw.get("condition", "Decision")

            elem_id = self._make_id(
                "exclusiveGateway",
                counters,
                id_map,
                gw_name,
            )

            etree.SubElement(
                process,
                "exclusiveGateway",
                id=elem_id,
                name=gw_name,
            )

            positions[elem_id] = {
                "x": current_x,
                "y": current_y + 15,
                "width": 50,
                "height": 50,
            }

            current_x += 150

        # =========================================================
        # END EVENTS
        # =========================================================

        for name in state.end_events:

            elem_id = self._make_id(
                "endEvent",
                counters,
                id_map,
                name,
            )

            etree.SubElement(
                process,
                "endEvent",
                id=elem_id,
                name=name,
            )

            positions[elem_id] = {
                "x": current_x,
                "y": current_y,
                "width": 36,
                "height": 36,
            }

            current_x += 150

        # =========================================================
        # SEQUENCE FLOWS
        # =========================================================

        # --- Cria LaneSet e Lanes ---
        actors = state.actors if state.actors else ["Processo"]
        lane_set = etree.SubElement(process, "laneSet")

        # Agrupa atividades por ator
        actor_tasks: Dict[str, list[dict]] = {actor: [] for actor in actors}
        for act in state.activities:
            actor = act.get("actor", "").strip()
            # Se o ator não estiver na lista, coloca no primeiro ator como fallback
            if actor not in actor_tasks:
                actor = actors[0]
            actor_tasks[actor].append(act)

        for actor_name, tasks in actor_tasks.items():
            lane_id = f"lane_{actor_name.replace(' ', '_')}"
            lane = etree.SubElement(lane_set, "lane", id=lane_id, name=actor_name)
            for task in tasks:
                task_name = task["name"]
                task_id = self._make_id("task", counters, id_map, task_name)
                task_elem = etree.SubElement(lane, "task", id=task_id, name=task_name)
                etree.SubElement(lane, "flowNodeRef", id=task_id)

        # --- Cria Sequence Flows ---
        flow_counter = 0

        for seq in state.sequences:

            flow_counter += 1

            source_name = seq.get("source", "")
            target_name = seq.get("target", "")
            condition = seq.get("condition", "")

            source_id = id_map.get(source_name)
            target_id = id_map.get(target_name)

            if source_id is None:
                logger.warning(
                    "SequenceFlow '%d': source '%s' não encontrado.",
                    flow_counter,
                    source_name,
                )
                continue

            if target_id is None:
                logger.warning(
                    "SequenceFlow '%d': target '%s' não encontrado.",
                    flow_counter,
                    target_name,
                )
                continue

            attrs = {
            flow_attrs: Dict[str, str] = {
                "id": f"flow_{flow_counter}",
                "sourceRef": source_id,
                "targetRef": target_id,
            }

            if condition:
                attrs["name"] = condition

            etree.SubElement(
                process,
                "sequenceFlow",
                **attrs,
            )

        # =========================================================
        # BPMNDI
        # =========================================================

        diagram = etree.SubElement(
            root,
            f"{{{self.BPMNDI_NS}}}BPMNDiagram",
            id="BPMNDiagram_1",
        )

        plane = etree.SubElement(
            diagram,
            f"{{{self.BPMNDI_NS}}}BPMNPlane",
            id="BPMNPlane_1",
            bpmnElement="Process_1",
        )

        # =========================================================
        # BPMN SHAPES
        # =========================================================

        for elem_id, pos in positions.items():

            shape = etree.SubElement(
                plane,
                f"{{{self.BPMNDI_NS}}}BPMNShape",
                id=f"{elem_id}_di",
                bpmnElement=elem_id,
            )

            etree.SubElement(
                shape,
                f"{{{self.DC_NS}}}Bounds",
                x=str(pos["x"]),
                y=str(pos["y"]),
                width=str(pos["width"]),
                height=str(pos["height"]),
            )

        # =========================================================
        # BPMN EDGES
        # =========================================================

        flow_counter = 0

        for seq in state.sequences:

            flow_counter += 1

            source_name = seq.get("source", "")
            target_name = seq.get("target", "")

            source_id = id_map.get(source_name)
            target_id = id_map.get(target_name)

            if source_id is None or target_id is None:
                continue

            source_pos = positions[source_id]
            target_pos = positions[target_id]

            edge = etree.SubElement(
                plane,
                f"{{{self.BPMNDI_NS}}}BPMNEdge",
                id=f"flow_{flow_counter}_di",
                bpmnElement=f"flow_{flow_counter}",
            )

            # ponto de saída
            etree.SubElement(
                edge,
                f"{{{self.DI_NS}}}waypoint",
                x=str(source_pos["x"] + source_pos["width"]),
                y=str(source_pos["y"] + source_pos["height"] // 2),
            )

            # ponto de entrada
            etree.SubElement(
                edge,
                f"{{{self.DI_NS}}}waypoint",
                x=str(target_pos["x"]),
                y=str(target_pos["y"] + target_pos["height"] // 2),
            )

        # =========================================================
        # SERIALIZAÇÃO FINAL
        # =========================================================

        state.bpmn_xml = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            + etree.tostring(
                root,
                pretty_print=True,
                encoding="unicode",
            )
        )

        return state

    @staticmethod
    def _make_id(
        element_type: str,
        counters: Dict[str, int],
        id_map: Dict[str, str],
        name: str,
    ) -> str:

        if name in id_map:
            return id_map[name]

        counters[element_type] += 1

        elem_id = f"{element_type}_{counters[element_type]}"

        id_map[name] = elem_id

        return elem_id