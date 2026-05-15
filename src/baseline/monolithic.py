"""
Baseline monolítico — geração de BPMN via LLM em uma única chamada (one-shot).

Reproduz a abordagem do artigo de referência: o modelo recebe a descrição
do processo e retorna o XML BPMN 2.0 diretamente, sem pipeline multiagente.
"""

from __future__ import annotations

from pathlib import Path

from src.llm.provider import generate

# Localiza o diretório raiz do projeto (dois níveis acima deste arquivo:
# src/baseline/monolithic.py → src/ → raiz)
_PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent.parent
_PROMPT_PATH: Path = _PROJECT_ROOT / "prompts" / "monolithic.txt"


def _load_prompt_template() -> str:
    """Lê o arquivo de prompt e retorna seu conteúdo.

    Raises:
        FileNotFoundError: Se o arquivo de prompt não existir.
    """
    if not _PROMPT_PATH.exists():
        raise FileNotFoundError(
            f"Arquivo de prompt não encontrado: {_PROMPT_PATH}\n"
            "Verifique se 'prompts/monolithic.txt' existe na raiz do projeto."
        )
    return _PROMPT_PATH.read_text(encoding="utf-8")


def _extract_xml(raw: str) -> str:
    """Remove blocos markdown ```xml ... ``` caso o modelo os inclua.

    O prompt instrui o modelo a não incluí-los, mas modelos menores
    frequentemente ignoram essa instrução. Esta limpeza mínima garante
    que o retorno comece em '<'.
    """
    text = raw.strip()

    # Remove fences de código se presentes
    if text.startswith("```"):
        lines = text.splitlines()
        # Remove primeira linha (```xml ou ```) e última (```)
        inner = lines[1:] if lines[0].startswith("```") else lines
        if inner and inner[-1].strip() == "```":
            inner = inner[:-1]
        text = "\n".join(inner).strip()

    return text


def run_monolithic(text: str) -> str:
    """Gera XML BPMN 2.0 a partir de uma descrição textual de processo.

    Carrega o prompt template, substitui o placeholder {DESCRICAO} pelo
    texto fornecido e faz uma única chamada ao LLM (one-shot).

    Args:
        text: Descrição em linguagem natural do processo de negócio.

    Returns:
        String contendo o XML BPMN 2.0 gerado pelo modelo (bruto, sem
        validação de esquema).

    Raises:
        FileNotFoundError: Se o arquivo de prompt não for encontrado.
        LLMProviderError: Se a chamada ao Ollama falhar.
    """
    template: str = _load_prompt_template()
    prompt: str = template.replace("{DESCRICAO}", text.strip())
    raw_output: str = generate(prompt)
    return _extract_xml(raw_output)