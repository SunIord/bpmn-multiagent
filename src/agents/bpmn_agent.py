"""
BPMNAgent — terceiro agente do pipeline.

Recebe a estrutura lógica do processo (atividades, eventos, gateways e
sequências) e gera deterministicamente o XML BPMN 2.0 usando lxml.

Este agente NÃO usa LLM.

Agora também gera:
- BPMNDI
- BPMNShape
- BPMNEdge
- Bounds
- Waypoints

Permitindo renderização automática em ferramentas BPMN.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from lxml import etree

from src.agents.base_agent import BaseAgent
from src.pipeline.state import ProcessModel

logger = logging.getLogger(__name__)


class BPMNAgent(BaseAgent):

    # =========================================================
    # NAMESPACES BPMN 2.0
    # =========================================================

    NSMAP: Dict[str | None, str] = {
        None: "http://www.omg.org/spec/BPMN/20100524/MODEL",
        "bpmndi": "http://www.omg.org/spec/BPMN/20100524/DI",
        "dc": "http://www.omg.org/spec/DD/20100524/DC",
        "di": "http://www.omg.org/spec/DD/20100524/DI",
    }

    BPMNDI_NS = "http://www.omg.org/spec/BPMN/20100524/DI"
    DC_NS = "http://www.omg.org/spec/DD/20100524/DC"
    DI_NS = "http://www.omg.org/spec/DD/20100524/DI"

    # =========================================================
    # MAIN
    # =========================================================

    def run(self, state: ProcessModel) -> ProcessModel:
        """
        Gera XML BPMN 2.0 + BPMNDI.

        Args:
            state: ProcessModel preenchido pelos agentes anteriores.

        Returns:
            ProcessModel com state.bpmn_xml preenchido.
        """

        # =========================================================
        # ROOT
        # =========================================================

        root = etree.Element(
            "definitions",
            nsmap=self.NSMAP,
        )

        process = etree.SubElement(
            root,
            "process",
            id="Process_1",
            isExecutable="false",
        )

        # =========================================================
        # AUXILIARES
        # =========================================================

        id_map: Dict[str, str] = {}

        counters: Dict[str, int] = {
            "startEvent": 0,
            "task": 0,
            "exclusiveGateway": 0,
            "endEvent": 0,
        }

        positions: Dict[str, Dict[str, Any]] = {}

        current_x = 100
        current_y = 200

        # =========================================================
        # START EVENTS
        # =========================================================

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

        for activity in state.activities:

            # Compatibilidade:
            # aceita string OU dict

            if isinstance(activity, dict):
                task_name = activity.get("name", "Task")
            else:
                task_name = str(activity)

            elem_id = self._make_id(
                "task",
                counters,
                id_map,
                task_name,
            )

            etree.SubElement(
                process,
                "task",
                id=elem_id,
                name=task_name,
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

            if isinstance(gw, dict):
                gw_name = gw.get("condition", "Decision")
            else:
                gw_name = str(gw)

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
        # LANESET
        # =========================================================

        actors = set()

        for activity in state.activities:

            if isinstance(activity, dict):
                actors.add(
                    activity.get("actor", "Processo")
                )

        if actors:

            lane_set = etree.SubElement(
                process,
                "laneSet",
                id="LaneSet_1",
            )

            for actor_name in actors:

                lane_id = (
                    "Lane_"
                    + actor_name.replace(" ", "_")
                )

                lane = etree.SubElement(
                    lane_set,
                    "lane",
                    id=lane_id,
                    name=actor_name,
                )

                for activity in state.activities:

                    if not isinstance(activity, dict):
                        continue

                    if activity.get("actor") != actor_name:
                        continue

                    task_name = activity.get("name")

                    task_id = id_map.get(task_name)

                    if task_id:

                        flow_node_ref = etree.SubElement(
                            lane,
                            "flowNodeRef",
                        )

                        flow_node_ref.text = task_id

        # =========================================================
        # SEQUENCE FLOWS
        # =========================================================

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

            flow_attrs: Dict[str, str] = {
                "id": f"flow_{flow_counter}",
                "sourceRef": source_id,
                "targetRef": target_id,
            }

            if condition:
                flow_attrs["name"] = condition

            etree.SubElement(
                process,
                "sequenceFlow",
                **flow_attrs,
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

            source_pos = positions.get(source_id)
            target_pos = positions.get(target_id)

            if not source_pos or not target_pos:
                continue

            edge = etree.SubElement(
                plane,
                f"{{{self.BPMNDI_NS}}}BPMNEdge",
                id=f"flow_{flow_counter}_di",
                bpmnElement=f"flow_{flow_counter}",
            )

            # waypoint origem
            etree.SubElement(
                edge,
                f"{{{self.DI_NS}}}waypoint",
                x=str(
                    source_pos["x"]
                    + source_pos["width"]
                ),
                y=str(
                    source_pos["y"]
                    + source_pos["height"] // 2
                ),
            )

            # waypoint destino
            etree.SubElement(
                edge,
                f"{{{self.DI_NS}}}waypoint",
                x=str(target_pos["x"]),
                y=str(
                    target_pos["y"]
                    + target_pos["height"] // 2
                ),
            )

        # =========================================================
        # SERIALIZAÇÃO
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

    # =========================================================
    # HELPERS
    # =========================================================

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

        elem_id = (
            f"{element_type}_{counters[element_type]}"
        )

        id_map[name] = elem_id

        return elem_id