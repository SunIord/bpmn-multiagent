# bpmn-multiagent

> **Multi-agent pipeline for BPMN generation from natural language using LLMs**
> Tópicos Avançados em Engenharia de Software — CIn UFPE

---

# Sobre o Projeto

Este projeto propõe uma evolução sobre a abordagem do artigo *"Do they speak BPMN? Preliminary evaluation of LLMs modeling capabilities based on process model quality measures"*, substituindo a geração monolítica *one-shot* por uma **arquitetura multiagente** que decompõe o problema em etapas especializadas.

## O problema com a abordagem monolítica

Um único LLM executando extração semântica + modelagem lógica + geração BPMN ao mesmo tempo produz:

* Alta taxa de erros semânticos
* Inconsistência entre execuções
* Modelos sem validação formal

## Nossa solução

Um pipeline multiagente especializado:

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
XML BPMN + PNG + SVG
```

Cada agente possui uma responsabilidade específica e compartilha informações através de um estado global (`ProcessModel`).

---

# Arquitetura dos Agentes

| Agente          | Responsabilidade                               |
| --------------- | ---------------------------------------------- |
| ExtractionAgent | Extrai atividades, eventos e gateways do texto |
| ModelingAgent   | Constrói a lógica do processo                  |
| BPMNAgent       | Gera BPMN XML 2.0 de forma determinística      |
| ValidationAgent | Executa validações estruturais BPMN            |
| RefinementAgent | Corrige inconsistências encontradas            |
| RenderAgent     | Gera imagens PNG e SVG a partir do BPMN        |

---

# Stack

| Camada            | Tecnologia         |
| ----------------- | ------------------ |
| Linguagem         | Python             |
| Agentes           | LangChain          |
| Orquestração      | LangGraph          |
| API               | FastAPI            |
| Geração XML       | lxml               |
| Renderização BPMN | bpmn-js            |
| Captura de imagem | Puppeteer          |
| Validação BPMN    | Camunda            |
| Persistência      | PostgreSQL         |
| LLM Local         | Ollama             |
| Modelos           | Mistral / Qwen 2.5 |

---

# Estrutura do Projeto

```text
bpmn-multiagent/
├── docs/
│
├── data/
│   ├── inputs/
│   └── outputs/
│       ├── baseline/
│       ├── multiagent/
│       ├── render/
│       └── debug/
│
├── renderer/
│   ├── package.json
│   ├── render_bpmn.js
│   └── node_modules/
│
├── prompts/
│
├── experiments/
│   ├── run_baseline.py
│   └── run_multiagent.py
│
├── src/
│   ├── agents/
│   │   ├── extraction_agent.py
│   │   ├── modeling_agent.py
│   │   ├── bpmn_agent.py
│   │   ├── validation_agent.py
│   │   ├── refinement_agent.py
│   │   └── render_agent.py
│   │
│   ├── pipeline/
│   ├── llm/
│   ├── validation/
│   └── evaluation/
│
├── tests/
│
└── README.md
```

---

# Requisitos

## Software

* Python 3.11+
* Node.js 20+
* npm
* Ollama

Verifique:

```bash
python --version
node --version
npm --version
ollama --version
```

---

# Instalação

## 1. Clonar o repositório

```bash
git clone https://github.com/SunIord/bpmn-multiagent
cd bpmn-multiagent
```

---

## 2. Criar ambiente virtual

### Windows

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### Linux/macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
```

---

## 3. Instalar dependências Python

```bash
pip install -e ".[dev]"
```

Caso necessário:

```bash
pip install lxml langchain langgraph fastapi requests
```

---

# Configuração do Ollama

## 1. Instalar o Ollama

### Windows

Baixe:

https://ollama.com/download/windows

Verifique:

```powershell
ollama --version
```

### Linux / WSL2

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

Inicie o serviço:

```bash
ollama serve
```

### macOS

Baixe:

https://ollama.com/download

---

## 2. Baixar os modelos

