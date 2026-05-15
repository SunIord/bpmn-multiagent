"""
Teste do pipeline multiagente.

Lê as fixtures de entrada, executa o pipeline completo (ExtractionAgent →
ModelingAgent → BPMNAgent) para cada processo e salva os XMLs em
data/outputs/multiagent/. Em seguida, valida a boa formação de cada XML
com lxml e imprime um relatório de observações.

Execução:
    python tests/test_multiagent.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Garante que a raiz do projeto esteja no sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.pipeline.orchestrator import run_pipeline  # noqa: E402

# Caminhos
FIXTURES_PATH = PROJECT_ROOT / "tests" / "fixtures" / "sample_input.txt"
OUTPUT_DIR = PROJECT_ROOT / "data" / "outputs" / "multiagent"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Tags BPMN que verificamos na análise básica
BPMN_TAGS_TO_CHECK: list[tuple[str, str]] = [
    ("startEvent", "startEvent"),
    ("endEvent", "endEvent"),
    ("task", "task"),
    ("exclusiveGateway", "exclusiveGateway"),
    ("sequenceFlow", "sequenceFlow"),
]


def load_fixtures(path: Path) -> list[str]:
    """Lê o arquivo de fixtures e retorna a lista de descrições de processo."""
    content = path.read_text(encoding="utf-8")
    return [bloco.strip() for bloco in content.split("---") if bloco.strip()]


def check_xml(xml_str: str) -> dict[str, object]:
    """
    Valida a boa formação do XML e verifica presença de tags BPMN.

    Returns:
        Dicionário com 'bem_formado' (bool), 'erro' (str|None) e
        contagens de cada tag verificada.
    """
    result: dict[str, object] = {"bem_formado": False, "erro": None}

    try:
        from lxml import etree

        root = etree.fromstring(xml_str.encode("utf-8"))
        result["bem_formado"] = True

        ns = {"bpmn": "http://www.omg.org/spec/BPMN/20100524/MODEL"}

        for tag_name, _ in BPMN_TAGS_TO_CHECK:
            with_ns = root.findall(f".//bpmn:{tag_name}", ns)
            without_ns = root.findall(f".//{tag_name}")
            count = len(with_ns) or len(without_ns)
            result[tag_name] = count

    except ImportError:
        result["erro"] = "lxml não instalado"
    except Exception as exc:
        result["erro"] = str(exc)

    return result


def print_report(processo_num: int, output_path: Path, analysis: dict[str, object]) -> None:
    """Imprime o relatório de observações de um processo."""
    print(f"\n{'='*60}")
    print(f"  Processo {processo_num}: {output_path.name}")
    print(f"{'='*60}")

    bem_formado: bool = bool(analysis.get("bem_formado"))
    erro: str | None = analysis.get("erro")  # type: ignore[assignment]

    print(f"  XML bem formado : {'✓ sim' if bem_formado else '✗ não'}")
    if erro:
        print(f"  Erro de parse   : {erro}")

    if bem_formado:
        for tag_name, label in BPMN_TAGS_TO_CHECK:
            count = analysis.get(tag_name, 0)
            presente = "sim" if count else "não"
            print(f"  {label:<20}: {presente} ({count} elemento(s))")

    print(f"  Arquivo salvo   : {output_path}")


def main() -> None:
    print("=" * 60)
    print("  PIPELINE MULTIAGENTE — Geração de BPMN")
    print("=" * 60)

    if not FIXTURES_PATH.exists():
        print(f"\n[ERRO] Arquivo de fixtures não encontrado: {FIXTURES_PATH}")
        sys.exit(1)

    processos = load_fixtures(FIXTURES_PATH)
    print(f"\n{len(processos)} processo(s) carregado(s) de {FIXTURES_PATH.name}\n")

    for i, descricao in enumerate(processos, start=1):
        output_path = OUTPUT_DIR / f"processo{i}_multiagent.xml"
        print(f"[{i}/{len(processos)}] Executando pipeline multiagente para o Processo {i}...")
        print(f"       Descrição: {descricao[:80].replace(chr(10), ' ')}...")

        try:
            state = run_pipeline(descricao)
            xml = state.bpmn_xml

            if not xml:
                print("  [ERRO] Pipeline concluído, mas bpmn_xml está vazio.")
                continue

            output_path.write_text(xml, encoding="utf-8")
            analysis = check_xml(xml)
            print_report(i, output_path, analysis)

        except Exception as exc:
            print(f"  [ERRO] Falha durante a execução do pipeline: {exc}")

    print(f"\n{'='*60}")
    print(f"  Concluído. Arquivos em: {OUTPUT_DIR}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()