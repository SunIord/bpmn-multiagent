# ADR-001: Arquitetura Multiagente

**Status:** Accepted  
**Data:** 06/05/2025  
**Autores:** Equipe bpmn-multiagent

---

## Contexto

O artigo de referência utiliza uma abordagem monolítica (*one-shot*): um único LLM recebe a descrição textual e gera o BPMN diretamente. A análise de gargalos identificou que isso impõe sobrecarga cognitiva excessiva ao modelo, resultando em alta taxa de erros semânticos, baixa consistência e ausência de validação formal.

## Decisão

Adotar uma **arquitetura multiagente** com 5 agentes especializados, orquestrados pelo LangGraph:

1. **ExtractionAgent** — extração semântica (texto → estrutura JSON)
2. **ModelingAgent** — modelagem lógica (estrutura → fluxo)
3. **BPMNAgent** — geração BPMN (fluxo → XML via lxml)
4. **ValidationAgent** — validação estrutural e lógica
5. **RefinementAgent** — refinamento de clareza e nomenclatura

## Consequências

**Positivas:**
- Separação clara de responsabilidades
- Loop de refinamento iterativo possível
- Facilita experimentos comparativos com o baseline
- Cada agente pode ser melhorado ou substituído de forma isolada

**Negativas:**
- Maior latência por execução (múltiplas chamadas ao LLM)
- Maior complexidade de implementação inicial
- Custo de tokens maior por geração

## Alternativas consideradas

- **One-shot (baseline):** mantido apenas como comparação — é a abordagem do artigo
- **Two-agent (extração + geração):** descartado por não incluir validação formal