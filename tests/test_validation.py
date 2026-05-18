"""
Testes para o módulo de validação estrutural BPMN.

Cobre as 10 regras de src/validation/rules.py individualmente
e o ValidationAgent integrado.
"""

from __future__ import annotations

import pytest
from lxml import etree

from src.pipeline.state import ProcessModel
from src.agents.validation_agent import ValidationAgent
from src.validation.rules import (
    validate_all,
    validate_duplicate_ids,
    validate_end_event_exists,
    validate_end_event_not_source,
    validate_gateway_outgoing,
    validate_node_connectivity,
    validate_process_exists,
    validate_sequence_flow_exists,
    validate_start_event_exists,
    validate_start_event_not_target,
    validate_xml_well_formed,
)


# ── Fixtures XML ──────────────────────────────────────────────────────────────

VALID_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<definitions xmlns="http://www.omg.org/spec/BPMN/20100524/MODEL"
             id="Definitions_1" targetNamespace="http://bpmn.io/schema/bpmn">
  <process id="Process_1" isExecutable="false">
    <startEvent id="start_1" name="Início"/>
    <task id="task_1" name="Verificar estoque"/>
    <exclusiveGateway id="gw_1" name="Estoque disponível?"/>
    <task id="task_2" name="Separar pedido"/>
    <task id="task_3" name="Notificar cliente"/>
    <endEvent id="end_1" name="Pedido concluído"/>
    <endEvent id="end_2" name="Processo encerrado"/>
    <sequenceFlow id="sf_1" sourceRef="start_1" targetRef="task_1"/>
    <sequenceFlow id="sf_2" sourceRef="task_1" targetRef="gw_1"/>
    <sequenceFlow id="sf_3" sourceRef="gw_1" targetRef="task_2" name="sim"/>
    <sequenceFlow id="sf_4" sourceRef="gw_1" targetRef="task_3" name="não"/>
    <sequenceFlow id="sf_5" sourceRef="task_2" targetRef="end_1"/>
    <sequenceFlow id="sf_6" sourceRef="task_3" targetRef="end_2"/>
  </process>
</definitions>"""

XML_MALFORMED = """\
<?xml version="1.0" encoding="UTF-8"?>
<definitions xmlns="http://www.omg.org/spec/BPMN/20100524/MODEL">
  <process id="Process_1">
    <startEvent id="start_1"
  </process>
"""

XML_NO_PROCESS = """\
<?xml version="1.0" encoding="UTF-8"?>
<definitions xmlns="http://www.omg.org/spec/BPMN/20100524/MODEL" id="D1">
</definitions>"""

XML_NO_START = """\
<?xml version="1.0" encoding="UTF-8"?>
<definitions xmlns="http://www.omg.org/spec/BPMN/20100524/MODEL" id="D1">
  <process id="Process_1">
    <task id="task_1" name="Fazer algo"/>
    <endEvent id="end_1" name="Fim"/>
    <sequenceFlow id="sf_1" sourceRef="task_1" targetRef="end_1"/>
  </process>
</definitions>"""

XML_NO_END = """\
<?xml version="1.0" encoding="UTF-8"?>
<definitions xmlns="http://www.omg.org/spec/BPMN/20100524/MODEL" id="D1">
  <process id="Process_1">
    <startEvent id="start_1" name="Início"/>
    <task id="task_1" name="Fazer algo"/>
    <sequenceFlow id="sf_1" sourceRef="start_1" targetRef="task_1"/>
  </process>
</definitions>"""

XML_NO_FLOWS = """\
<?xml version="1.0" encoding="UTF-8"?>
<definitions xmlns="http://www.omg.org/spec/BPMN/20100524/MODEL" id="D1">
  <process id="Process_1">
    <startEvent id="start_1" name="Início"/>
    <endEvent id="end_1" name="Fim"/>
  </process>
</definitions>"""

XML_DUPLICATE_IDS = """\
<?xml version="1.0" encoding="UTF-8"?>
<definitions xmlns="http://www.omg.org/spec/BPMN/20100524/MODEL" id="D1">
  <process id="Process_1">
    <startEvent id="start_1" name="Início"/>
    <task id="start_1" name="Tarefa com ID duplicado"/>
    <endEvent id="end_1" name="Fim"/>
    <sequenceFlow id="sf_1" sourceRef="start_1" targetRef="end_1"/>
  </process>
</definitions>"""

XML_START_AS_TARGET = """\
<?xml version="1.0" encoding="UTF-8"?>
<definitions xmlns="http://www.omg.org/spec/BPMN/20100524/MODEL" id="D1">
  <process id="Process_1">
    <startEvent id="start_1" name="Início"/>
    <task id="task_1" name="Tarefa"/>
    <endEvent id="end_1" name="Fim"/>
    <sequenceFlow id="sf_1" sourceRef="start_1" targetRef="task_1"/>
    <sequenceFlow id="sf_2" sourceRef="task_1" targetRef="start_1"/>
  </process>
