"""
BaseAgent — classe abstrata que todos os agentes do pipeline herdam.

Define o contrato mínimo de interface (método run) e fornece utilitários
comuns como carregamento de arquivos de prompt.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from src.pipeline.state import ProcessModel

# Raiz do projeto: src/agents/base_agent.py → src/ → raiz
_PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent.parent
_PROMPTS_DIR: Path = _PROJECT_ROOT / "prompts"


class BaseAgent(ABC):
    """
    Classe base para todos os agentes do pipeline bpmn-multiagent.

    Cada agente concreto deve implementar `run`, que recebe um `ProcessModel`,
    opera sobre os campos de sua responsabilidade e retorna o estado atualizado.
    """

    @abstractmethod
    def run(self, state: ProcessModel) -> ProcessModel:
        """
        Executa a lógica do agente sobre o estado atual do pipeline.

        Args:
            state: Objeto `ProcessModel` com os campos preenchidos pelos
                   agentes anteriores. O agente lê os campos de sua entrada
                   e escreve nos campos de sua saída.

        Returns:
            O mesmo objeto `ProcessModel` com os campos de saída preenchidos.
        """

    def _load_prompt(self, filename: str) -> str:
        """
        Lê um arquivo de prompt do diretório `prompts/` na raiz do projeto.

        Args:
            filename: Nome do arquivo (ex.: "extraction.txt").

        Returns:
            Conteúdo do arquivo como string.

        Raises:
            FileNotFoundError: Se o arquivo não existir no diretório de prompts.
        """
        path = _PROMPTS_DIR / filename
        if not path.exists():
            raise FileNotFoundError(
                f"Arquivo de prompt não encontrado: {path}\n"
                f"Verifique se '{filename}' existe em prompts/."
            )
        return path.read_text(encoding="utf-8")