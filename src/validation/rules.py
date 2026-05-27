from __future__ import annotations

from collections import Counter, defaultdict
from lxml import etree

BPMN_NS = "http://www.omg.org/spec/BPMN/20100524/MODEL"

NS = {
    "bpmn": BPMN_NS,
    "bpmndi": "http://www.omg.org/spec/BPMN/20100524/DI",
}

_NODE_TAGS = (
    "startEvent",
    "endEvent",
    "task",
    "userTask",
    "serviceTask",
    "exclusiveGateway",
    "parallelGateway",
    "inclusiveGateway",
    "intermediateThrowEvent",
    "intermediateCatchEvent",
)


def _all_nodes(root):
    result = {}

    for tag in _NODE_TAGS:
        for el in root.findall(f".//bpmn:{tag}", NS):
            node_id = el.get("id")

            if node_id:
                result[node_id] = tag

    return result


# =========================================================
# XML WELL FORMED
# =========================================================

def validate_xml_well_formed(xml_string):

    try:
        etree.fromstring(xml_string.encode("utf-8"))
        return []

    except etree.XMLSyntaxError as e:
        return [f"XML mal-formado: {e}"]


# =========================================================
# PROCESS EXISTS
# =========================================================

def validate_process_exists(root):

    processes = root.findall("bpmn:process", NS)

    if not processes:
        return ["Nenhum <process> encontrado."]

    if len(processes) > 1:
        return ["Mais de um <process> encontrado."]

    return []


# =========================================================
# START EVENT
# =========================================================

def validate_start_event_exists(root):

    starts = root.findall(".//bpmn:startEvent", NS)

    if not starts:
        return ["Nenhum startEvent encontrado."]

    return []


# =========================================================
# END EVENT
# =========================================================

def validate_end_event_exists(root):

    ends = root.findall(".//bpmn:endEvent", NS)

    if not ends:
        return ["Nenhum endEvent encontrado."]

    return []


# =========================================================
# SEQUENCE FLOWS
# =========================================================

def validate_sequence_flow_exists(root):

    flows = root.findall(".//bpmn:sequenceFlow", NS)

    if not flows:
        return ["Nenhum sequenceFlow encontrado."]

    return []


# =========================================================
# DUPLICATE IDS
# =========================================================

def validate_duplicate_ids(root):

    all_ids = [el.get("id") for el in root.iter() if el.get("id")]

    counts = Counter(all_ids)

    errors = []

    for id_val, count in counts.items():

        if count > 1:
            errors.append(
                f"ID duplicado: '{id_val}' aparece {count} vezes."
            )

    return errors


# =========================================================
# INVALID REFERENCES
# =========================================================

def validate_node_connectivity(root):

    known_ids = set(_all_nodes(root).keys())

    errors = []

    for flow in root.findall(".//bpmn:sequenceFlow", NS):

        source = flow.get("sourceRef")
        target = flow.get("targetRef")

        if source not in known_ids:
            errors.append(
                f"sourceRef inválido: '{source}'"
            )

        if target not in known_ids:
            errors.append(
                f"targetRef inválido: '{target}'"
            )

    return errors


# =========================================================
# ORPHAN NODES
# =========================================================

def validate_orphan_nodes(root):

    flows = root.findall(".//bpmn:sequenceFlow", NS)

    incoming = set()
    outgoing = set()

    for flow in flows:
        incoming.add(flow.get("targetRef"))
        outgoing.add(flow.get("sourceRef"))

    warnings = []

    for node_id, tag in _all_nodes(root).items():

        if tag == "startEvent":
            continue

        if tag == "endEvent":
            continue

        if node_id not in incoming and node_id not in outgoing:
            warnings.append(
                f"Nó órfão detectado: '{node_id}'"
            )

    return warnings


# =========================================================
# START EVENT TARGET
# =========================================================

def validate_start_event_not_target(root):

    start_ids = {
        el.get("id")
        for el in root.findall(".//bpmn:startEvent", NS)
    }

    errors = []

    for flow in root.findall(".//bpmn:sequenceFlow", NS):

        target = flow.get("targetRef")

        if target in start_ids:
            errors.append(
                f"Fluxo aponta para startEvent '{target}'"
            )

    return errors