</definitions>"""

XML_END_AS_SOURCE = """\
<?xml version="1.0" encoding="UTF-8"?>
<definitions xmlns="http://www.omg.org/spec/BPMN/20100524/MODEL" id="D1">
  <process id="Process_1">
    <startEvent id="start_1" name="Início"/>
    <task id="task_1" name="Tarefa"/>
    <endEvent id="end_1" name="Fim"/>
    <sequenceFlow id="sf_1" sourceRef="start_1" targetRef="task_1"/>
    <sequenceFlow id="sf_2" sourceRef="end_1" targetRef="task_1"/>
  </process>
</definitions>"""

XML_BAD_REFS = """\
<?xml version="1.0" encoding="UTF-8"?>
<definitions xmlns="http://www.omg.org/spec/BPMN/20100524/MODEL" id="D1">
  <process id="Process_1">
    <startEvent id="start_1" name="Início"/>
    <endEvent id="end_1" name="Fim"/>
    <sequenceFlow id="sf_1" sourceRef="start_1" targetRef="nao_existe_999"/>
  </process>
</definitions>"""

XML_GW_ONE_OUT = """\
<?xml version="1.0" encoding="UTF-8"?>
<definitions xmlns="http://www.omg.org/spec/BPMN/20100524/MODEL" id="D1">
  <process id="Process_1">
    <startEvent id="start_1" name="Início"/>
    <exclusiveGateway id="gw_1" name="Decisão"/>
    <task id="task_1" name="Tarefa"/>
    <endEvent id="end_1" name="Fim"/>
    <sequenceFlow id="sf_1" sourceRef="start_1" targetRef="gw_1"/>
    <sequenceFlow id="sf_2" sourceRef="gw_1" targetRef="task_1"/>
    <sequenceFlow id="sf_3" sourceRef="task_1" targetRef="end_1"/>
  </process>
