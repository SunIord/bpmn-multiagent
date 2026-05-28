# Instalação e Execução

## Pré-requisitos

Antes de executar o projeto, instale:

* Python 3.11+
* Node.js 18+
* npm
* Ollama

---

# 1. Clonar o repositório

```bash
git clone <URL_DO_REPOSITORIO>
cd bpmn-multiagent
```

---

# 2. Configurar ambiente virtual Python

## Linux/macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## Windows (PowerShell)

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

---

# 3. Instalar dependências Python

```bash
pip install -e ".[dev]"
```

---

# 4. Instalar e configurar o Ollama

## Instalação

### Windows

Baixe:

```text
https://ollama.com/download/windows
```

### Linux/macOS

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

---

# 5. Iniciar o Ollama

## Linux/macOS

Abra um terminal separado:

```bash
ollama serve
```

## Windows

O serviço normalmente inicia automaticamente.

---

# 6. Baixar o modelo Mistral

```bash
ollama pull mistral
```

Verificar instalação:

```bash
ollama list
```

Saída esperada:

```text
NAME      ID              SIZE
mistral   xxxxxxxxxxxx    4.4 GB
```

---

# 7. Testar o Ollama

```bash
ollama run mistral "1+1?"
```

---

# 8. Instalar dependências do renderizador BPMN

O projeto utiliza:

* bpmn-js
* Puppeteer
* Chromium Headless

para renderizar automaticamente o BPMN em PNG.

Entre na pasta renderer:

```bash
cd renderer
```

Instale as dependências:

```bash
npm install
```

Isso instalará automaticamente:

* bpmn-js
* puppeteer
* chromium headless

---

# 9. Estrutura esperada do renderizador

```text
renderer/
├── render_bpmn.js
├── package.json
└── node_modules/
```

---

# 10. Executar o pipeline multiagente

Volte para a raiz do projeto:

```bash
cd ..
```

Execute:

```bash
python experiments/run_multiagent.py
```

O sistema perguntará:

* qual dataset deseja executar
* ou qual arquivo específico deseja processar

---

# 11. Fluxo completo do pipeline

```text
Texto
 ↓
ExtractionAgent
 ↓
ModelingAgent
 ↓
BPMNAgent
 ↓
ValidationAgent
 ↓
RefinementAgent
 ↓
RenderAgent
 ↓
XML BPMN + PNG
```

---

# 12. Saídas geradas

## XML BPMN

```text
data/outputs/multiagent/
```

## Renderizações PNG

```text
data/outputs/render/
```

---

# 13. Executar baseline monolítico

```bash
python experiments/run_baseline.py
```

---

# 14. Executar testes

```bash
pytest tests/ -v
```

---

# 15. Tecnologias utilizadas

| Camada                  | Tecnologia |
| ----------------------- | ---------- |
| LLM local               | Ollama     |
| Modelo                  | Mistral    |
| Pipeline multiagente    | LangGraph  |
| Agentes                 | LangChain  |
| XML BPMN                | lxml       |
| Renderização BPMN       | bpmn-js    |
| Screenshot automatizado | Puppeteer  |
| Runtime JS              | Node.js    |

---

# 16. Consumo de memória

O projeto executa:

* Ollama + Mistral (~4 GB RAM)
* Chromium Headless (~300 MB–1.5 GB)

Recomendado:

* mínimo: 8 GB RAM
* ideal: 16 GB RAM

---

# 17. Solução de problemas

| Problema                       | Solução                                          |
| ------------------------------ | ------------------------------------------------ |
| `ollama: command not found`    | Reinstale o Ollama                               |
| `connection refused`           | Execute `ollama serve`                           |
| `model not found`              | Execute `ollama pull mistral`                    |
| `npm: command not found`       | Instale Node.js                                  |
| `Cannot find module 'bpmn-js'` | Execute `npm install` dentro de `renderer/`      |
| `Failed to launch browser`     | Reinstale o Puppeteer: `npm install puppeteer`   |
| PNG não gerado                 | Verifique se o RenderAgent executou corretamente |

---

# 18. Observações

* O projeto roda completamente localmente.
* Nenhuma API paga é utilizada.
* O BPMN é renderizado automaticamente em PNG.
* O pipeline é determinístico após a etapa de modelagem.
