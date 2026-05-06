# ADR-002: LangGraph como Orquestrador

**Status:** Accepted  
**Data:** 06/05/2025

---

## Contexto

O pipeline multiagente requer controle de fluxo com estados, transições condicionais e ciclos de correção (loops). É necessário um mecanismo que gerencie isso de forma explícita.

## Decisão

Usar **LangGraph** como orquestrador do pipeline, definindo os agentes como nós de um grafo de estados e as transições como arestas condicionais.

## Consequências

- Fluxo de execução explícito e auditável
- Suporte nativo a loops (ciclo Gerar → Validar → Corrigir)
- Integração direta com LangChain (mesma stack)
- Curva de aprendizado inicial para a equipe