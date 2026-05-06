bpmn-multiagent/
│
├── README.md
├── .gitignore
├── .env.example
├── pyproject.toml                  # (ou requirements.txt / package.json — a definir pela equipe de stack)
│
├── docs/
│   ├── architecture.md             # Documento de arquitetura (este sprint)
│   ├── bottleneck-analysis.md      # Análise de gargalos (já produzida)
│   ├── planning.md                 # Planejamento ágil (já produzido)
│   └── decisions/
│       └── ADR-001-multiagent.md   # Architecture Decision Record: escolha multiagente
│
├── data/
│   ├── inputs/
│   │   ├── structured/             # Entradas estruturadas (ex: JSON, tabelas)
│   │   ├── freetext/               # Entradas em texto livre
│   │   └── noisy/                  # Entradas com ruído (Sprint 3)
│   ├── outputs/
│   │   ├── baseline/               # Saídas do monolito
│   │   └── multiagent/             # Saídas do pipeline multiagente
│   └── ground_truth/               # Modelos BPMN de referência para avaliação
│
├── src/
│   ├── __init__.py
│   │
│   ├── agents/                     # Núcleo da arquitetura multiagente
│   │   ├── __init__.py
│   │   ├── base_agent.py           # Classe/interface abstrata de agente
│   │   ├── extraction_agent.py     # Agente 1: Extração semântica (texto → estrutura)
│   │   ├── modeling_agent.py       # Agente 2: Modelagem lógica (estrutura → fluxo)
│   │   ├── bpmn_agent.py           # Agente 3: Geração BPMN (fluxo → XML BPMN)
│   │   ├── validation_agent.py     # Agente 4: Validação estrutural
│   │   └── refinement_agent.py     # Agente 5: Refinamento iterativo
│   │
│   ├── pipeline/                   # Orquestração do fluxo entre agentes
│   │   ├── __init__.py
│   │   ├── orchestrator.py         # Controlador principal do pipeline
│   │   └── state.py                # Estado intermediário compartilhado (ex: ProcessModel)
│   │
│   ├── baseline/                   # Abordagem monolítica (reprodução do artigo)
│   │   ├── __init__.py
│   │   └── monolithic.py           # Um único LLM: texto → BPMN (one-shot)
│   │
│   ├── llm/                        # Camada de abstração para LLMs
│   │   ├── __init__.py
│   │   └── provider.py             # Interface agnóstica de LLM (OpenAI, Anthropic, etc.)
│   │
│   ├── validation/                 # Regras de validação do BPMN gerado
│   │   ├── __init__.py
│   │   └── rules.py                # Início/fim, conectividade, gateways, etc.
│   │
│   └── evaluation/                 # Métricas de avaliação
│       ├── __init__.py
│       └── metrics.py              # Corretude, completude, clareza, variância
│
├── prompts/                        # Prompts de cada agente (separados do código)
│   ├── extraction.txt
│   ├── modeling.txt
│   ├── bpmn_generation.txt
│   ├── validation.txt
│   └── refinement.txt
│
├── experiments/                    # Scripts de experimento e análise (Sprint 3)
│   ├── run_baseline.py
│   ├── run_multiagent.py
│   └── compare_results.py
│
├── notebooks/                      # Análise exploratória e visualizações
│   └── analysis.ipynb
│
└── tests/                          # Testes automatizados
    ├── __init__.py
    ├── test_agents.py
    ├── test_pipeline.py
    ├── test_validation.py
    └── fixtures/                   # Exemplos de entrada/saída para testes
        ├── sample_input.txt
        └── expected_output.bpmn