# =========================================================
# END EVENT SOURCE
# =========================================================

def validate_end_event_not_source(root):

    end_ids = {
        el.get("id")
        for el in root.findall(".//bpmn:endEvent", NS)
    }

    errors = []

    for flow in root.findall(".//bpmn:sequenceFlow", NS):

        source = flow.get("sourceRef")

        if source in end_ids:
            errors.append(
                f"Fluxo saindo de endEvent '{source}'"
            )

    return errors


# =========================================================
# START EVENTS NEED OUTPUT
# =========================================================

def validate_start_event_outgoing(root):

    flows = root.findall(".//bpmn:sequenceFlow", NS)

    errors = []

    for start in root.findall(".//bpmn:startEvent", NS):

        start_id = start.get("id")

        outgoing = [
            f for f in flows
            if f.get("sourceRef") == start_id
        ]

        if not outgoing:
            errors.append(
                f"startEvent '{start_id}' não possui saída."
            )

    return errors


# =========================================================
# END EVENTS NEED INPUT
# =========================================================

def validate_end_event_incoming(root):

    flows = root.findall(".//bpmn:sequenceFlow", NS)

    errors = []

    for end in root.findall(".//bpmn:endEvent", NS):

        end_id = end.get("id")

        incoming = [
            f for f in flows
            if f.get("targetRef") == end_id
        ]

        if not incoming:
            errors.append(
                f"endEvent '{end_id}' não possui entrada."
            )

    return errors


# =========================================================
# GATEWAY OUTPUTS
# =========================================================

def validate_gateway_outgoing(root):

    flows = root.findall(".//bpmn:sequenceFlow", NS)

    warnings = []

    for gw in root.findall(".//bpmn:exclusiveGateway", NS):

        gw_id = gw.get("id")

        outgoing = [
            f for f in flows
            if f.get("sourceRef") == gw_id
        ]

        if len(outgoing) < 2:
            warnings.append(
                f"Gateway '{gw_id}' possui menos de 2 saídas."
            )

    return warnings


# =========================================================
# DUPLICATE FLOWS
# =========================================================

def validate_duplicate_flows(root):

    pairs = []

    errors = []

    for flow in root.findall(".//bpmn:sequenceFlow", NS):

        pair = (
            flow.get("sourceRef"),
            flow.get("targetRef"),
        )

        if pair in pairs:
            errors.append(
                f"Fluxo duplicado: {pair}"
            )

        pairs.append(pair)

    return errors


# =========================================================
# BPMNDI EXISTS
# =========================================================

def validate_bpmndi_exists(root):

    diagrams = root.findall(".//bpmndi:BPMNDiagram", NS)

    if not diagrams:
        return [
            "BPMNDI ausente — diagrama não poderá ser renderizado visualmente."
        ]

    return []


# =========================================================
# MAIN VALIDATOR
# =========================================================

def validate_all(xml_string):

    errors = []
    warnings = []

    wf_errors = validate_xml_well_formed(xml_string)

    if wf_errors:
        return {
            "errors": wf_errors,
            "warnings": [],
        }

    root = etree.fromstring(xml_string.encode("utf-8"))

    errors.extend(validate_process_exists(root))
    errors.extend(validate_start_event_exists(root))
    errors.extend(validate_end_event_exists(root))
    errors.extend(validate_sequence_flow_exists(root))
    errors.extend(validate_duplicate_ids(root))
    errors.extend(validate_node_connectivity(root))
    errors.extend(validate_start_event_not_target(root))
    errors.extend(validate_end_event_not_source(root))
    errors.extend(validate_start_event_outgoing(root))
    errors.extend(validate_end_event_incoming(root))
    errors.extend(validate_duplicate_flows(root))

    warnings.extend(validate_gateway_outgoing(root))
    warnings.extend(validate_orphan_nodes(root))
    warnings.extend(validate_bpmndi_exists(root))

    return {
        "errors": errors,
        "warnings": warnings,
    }