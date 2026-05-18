"""
Regras de validação estrutural para BPMN 2.0.

Todas as funções são determinísticas — sem LLM.
Cada regra recebe a raiz do XML já parseada (lxml Element) e retorna
uma lista de strings com mensagens de erro ou warning.

A função principal `validate_all` recebe a string XML, aplica todas
as regras e retorna um dicionário {"errors": [...], "warnings": [...]}.
"""

from __future__ import annotations

from collections import Counter
from lxml import etree

BPMN_NS = "http://www.omg.org/spec/BPMN/20100524/MODEL"
NS = {"bpmn": BPMN_NS}

# Tipos de nós que podem ser source/target em sequenceFlows
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


def _all_nodes(root: etree._Element) -> dict[str, str]:
    """Retorna mapeamento id → tag de todos os nós do processo."""
    result: dict[str, str] = {}
    for tag in _NODE_TAGS:
        for el in root.findall(f".//bpmn:{tag}", NS):
            node_id = el.get("id")
            if node_id:
                result[node_id] = tag
    return result


# ── Regra 1 ───────────────────────────────────────────────────────────────────

def validate_xml_well_formed(xml_string: str) -> list[str]:
    """
    Verifica se a string XML é bem-formada.

    Args:
        xml_string: Conteúdo XML como string.

    Returns:
        Lista vazia se válido; lista com um erro se mal-formado.
    """
    try:
        etree.fromstring(xml_string.encode("utf-8"))
        return []
    except etree.XMLSyntaxError as e:
        return [f"XML mal-formado: {e}"]


# ── Regra 2 ───────────────────────────────────────────────────────────────────

def validate_process_exists(root: etree._Element) -> list[str]:
    """
    Verifica se há exatamente 1 elemento <process> dentro de <definitions>.

    Args:
        root: Elemento raiz (<definitions>) já parseado.

    Returns:
        Lista de erros encontrados.
    """
    processes = root.findall("bpmn:process", NS)
    if len(processes) == 0:
        return ["Nenhum elemento <process> encontrado em <definitions>."]
    if len(processes) > 1:
        return [
            f"Encontrado(s) {len(processes)} elemento(s) <process>; "
            "esperado exatamente 1."
        ]
    return []


# ── Regra 3 ───────────────────────────────────────────────────────────────────

def validate_start_event_exists(root: etree._Element) -> list[str]:
    """
    Verifica se há pelo menos 1 <startEvent> no processo.

    Args:
        root: Elemento raiz (<definitions>) já parseado.

    Returns:
        Lista de erros encontrados.
    """
    starts = root.findall(".//bpmn:startEvent", NS)
    if not starts:
        return [
            "Nenhum <startEvent> encontrado. "
            "Todo processo BPMN deve ter ao menos um evento de início."
        ]
    return []


# ── Regra 4 ───────────────────────────────────────────────────────────────────

def validate_end_event_exists(root: etree._Element) -> list[str]:
    """
    Verifica se há pelo menos 1 <endEvent> no processo.

    Args:
        root: Elemento raiz (<definitions>) já parseado.

    Returns:
        Lista de erros encontrados.
    """
    ends = root.findall(".//bpmn:endEvent", NS)
    if not ends:
        return [
            "Nenhum <endEvent> encontrado. "
            "Todo processo BPMN deve ter ao menos um evento de fim."
        ]
    return []


# ── Regra 5 ───────────────────────────────────────────────────────────────────

def validate_sequence_flow_exists(root: etree._Element) -> list[str]:
    """
    Verifica se há pelo menos 1 <sequenceFlow> no processo.

    Args:
        root: Elemento raiz (<definitions>) já parseado.

    Returns:
        Lista de erros encontrados.
    """
    flows = root.findall(".//bpmn:sequenceFlow", NS)
    if not flows:
        return [
            "Nenhum <sequenceFlow> encontrado. "
            "Os elementos do processo não estão conectados."
        ]
    return []


# ── Regra 6 ───────────────────────────────────────────────────────────────────

def validate_node_connectivity(root: etree._Element) -> list[str]:
    """
    Verifica se todo sourceRef/targetRef referencia um id existente no processo.

    Args:
        root: Elemento raiz (<definitions>) já parseado.

    Returns:
        Lista de warnings para referências inválidas.
    """
    known_ids = set(_all_nodes(root).keys())
    warnings: list[str] = []

    for flow in root.findall(".//bpmn:sequenceFlow", NS):
        flow_id = flow.get("id", "<sem id>")
        source = flow.get("sourceRef", "")
        target = flow.get("targetRef", "")

        if source and source not in known_ids:
            warnings.append(
                f"sequenceFlow '{flow_id}': sourceRef '{source}' não referencia "
                "nenhum elemento conhecido no processo."
            )
        if target and target not in known_ids:
            warnings.append(
                f"sequenceFlow '{flow_id}': targetRef '{target}' não referencia "
                "nenhum elemento conhecido no processo."
            )

    return warnings


# ── Regra 7 ───────────────────────────────────────────────────────────────────

