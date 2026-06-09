"""
RenderAgent — agente de renderização BPMN.

Recebe o bpmn_xml do ProcessModel e gera um arquivo HTML autocontido
usando bpmn-js (open-source, Camunda) carregado via CDN.

Este agente NÃO usa LLM — é puramente determinístico.

Saída: data/outputs/rendered/<process_id>.html
"""

from __future__ import annotations

import logging
import webbrowser
from pathlib import Path

from src.agents.base_agent import BaseAgent
from src.pipeline.state import ProcessModel

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_OUTPUT_DIR = _PROJECT_ROOT / "data" / "outputs" / "rendered"

_HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8" />
  <title>BPMN Viewer — {process_id}</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: sans-serif; background: #f5f5f5; }}
    #header {{
      padding: 12px 20px;
      background: #1a56db;
      color: #fff;
      font-size: 14px;
      display: flex;
      align-items: center;
      gap: 10px;
    }}
    #canvas {{
      width: 100vw;
      height: calc(100vh - 44px);
      background: #fff;
    }}
    .bjs-powered-by {{ display: none; }}
  </style>
</head>
<body>
  <div id="header">
    <strong>BPMN Viewer</strong>
    <span style="opacity:.7">process_id: {process_id}</span>
  </div>
  <div id="canvas"></div>

  <script src="https://unpkg.com/bpmn-js@17/dist/bpmn-viewer.development.js"></script>
  <script>
    var xml = {xml_json};

    var viewer = new BpmnJS({{ container: '#canvas' }});

    viewer.importXML(xml).then(function(result) {{
      var warnings = result.warnings;
      if (warnings.length) console.warn('bpmn-js warnings:', warnings);
      viewer.get('canvas').zoom('fit-viewport');
    }}).catch(function(err) {{
      document.getElementById('canvas').innerHTML =
        '<pre style="color:red;padding:20px">' + err.message + '</pre>';
      console.error('Erro ao importar BPMN:', err);
    }});
  </script>
</body>
</html>
"""


class RenderAgent(BaseAgent):
    """
    Gera um HTML autocontido que renderiza o BPMN via bpmn-js (CDN).

    Salva o arquivo em data/outputs/rendered/<process_id>.html e,
    opcionalmente, abre no browser padrão do sistema.
    """

    def __init__(self, open_browser: bool = False) -> None:
        self._open_browser = open_browser

    def run(self, state: ProcessModel) -> ProcessModel:
        """
        Args:
            state: ProcessModel com bpmn_xml preenchido.

        Returns:
            ProcessModel com rendered_html_path preenchido.

        Raises:
            RuntimeError: Se bpmn_xml estiver vazio.
        """
        if not state.bpmn_xml:
            raise RuntimeError("RenderAgent: bpmn_xml está vazio — nada a renderizar.")

        _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        output_path = _OUTPUT_DIR / f"{state.process_id}.html"

        import json
        xml_json = json.dumps(state.bpmn_xml)

        html = _HTML_TEMPLATE.format(
            process_id=state.process_id,
            xml_json=xml_json,
        )

        output_path.write_text(html, encoding="utf-8")
        state.rendered_html_path = str(output_path)

        logger.info("RenderAgent: HTML salvo em %s", output_path)

        if self._open_browser:
            webbrowser.open(output_path.as_uri())
            logger.info("RenderAgent: abrindo no browser.")

        return state
