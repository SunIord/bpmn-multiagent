# ADR-001: Arquitetura Multiagente

**Status:** Accepted  
**Data:** 2025-05-06

## Contexto
O artigo base usa abordagem monolítica (one-shot LLM). Identificamos gargalos de sobrecarga cognitiva, ausência de validação e baixa robustez.

## Decisão
Adotar pipeline com 5 agentes especializados: Extração, Modelagem, Geração BPMN, Validação e Refinamento.

## Consequências
- Maior controle e rastreabilidade do processo
- Facilita experimentos comparativos com o baseline
- Permite substituição individual de agentes sem impacto no pipeline