def validate_duplicate_ids(root: etree._Element) -> list[str]:
    """
    Verifica se há IDs duplicados em qualquer elemento do XML.

    Args:
        root: Elemento raiz (<definitions>) já parseado.

    Returns:
        Lista de erros para cada ID duplicado encontrado.
    """
    all_ids = [el.get("id") for el in root.iter() if el.get("id")]
    counts = Counter(all_ids)
    errors: list[str] = []
    for id_val, count in counts.items():
        if count > 1:
            errors.append(
                f"ID duplicado encontrado: '{id_val}' aparece {count} vezes no XML."
            )
    return errors


# ── Regra 8 ───────────────────────────────────────────────────────────────────

def validate_gateway_outgoing(root: etree._Element) -> list[str]:
    """
    Verifica se todo <exclusiveGateway> tem pelo menos 2 saídas (sequenceFlows
    cujo sourceRef aponta para o gateway).

    Args:
        root: Elemento raiz (<definitions>) já parseado.

    Returns:
        Lista de warnings para gateways com menos de 2 saídas.
    """
    flows = root.findall(".//bpmn:sequenceFlow", NS)
    warnings: list[str] = []

    for gw in root.findall(".//bpmn:exclusiveGateway", NS):
        gw_id = gw.get("id", "<sem id>")
        gw_name = gw.get("name", gw_id)
        outgoing = [f for f in flows if f.get("sourceRef") == gw_id]
        if len(outgoing) < 2:
            warnings.append(
                f"exclusiveGateway '{gw_name}' (id='{gw_id}') tem {len(outgoing)} "
                "saída(s); esperado ≥ 2 para um gateway exclusivo."
            )

    return warnings


# ── Regra 9 ───────────────────────────────────────────────────────────────────

def validate_start_event_not_target(root: etree._Element) -> list[str]:
    """
    Verifica se nenhum <sequenceFlow> tem targetRef apontando para um <startEvent>.

    Args:
        root: Elemento raiz (<definitions>) já parseado.

    Returns:
        Lista de erros encontrados.
    """
    start_ids = {el.get("id") for el in root.findall(".//bpmn:startEvent", NS)}
    errors: list[str] = []

    for flow in root.findall(".//bpmn:sequenceFlow", NS):
        target = flow.get("targetRef", "")
        if target in start_ids:
            flow_id = flow.get("id", "<sem id>")
            errors.append(
                f"sequenceFlow '{flow_id}' aponta para startEvent '{target}'. "
                "Eventos de início não podem ser alvo de fluxos."
            )

    return errors


# ── Regra 10 ──────────────────────────────────────────────────────────────────

def validate_end_event_not_source(root: etree._Element) -> list[str]:
    """
    Verifica se nenhum <sequenceFlow> tem sourceRef apontando para um <endEvent>.

    Args:
        root: Elemento raiz (<definitions>) já parseado.

    Returns:
        Lista de erros encontrados.
    """
    end_ids = {el.get("id") for el in root.findall(".//bpmn:endEvent", NS)}
    errors: list[str] = []

    for flow in root.findall(".//bpmn:sequenceFlow", NS):
        source = flow.get("sourceRef", "")
        if source in end_ids:
            flow_id = flow.get("id", "<sem id>")
            errors.append(
                f"sequenceFlow '{flow_id}' parte de endEvent '{source}'. "
                "Eventos de fim não podem ser origem de fluxos."
            )

    return errors


# ── Ponto de entrada principal ────────────────────────────────────────────────

def validate_all(xml_string: str) -> dict[str, list[str]]:
    """
    Aplica todas as 10 regras de validação sobre o XML BPMN fornecido.

    Erros (errors) tornam o BPMN inválido e devem ser corrigidos.
    Avisos (warnings) são informativos e não bloqueiam o uso do BPMN.

    Args:
        xml_string: Conteúdo XML BPMN como string.

    Returns:
        Dicionário com chaves "errors" e "warnings", cada uma
        contendo uma lista de strings descritivas.
    """
    errors: list[str] = []
    warnings: list[str] = []

    # Regra 1: XML bem-formado (opera sobre a string, não o elemento)
    well_formed_errors = validate_xml_well_formed(xml_string)
    if well_formed_errors:
        errors.extend(well_formed_errors)
        # Não há como continuar sem um XML parseável
        return {"errors": errors, "warnings": warnings}

    root = etree.fromstring(xml_string.encode("utf-8"))

    # Regras 2–10: operam sobre o elemento raiz
    errors.extend(validate_process_exists(root))
    errors.extend(validate_start_event_exists(root))
    errors.extend(validate_end_event_exists(root))
    errors.extend(validate_sequence_flow_exists(root))
    errors.extend(validate_duplicate_ids(root))
    errors.extend(validate_start_event_not_target(root))
    errors.extend(validate_end_event_not_source(root))

    warnings.extend(validate_node_connectivity(root))
    warnings.extend(validate_gateway_outgoing(root))

    return {"errors": errors, "warnings": warnings}