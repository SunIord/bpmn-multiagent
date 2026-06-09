"""
Experimento — Pipeline Multiagente.

Executa o pipeline multiagente sobre arquivos de entrada BPMN.

Suporta:
- freetext
- structured
- noisy
- todos os datasets
- escolha individual de arquivo

Execução:
    python experiments/run_multiagent.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# =========================================================
# PATH SETUP
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.pipeline.orchestrator import run_pipeline  # noqa: E402


# =========================================================
# DIRETÓRIOS
# =========================================================

INPUT_BASE = PROJECT_ROOT / "data" / "inputs"

OUTPUT_DIR = PROJECT_ROOT / "data" / "outputs" / "multiagent"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

INPUT_TYPES = {
    "1": "freetext",
    "2": "structured",
    "3": "noisy",
    "4": "all",
}


# =========================================================
# HELPERS
# =========================================================

def collect_files(input_type: str):

    txt_files = []

    if input_type == "all":

        for folder in ["freetext", "structured", "noisy"]:

            folder_path = INPUT_BASE / folder

            txt_files.extend(
                sorted(folder_path.glob("*.txt"))
            )

    else:

        folder_path = INPUT_BASE / input_type

        txt_files.extend(
            sorted(folder_path.glob("*.txt"))
        )

    return txt_files


def print_menu():

    print("\nEscolha o tipo de input:\n")

    print("[1] freetext")
    print("[2] structured")
    print("[3] noisy")
    print("[4] TODOS")
    print("[5] Escolher arquivo específico")


# =========================================================
# MAIN
# =========================================================

def main():

    print("=" * 60)
    print(" EXPERIMENTO — Pipeline Multiagente ")
    print("=" * 60)

    print_menu()

    option = input("\nDigite a opção desejada: ").strip()

    # =====================================================
    # ESCOLHA INDIVIDUAL
    # =====================================================

    if option == "5":

        all_files = []

        for folder in ["freetext", "structured", "noisy"]:

            folder_path = INPUT_BASE / folder

            files = sorted(folder_path.glob("*.txt"))

            for f in files:
                all_files.append(f)

        if not all_files:
            print("\nNenhum arquivo encontrado.")
            sys.exit(1)

        print("\nArquivos disponíveis:\n")

        for idx, file in enumerate(all_files, start=1):
            relative = file.relative_to(PROJECT_ROOT)
            print(f"[{idx}] {relative}")

        try:

            file_option = int(
                input("\nEscolha o arquivo: ").strip()
            )

            selected_file = all_files[file_option - 1]

            txt_files = [selected_file]

        except Exception:
            print("\n[ERRO] Opção inválida.")
            sys.exit(1)

    # =====================================================
    # EXECUÇÃO NORMAL
    # =====================================================

    else:

        input_type = INPUT_TYPES.get(option)

        if not input_type:
            print("\n[ERRO] Opção inválida.")
            sys.exit(1)

        txt_files = collect_files(input_type)

    # =====================================================
    # VALIDAÇÃO
    # =====================================================

    if not txt_files:
        print("\n[ERRO] Nenhum arquivo encontrado.")
        sys.exit(1)

    print(f"\n{len(txt_files)} arquivo(s) encontrado(s).\n")

    successes = 0
    errors = 0

    # =====================================================
    # PROCESSAMENTO
    # =====================================================

    for idx, txt_file in enumerate(txt_files, start=1):

        relative_path = txt_file.relative_to(PROJECT_ROOT)

        print(
            f"[{idx}/{len(txt_files)}] "
            f"{relative_path}...",
            end=" "
        )

        try:

            text = txt_file.read_text(
                encoding="utf-8"
            ).strip()

            state = run_pipeline(text, render=True)

            xml = state.bpmn_xml

            if not xml:
                raise RuntimeError(
                    "bpmn_xml vazio."
                )

            # Nome do output
            folder_name = txt_file.parent.name

            output_name = (
                f"{txt_file.stem}_"
                f"{folder_name}_multiagent.xml"
            )

            output_path = OUTPUT_DIR / output_name

            output_path.write_text(
                xml,
                encoding="utf-8"
            )

            print("✓ OK")

            successes += 1

        except Exception as exc:

            print(f"✗ ERRO: {exc}")

            errors += 1

    # =====================================================
    # RELATÓRIO FINAL
    # =====================================================

    print("\n" + "=" * 60)

    print(f"Processados : {successes + errors}")
    print(f"Sucessos    : {successes}")
    print(f"Erros       : {errors}")

    print(f"\nSaídas em:")
    print(OUTPUT_DIR)

    print("=" * 60 + "\n")


# =========================================================
# ENTRYPOINT
# =========================================================

if __name__ == "__main__":
    main()