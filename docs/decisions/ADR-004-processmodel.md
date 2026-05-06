# ADR-004: Estado Intermediário em JSON (ProcessModel)

**Status:** Accepted  
**Data:** 06/05/2025

---

## Contexto

Os agentes precisam compartilhar informações entre si de forma estruturada e consistente. Sem um contrato de dados explícito, cada agente dependeria do formato de saída do anterior, tornando o sistema frágil.

## Decisão

Definir um **ProcessModel** como contrato de dados central, representado em JSON e persistido no PostgreSQL a cada iteração. Todos os agentes leem e escrevem nessa estrutura.

## Consequências

- Rastreabilidade completa de cada iteração
- Facilita debugging e análise de experimentos
- Permite reprocessar a partir de qualquer etapa
- O estado cresce conforme o pipeline avança (mais campos preenchidos)