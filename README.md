# bpmn-multiagent

> **Multi-agent pipeline for BPMN generation from natural language using LLMs**  
> Tópicos Avançados em Engenharia de Software — CIn UFPE

---

## Sobre o Projeto

Este projeto propõe uma evolução sobre a abordagem do artigo *"Do they speak BPMN? Preliminary evaluation of LLMs modeling capabilities based on process model quality measures"*, substituindo a geração monolítica *one-shot* por uma **arquitetura multiagente** que decompõe o problema em etapas especializadas.

### O problema com a abordagem monolítica

Um único LLM executando extração semântica + modelagem lógica + geração BPMN ao mesmo tempo produz:
- Alta taxa de erros semânticos
- Inconsistência entre execuções
- Modelos sem validação formal

### Nossa solução

Um pipeline de 5 agentes especializados orquestrados pelo LangGraph:

```
Texto → [Extração] → [Modelagem] → [Geração BPMN] → [Validação] → [Refinamento] → XML BPMN
```

---

## Stack

| Camada | Tecnologia |
|---|---|
| Linguagem | Python |
| Agentes | LangChain |
| Orquestração | LangGraph |
| API | FastAPI |
| Geração XML | lxml |
| Visualização | bpmn-js |
| Validação BPMN | Camunda |
| Persistência | PostgreSQL |

---

## Estrutura do Projeto

```
bpmn-multiagent/
├── docs/               # Documentação e decisões arquiteturais
├── data/               # Dados de entrada, saída e ground truth
├── src/
│   ├── agents/         # Os 5 agentes especializados
│   ├── pipeline/       # Orquestrador LangGraph + estado intermediário
│   ├── baseline/       # Abordagem monolítica (reprodução do artigo)
│   ├── llm/            # Abstração do provedor LLM
│   ├── validation/     # Regras de validação BPMN
│   └── evaluation/     # Métricas de avaliação
├── prompts/            # Prompts de cada agente
├── experiments/        # Scripts de experimentos comparativos
├── notebooks/          # Análise exploratória
└── tests/              # Testes automatizados
```

---

## Equipe

| Nome | Papel |
|---|---|
| Tiago Henrique | PO & Desenvolvedor |
| João Victor | Scrum Master & Desenvolvedor |
| João Pedro | Desenvolvedor |
| Isaac | Desenvolvedor |

---

## Sprints

| Sprint | Período | Foco |
|---|---|---|
| Sprint 0 | 05/05 → 08/05 | Setup, arquitetura, alinhamento |
| Sprint 1 | 08/05 → 18/05 | MVP: baseline + pipeline multiagente inicial |
| Sprint 2 | 18/05 → 28/05 | Validação, refinamento iterativo, métricas |
| Sprint 3 | 28/05 → 04/06 | Experimentos comparativos |
| Final | 04/06 → 08/06 | Documentação e apresentação |

---

## Referências

- Artigo base: [Do they speak BPMN?](https://github.com/BPM-UOM/llm_based_tools_for_process_modeling)
- Documentação de arquitetura: [`docs/architecture.txt`](docs/architecture.txt)
- Análise de gargalos: [`docs/bottleneck-analysis.pdf`](docs/bottleneck-analysis.pdf)
- Planejamento ágil: [`docs/planning.pdf`](docs/planning.pdf)