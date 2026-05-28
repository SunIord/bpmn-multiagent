"""
RenderAgent — responsável por transformar BPMN XML em SVG e PNG.

Utiliza:
- Node.js
- bpmn-js
- Puppeteer

Não usa LLM.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from src.agents.base_agent import BaseAgent
from src.pipeline.state import ProcessModel


class RenderAgent(BaseAgent):

    def run(self, state: ProcessModel) -> ProcessModel:

        if not state.bpmn_xml:
            raise ValueError(
                "RenderAgent recebeu bpmn_xml vazio."
            )

        project_root = Path(__file__).resolve().parent.parent.parent

        temp_dir = project_root / "data" / "outputs" / "render"
        temp_dir.mkdir(parents=True, exist_ok=True)

        renderer_dir = project_root / "renderer"

        xml_path = temp_dir / "diagram.bpmn"

        xml_path.write_text(
            state.bpmn_xml,
            encoding="utf-8",
        )

        command = [
            "node",
            str(renderer_dir / "render_bpmn.js"),
            str(xml_path),
            str(temp_dir),
        ]

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            raise RuntimeError(
                f"Erro ao renderizar BPMN:\n{result.stderr}"
            )

        state.svg_path = str(temp_dir / "diagram.svg")
        state.png_path = str(temp_dir / "diagram.png")

        return state