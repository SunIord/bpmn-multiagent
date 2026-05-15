"""
LLM Provider — camada de abstração para chamadas ao modelo de linguagem.

Usa Ollama como provedor local. Para trocar de provedor,
adicione um novo bloco em generate().
"""

from __future__ import annotations

from typing import Optional


class LLMProviderError(Exception):
    """Erro lançado quando a chamada ao LLM falha."""


def generate(
    prompt: str,
    model: str = "mistral",
    system: Optional[str] = None,
    temperature: float = 0.0,
) -> str:
    """
    Chama o LLM via Ollama e retorna o texto da resposta.

    Args:
        prompt:      Mensagem principal do usuário.
        model:       Modelo Ollama instalado. Padrão: "mistral".
        system:      Instrução de sistema opcional.
        temperature: Grau de aleatoriedade. 0.0 = determinístico.

    Returns:
        Texto da resposta do modelo como string.

    Raises:
        LLMProviderError: Se o Ollama não estiver rodando ou a chamada falhar.
    """
    try:
        import ollama
    except ImportError:
        raise LLMProviderError(
            "Biblioteca 'ollama' não instalada. Execute: pip install ollama"
        )

    messages: list[dict[str, str]] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    try:
        response = ollama.chat(model=model, messages=messages)
        content = response.get("message", {}).get("content", "")
        if not content:
            raise LLMProviderError("O modelo retornou uma resposta vazia.")
        return content
    except Exception as e:
        if "connection refused" in str(e).lower():
            raise LLMProviderError(
                "Ollama não está rodando. Execute 'ollama serve' em outro terminal."
            ) from e
        raise LLMProviderError(f"Erro na chamada ao Ollama: {e}") from e