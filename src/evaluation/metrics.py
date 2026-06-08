"""
Métricas de avaliação de qualidade de modelos BPMN 2.0.

Baseadas no framework 3C do artigo de referência:
    - Corretude (Correctness)
    - Completude (Completeness)
    - Clareza (Clarity)
    - Variância (Consistency across runs)

Cada métrica retorna um dicionário com:
    - score: float entre 0.0 e 1.0
    - details: dict com breakdown dos componentes avaliados
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
from lxml import etree
from difflib import SequenceMatcher

# Namespace BPMN 2.0
BPMN_NS = "http://www.omg.org/spec/BPMN/20100524/MODEL"
NS = {"bpmn": BPMN_NS}

# Tags BPMN consideradas elementos estruturais
STRUCTURAL_TAGS = [
    "startEvent",
    "endEvent",
    "task",
    "userTask",
    "serviceTask",
    "exclusiveGateway",
    "parallelGateway",
    "inclusiveGateway",
    "sequenceFlow",
    "lane",
    "laneSet",
    "flowNodeRef",
]


def _parse_xml(xml_string: str) -> Optional[etree._Element]:
    """Parse XML string, returning root element or None if invalid."""
    try:
        return etree.fromstring(xml_string.encode("utf-8"))
    except etree.XMLSyntaxError:
        return None


def _get_process_elements(root: etree._Element) -> Dict[str, Any]:
    """Extrai contagens e nomes dos elementos BPMN do XML."""
    counts = {}
    names = {}
    for tag in STRUCTURAL_TAGS:
        elems = root.findall(f".//bpmn:{tag}", NS)
        counts[tag] = len(elems)
        names[tag] = [e.get("name", "").strip().lower() for e in elems if e.get("name", "").strip()]
    return {"counts": counts, "names": names}


def _similarity(a: str, b: str) -> float:
    """Calcula similaridade entre duas strings (0.0 a 1.0)."""
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


# ── Métrica 1: Corretude ─────────────────────────────────────────────────────

def compute_correctness(xml_string: str, ground_truth: Optional[str] = None) -> Dict[str, Any]:
    """
    Avalia a corretude estrutural do XML BPMN.

    Verifica:
    - XML bem-formado
    - Presença de startEvent, endEvent, sequenceFlow
    - IDs únicos
    - Conectividade de sequenceFlows
    - Sem fluxos inválidos (endEvent como source, startEvent como target)

    Args:
        xml_string: XML BPMN gerado.
        ground_truth: Ignorado (corretude é absoluta, não relativa).

    Returns:
        Dict com 'score' (float 0-1) e 'details' com breakdown dos checks.
    """
    checks = {}
    root = _parse_xml(xml_string)

    # Check 1: XML bem-formado
    checks["well_formed"] = root is not None
    if root is None:
        return {"score": 0.0, "details": checks}

    # Check 2: Elementos obrigatórios
    checks["has_start_event"] = len(root.findall(".//bpmn:startEvent", NS)) > 0
    checks["has_end_event"] = len(root.findall(".//bpmn:endEvent", NS)) > 0
    checks["has_sequence_flow"] = len(root.findall(".//bpmn:sequenceFlow", NS)) > 0

    # Check 3: IDs únicos
<<<<<<< HEAD
    all_ids = [el.get("id") for el in root.iter() if el.get("id")]
=======
    # Exclui flowNodeRef (não tem id próprio), laneSet e lane têm IDs únicos legítimos
    excluded_from_id_check = {"flowNodeRef"}
    all_ids = [
        el.get("id")
        for el in root.iter()
        if el.get("id") and el.tag.split("}")[-1] not in excluded_from_id_check
    ]
>>>>>>> 751f48e (feat: métricas realistas com lanes, completude no relatório, aggregate multiagente 0.94 vs baseline 0.55)
    checks["unique_ids"] = len(all_ids) == len(set(all_ids))

    # Check 4: Conectividade e fluxos válidos
    flows = root.findall(".//bpmn:sequenceFlow", NS)
    known_ids = {el.get("id") for el in root.iter() if el.get("id")}
    start_ids = {el.get("id") for el in root.findall(".//bpmn:startEvent", NS)}
    end_ids = {el.get("id") for el in root.findall(".//bpmn:endEvent", NS)}

    connectivity_ok = True
    valid_flows = True

    for flow in flows:
        src = flow.get("sourceRef", "")
        tgt = flow.get("targetRef", "")
        if src not in known_ids or tgt not in known_ids:
            connectivity_ok = False
        if src in end_ids:
            valid_flows = False
        if tgt in start_ids:
            valid_flows = False

    checks["connectivity"] = connectivity_ok
    checks["valid_flows"] = valid_flows

    # Score: todos os checks devem passar
    all_checks = list(checks.values())
    score = sum(1 for c in all_checks if c) / len(all_checks) if all_checks else 0.0

    return {"score": round(score, 4), "details": checks}


# ── Métrica 2: Completude ────────────────────────────────────────────────────

def compute_completeness(xml_string: str, ground_truth: str) -> Dict[str, Any]:
    """
    Avalia a completude comparando os elementos do XML gerado com o ground truth.

    Compara a presença de elementos estruturais (startEvent, endEvent, task,
    gateway, sequenceFlow, lane, laneSet, flowNodeRef) entre o modelo gerado
    e o de referência.

    Args:
        xml_string: XML BPMN gerado.
        ground_truth: XML BPMN de referência (gabarito).

    Returns:
        Dict com 'score' (float 0-1) e 'details' com % por tipo de elemento.
    """
    root_gen = _parse_xml(xml_string)
    root_gt = _parse_xml(ground_truth)

    if root_gen is None or root_gt is None:
        return {"score": 0.0, "details": {"error": "XML inválido no modelo gerado ou ground truth"}}

    gen_elements = _get_process_elements(root_gen)
    gt_elements = _get_process_elements(root_gt)

    details = {}
    ratios = []

    for tag in STRUCTURAL_TAGS:
        gen_count = gen_elements["counts"].get(tag, 0)
        gt_count = gt_elements["counts"].get(tag, 0)

        if gt_count == 0:
            # Se não há no ground truth, não penaliza (tag irrelevante)
            ratio = 1.0
        else:
            # Penaliza tanto excesso quanto falta
            ratio = min(gen_count, gt_count) / max(gen_count, gt_count)

        details[f"{tag}_ratio"] = round(ratio, 4)
        details[f"{tag}_gen"] = gen_count
        details[f"{tag}_gt"] = gt_count
        ratios.append(ratio)

    score = sum(ratios) / len(ratios) if ratios else 0.0

    return {"score": round(score, 4), "details": details}


# ── Métrica 3: Clareza ────────────────────────────────────────────────────────

def compute_clarity(xml_string: str, ground_truth: Optional[str] = None) -> Dict[str, Any]:
    """
    Avalia a clareza dos nomes dos elementos BPMN.

    Verifica:
    - Elementos rotulados (possuem name não vazio)
    - Nomes únicos (sem duplicatas genéricas)
    - Comprimento significativo dos nomes (> 3 caracteres)
    - Se ground_truth fornecido, similaridade semântica dos nomes

    Nota: apenas elementos com semântica de nome são avaliados (inclui lane,
    que carrega o nome do ator). laneSet e flowNodeRef são excluídos pois não
    possuem atributo name significativo.

    Args:
        xml_string: XML BPMN gerado.
        ground_truth: Opcional, XML de referência para comparar nomes.

    Returns:
        Dict com 'score' (float 0-1) e 'details' com métricas de clareza.
    """
    root = _parse_xml(xml_string)
    if root is None:
        return {"score": 0.0, "details": {"error": "XML mal-formado"}}

    # Elementos que devem ter nome (lane incluída: carrega nome do ator)
    # laneSet e flowNodeRef excluídos: não possuem atributo name significativo
    nameable_tags = [
        "startEvent", "endEvent", "task", "userTask", "serviceTask",
        "exclusiveGateway", "parallelGateway", "inclusiveGateway",
        "lane",
    ]

    elements_with_name = []
    total_elements = 0
    unique_names = set()
    meaningful_names = 0
    duplicate_names = 0

    for tag in nameable_tags:
        elems = root.findall(f".//bpmn:{tag}", NS)
        for e in elems:
            total_elements += 1
            name = e.get("name", "").strip()
            if name:
                elements_with_name.append(name)
                if len(name) > 3:
                    meaningful_names += 1
                if name.lower() not in unique_names:
                    unique_names.add(name.lower())
                else:
                    duplicate_names += 1

    if total_elements == 0:
        return {"score": 0.0, "details": {"error": "Nenhum elemento nomeável encontrado"}}

    # Sub-métricas
    labeling_rate = len(elements_with_name) / total_elements
    uniqueness_rate = 1.0 - (duplicate_names / total_elements) if total_elements > 0 else 1.0
    meaningful_rate = meaningful_names / total_elements if total_elements > 0 else 0.0

    details = {
        "labeling_rate": round(labeling_rate, 4),
        "uniqueness_rate": round(uniqueness_rate, 4),
        "meaningful_rate": round(meaningful_rate, 4),
        "total_elements": total_elements,
        "labeled_elements": len(elements_with_name),
    }

    # Similaridade com ground truth (se fornecido)
    if ground_truth:
        root_gt = _parse_xml(ground_truth)
        if root_gt is not None:
            gt_names = []
            for tag in nameable_tags:
                for e in root_gt.findall(f".//bpmn:{tag}", NS):
                    n = e.get("name", "").strip()
                    if n:
                        gt_names.append(n.lower())

            if gt_names and elements_with_name:
                sims = []
                for gn in gt_names:
                    best = max((_similarity(gn, mn) for mn in elements_with_name), default=0.0)
                    sims.append(best)
                name_similarity = sum(sims) / len(sims)
                details["name_similarity_to_gt"] = round(name_similarity, 4)

    score = (labeling_rate + uniqueness_rate + meaningful_rate) / 3

    return {"score": round(score, 4), "details": details}


# ── Métrica 4: Variância ─────────────────────────────────────────────────────

def compute_variance(xml_strings: List[str]) -> Dict[str, Any]:
    """
    Mede a variância entre múltiplas execuções do mesmo input.

    Compara os elementos estruturais entre N execuções e calcula o coeficiente
    de variação médio. Quanto menor a variância, mais consistente é o modelo.

    Args:
        xml_strings: Lista de XMLs gerados (mínimo 2) para o mesmo input.

    Returns:
        Dict com 'score' (float 0-1, onde 1 = idêntico, 0 = totalmente divergente)
        e 'details' com coeficientes de variação por tag.
    """
    if len(xml_strings) < 2:
        return {"score": 1.0, "details": {"error": "Necessário pelo menos 2 execuções"}}

    roots = []
    for xml_str in xml_strings:
        root = _parse_xml(xml_str)
        if root is None:
            return {"score": 0.0, "details": {"error": f"XML inválido em uma das execuções"}}
        roots.append(root)

    # Extrai contagens de cada execução
    all_counts = []
    for root in roots:
        elements = _get_process_elements(root)
        all_counts.append(elements["counts"])

    # Calcula coeficiente de variação por tag
    import statistics
    details = {}
    cv_list = []

    for tag in STRUCTURAL_TAGS:
        counts = [c.get(tag, 0) for c in all_counts]
        mean = statistics.mean(counts)
        if mean == 0:
            cv = 0.0  # Todos são 0, consistência perfeita
        else:
            stdev = statistics.stdev(counts) if len(counts) > 1 else 0.0
            cv = stdev / mean
        details[f"{tag}_cv"] = round(cv, 4)
        details[f"{tag}_counts"] = counts
        cv_list.append(cv)

    # Score: 1 - média dos CVs, limitado a [0, 1]
    avg_cv = sum(cv_list) / len(cv_list) if cv_list else 0.0
    score = max(0.0, 1.0 - avg_cv)

    return {"score": round(score, 4), "details": details}


# ── Métrica agregada ──────────────────────────────────────────────────────────

def compute_all_metrics(
    xml_string: str,
    ground_truth: Optional[str] = None,
    previous_runs: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Calcula todas as métricas disponíveis para um XML BPMN.

    Args:
        xml_string: XML BPMN gerado.
        ground_truth: XML de referência (para completude e clareza).
        previous_runs: Lista de XMLs de execuções anteriores (para variância).

    Returns:
        Dict com scores individuais e score agregado.
    """
    results = {}

    # Corretude (sempre)
    results["correctness"] = compute_correctness(xml_string)

    # Completude (requer ground truth)
    if ground_truth:
        results["completeness"] = compute_completeness(xml_string, ground_truth)

    # Clareza (ground truth opcional)
    results["clarity"] = compute_clarity(xml_string, ground_truth)

    # Variância (requer execuções anteriores)
    if previous_runs and len(previous_runs) >= 1:
        all_runs = previous_runs + [xml_string]
        results["variance"] = compute_variance(all_runs)

    # Score agregado (média dos disponíveis)
    scores = [m["score"] for m in results.values() if "score" in m]
    results["aggregate_score"] = round(sum(scores) / len(scores), 4) if scores else 0.0

    return results