```bash
ollama pull mistral
ollama pull qwen2.5
```

Verificar:

```bash
ollama list
```

Exemplo:

```text
NAME        SIZE
mistral     4.4 GB
qwen2.5     4.7 GB
```

---

## 3. Testar os modelos

```bash
ollama run mistral "Responda em português: 1+1 é igual a?"
```

```bash
ollama run qwen2.5 "Responda em português: 1+1 é igual a?"
```

Se ambos responderem "2", está funcionando.

---

## 4. Testar o Provider

```bash
python -c "from src.llm.provider import generate; print(generate('Olá'))"
```

---

# Configuração do RenderAgent

O RenderAgent converte BPMN XML em imagens PNG e SVG.

Tecnologias utilizadas:

* bpmn-js
* Puppeteer
* Node.js

---

## Instalar dependências do RenderAgent

Entre na pasta:

```bash
cd renderer
```

Instale:

```bash
npm install
```

Ou manualmente:

```bash
npm install bpmn-js puppeteer
```

Verifique:

```bash
npm list bpmn-js
npm list puppeteer
```

Estrutura esperada:

```text
renderer/
├── package.json
├── render_bpmn.js
└── node_modules/
```

---

# Execução

## Baseline monolítico

```bash
python experiments/run_baseline.py
```

---

## Pipeline Multiagente

```bash
python experiments/run_multiagent.py
```

---

## Testes

```bash
pytest tests/ -v
```

---

# Saídas Geradas

## XML BPMN

```text
data/outputs/multiagent/
```

---

## Imagens BPMN

```text
data/outputs/render/
```

Arquivos:

```text
processo.png
processo.svg
```

---

## Arquivos de Debug

```text
data/outputs/debug/
```

Exemplos:

```text
iteration_1.xml
iteration_2.xml
iteration_3.xml
```

---

# Modelos Utilizados

O projeto utiliza modelos locais executados via Ollama.

Modelos recomendados:

| Modelo   | Uso                    |
| -------- | ---------------------- |
| Mistral  | Compatibilidade geral  |
| Qwen 2.5 | Extração e refinamento |
| Llama 3  | Modelagem lógica       |
| Gemma 3  | Alternativa leve       |

Instalação:

```bash
ollama pull mistral
ollama pull qwen2.5
ollama pull llama3
ollama pull gemma3
```

---

# Requisitos de Hardware

## Mínimo

* 8 GB RAM
* CPU Quad-Core

## Recomendado

* 16 GB RAM
* SSD
* GPU opcional

Consumo típico:

| Componente       | RAM         |
| ---------------- | ----------- |
| Ollama + Mistral | ~4.5 GB     |
| Python Pipeline  | ~300 MB     |
| RenderAgent      | ~300-800 MB |
| Total            | ~5-6 GB     |

---

# Equipe

| Nome           | Papel                        |
| -------------- | ---------------------------- |
| Tiago Henrique | PO & Desenvolvedor          |
| João Victor    | Scrum Master & Desenvolvedor |
| João Pedro     | Desenvolvedor                |
| Isaac          | Desenvolvedor              |

---

# Sprints

| Sprint   | Período       | Foco                                         |
| -------- | ------------- | -------------------------------------------- |
| Sprint 0 | 05/05 → 08/05 | Setup, arquitetura, alinhamento              |
| Sprint 1 | 08/05 → 18/05 | MVP: baseline + pipeline multiagente inicial |
| Sprint 2 | 18/05 → 28/05 | Validação, refinamento iterativo, métricas   |
| Sprint 3 | 28/05 → 04/06 | Experimentos comparativos                    |
| Final    | 04/06 → 08/06 | Documentação e apresentação                  |

---

# Referências

* Artigo base: https://github.com/BPM-UOM/llm_based_tools_for_process_modeling
* Documentação de arquitetura: `docs/architecture.txt`
* Análise de gargalos: `docs/bottleneck-analysis.pdf`
* Planejamento ágil: `docs/planning.pdf`