</definitions>"""


def _root(xml: str) -> etree._Element:
    """Parseia o XML e retorna o elemento raiz."""
    return etree.fromstring(xml.encode("utf-8"))


# ── Testes de validate_all (integração) ───────────────────────────────────────

class TestValidateAll:

    def test_valid_xml_passes_all_rules(self) -> None:
        result = validate_all(VALID_XML)
        assert result["errors"] == [], f"Erros inesperados: {result['errors']}"
        assert result["warnings"] == [], f"Warnings inesperados: {result['warnings']}"

    def test_malformed_xml_returns_error_and_stops(self) -> None:
        result = validate_all(XML_MALFORMED)
        assert len(result["errors"]) >= 1
        assert any("mal-formado" in e.lower() or "xml" in e.lower() for e in result["errors"])

    def test_missing_start_event(self) -> None:
        result = validate_all(XML_NO_START)
        assert any("startEvent" in e or "início" in e.lower() for e in result["errors"])

    def test_missing_end_event(self) -> None:
        result = validate_all(XML_NO_END)
        assert any("endEvent" in e or "fim" in e.lower() for e in result["errors"])

    def test_missing_sequence_flows(self) -> None:
        result = validate_all(XML_NO_FLOWS)
        assert any("sequenceFlow" in e for e in result["errors"])

    def test_duplicate_ids(self) -> None:
        result = validate_all(XML_DUPLICATE_IDS)
        assert any(
            "duplicado" in e.lower() or "duplicate" in e.lower()
            for e in result["errors"]
        )

    def test_start_event_as_target(self) -> None:
        result = validate_all(XML_START_AS_TARGET)
        assert any("startEvent" in e for e in result["errors"])

    def test_end_event_as_source(self) -> None:
        result = validate_all(XML_END_AS_SOURCE)
        assert any("endEvent" in e for e in result["errors"])

    def test_invalid_refs_produce_warnings(self) -> None:
        result = validate_all(XML_BAD_REFS)
        assert any("nao_existe_999" in w for w in result["warnings"])

    def test_gateway_single_outgoing_produces_warning(self) -> None:
        result = validate_all(XML_GW_ONE_OUT)
        assert any("gw_1" in w or "exclusiveGateway" in w for w in result["warnings"])

    def test_no_process_element(self) -> None:
        result = validate_all(XML_NO_PROCESS)
        assert any("process" in e.lower() for e in result["errors"])


# ── Testes unitários por regra ─────────────────────────────────────────────────

class TestValidateXmlWellFormed:

    def test_valid_returns_empty(self) -> None:
        assert validate_xml_well_formed(VALID_XML) == []

    def test_malformed_returns_error(self) -> None:
        errors = validate_xml_well_formed(XML_MALFORMED)
        assert len(errors) == 1
        assert "mal-formado" in errors[0].lower()


class TestValidateProcessExists:

    def test_valid_has_one_process(self) -> None:
        assert validate_process_exists(_root(VALID_XML)) == []

    def test_no_process_returns_error(self) -> None:
        errors = validate_process_exists(_root(XML_NO_PROCESS))
        assert len(errors) == 1
        assert "process" in errors[0].lower()


class TestValidateStartEventExists:

    def test_valid_has_start(self) -> None:
        assert validate_start_event_exists(_root(VALID_XML)) == []

    def test_no_start_returns_error(self) -> None:
        errors = validate_start_event_exists(_root(XML_NO_START))
        assert len(errors) == 1
        assert "startEvent" in errors[0]


class TestValidateEndEventExists:

    def test_valid_has_end(self) -> None:
        assert validate_end_event_exists(_root(VALID_XML)) == []

    def test_no_end_returns_error(self) -> None:
        errors = validate_end_event_exists(_root(XML_NO_END))
        assert len(errors) == 1
        assert "endEvent" in errors[0]


class TestValidateSequenceFlowExists:

    def test_valid_has_flows(self) -> None:
        assert validate_sequence_flow_exists(_root(VALID_XML)) == []

    def test_no_flows_returns_error(self) -> None:
        errors = validate_sequence_flow_exists(_root(XML_NO_FLOWS))
        assert len(errors) == 1
        assert "sequenceFlow" in errors[0]


class TestValidateDuplicateIds:

    def test_no_duplicates(self) -> None:
        assert validate_duplicate_ids(_root(VALID_XML)) == []

    def test_duplicate_id_returns_error(self) -> None:
        errors = validate_duplicate_ids(_root(XML_DUPLICATE_IDS))
        assert len(errors) >= 1
        assert any("start_1" in e for e in errors)


class TestValidateStartEventNotTarget:

    def test_valid_xml_passes(self) -> None:
        assert validate_start_event_not_target(_root(VALID_XML)) == []

    def test_start_as_target_returns_error(self) -> None:
        errors = validate_start_event_not_target(_root(XML_START_AS_TARGET))
        assert len(errors) >= 1
        assert any("startEvent" in e for e in errors)


class TestValidateEndEventNotSource:

    def test_valid_xml_passes(self) -> None:
        assert validate_end_event_not_source(_root(VALID_XML)) == []

    def test_end_as_source_returns_error(self) -> None:
        errors = validate_end_event_not_source(_root(XML_END_AS_SOURCE))
        assert len(errors) >= 1
        assert any("endEvent" in e for e in errors)


class TestValidateNodeConnectivity:

    def test_valid_xml_no_warnings(self) -> None:
        assert validate_node_connectivity(_root(VALID_XML)) == []

    def test_invalid_ref_returns_warning(self) -> None:
        warnings = validate_node_connectivity(_root(XML_BAD_REFS))
        assert len(warnings) >= 1
        assert any("nao_existe_999" in w for w in warnings)


class TestValidateGatewayOutgoing:

    def test_valid_gateway_two_outgoing(self) -> None:
        assert validate_gateway_outgoing(_root(VALID_XML)) == []

    def test_gateway_one_outgoing_returns_warning(self) -> None:
        warnings = validate_gateway_outgoing(_root(XML_GW_ONE_OUT))
        assert len(warnings) == 1
        assert "gw_1" in warnings[0]


# ── Testes do ValidationAgent ─────────────────────────────────────────────────

class TestValidationAgent:

    def _make_state(self, xml: str) -> ProcessModel:
        state = ProcessModel(raw_input="test")
        state.bpmn_xml = xml
        return state

    def test_valid_bpmn_sets_is_valid_true(self) -> None:
        agent = ValidationAgent()
        state = self._make_state(VALID_XML)
        result = agent.run(state)
        assert result.validation["is_valid"] is True
        assert result.validation["errors"] == []

    def test_invalid_bpmn_sets_is_valid_false(self) -> None:
        agent = ValidationAgent()
        state = self._make_state(XML_NO_START)
        result = agent.run(state)
        assert result.validation["is_valid"] is False
        assert len(result.validation["errors"]) >= 1

    def test_empty_bpmn_xml_returns_error(self) -> None:
        agent = ValidationAgent()
        state = ProcessModel(raw_input="test")  # bpmn_xml == ""
        result = agent.run(state)
        assert result.validation["is_valid"] is False
        assert any("vazio" in e.lower() for e in result.validation["errors"])

    def test_warnings_do_not_invalidate(self) -> None:
        agent = ValidationAgent()
        state = self._make_state(XML_GW_ONE_OUT)
        result = agent.run(state)
        # XML_GW_ONE_OUT só tem warnings, não erros
        assert result.validation["is_valid"] is True
        assert len(result.validation["warnings"]) >= 1

    def test_agent_does_not_raise_on_malformed_xml(self) -> None:
        agent = ValidationAgent()
        state = self._make_state(XML_MALFORMED)
        # Não deve lançar exceção
        result = agent.run(state)
        assert result.validation["is_valid"] is False