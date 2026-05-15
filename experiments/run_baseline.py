"""
Experimento — Baseline Monolítico (one-shot).

Processa todos os arquivos .txt em data/inputs/freetext/ usando o pipeline
monolítico e salva os XMLs gerados em data/outputs/baseline/.

Execução:
    python experiments/run_baseline.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Garante que a raiz do projeto esteja no sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.baseline.monolithic import run_monolithic  # noqa: E402

# Caminhos
INPUT_DIR = PROJECT_ROOT / "data" / "inputs" / "freetext"
OUTPUT_DIR = PROJECT_ROOT / "data" / "outputs" / "baseline"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def main() -> None:
    print("=" * 60)
    print("  EXPERIMENTO — Baseline Monolítico (one-shot)")
    print("=" * 60)

    if not INPUT_DIR.exists():
        print(f"\n[ERRO] Diretório de entrada não encontrado: {INPUT_DIR}")
        sys.exit(1)

    txt_files = sorted(INPUT_DIR.glob("*.txt"))
    if not txt_files:
        print(f"\n[ERRO] Nenhum arquivo .txt encontrado em: {INPUT_DIR}")
        sys.exit(1)

    print(f"\n{len(txt_files)} arquivo(s) encontrado(s) em {INPUT_DIR.name}\n")

    sucessos = 0
    erros = 0

    for txt_file in txt_files:
        output_path = OUTPUT_DIR / f"{txt_file.stem}_baseline.xml"
        print(f"[{sucessos + erros + 1}/{len(txt_files)}] {txt_file.name}...", end=" ")

        try:
            text = txt_file.read_text(encoding="utf-8").strip()
            xml = run_monolithic(text)
            output_path.write_text(xml, encoding="utf-8")
            print("✓ OK")
            sucessos += 1
        except Exception as exc:
            print(f"✗ ERRO: {exc}")
            erros += 1

    print(f"\n{'=' * 60}")
    print(f"  Processados: {sucessos + erros}")
    print(f"  Sucesso    : {sucessos}")
    print(f"  Erros      : {erros}")
    print(f"  Saídas em  : {OUTPUT_DIR}")
    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    main()