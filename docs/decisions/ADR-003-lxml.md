# ADR-003: lxml para Geração Determinística de XML BPMN

**Status:** Accepted  
**Data:** 06/05/2025

---

## Contexto

O BPMNAgent precisa gerar XML BPMN 2.0 válido. A opção mais simples seria pedir ao LLM que retorne o XML diretamente, mas isso introduz erros de formatação, namespaces incorretos e inconsistências estruturais.

## Decisão

O LLM gera uma **estrutura intermediária (FlowModel em JSON)** e a biblioteca `lxml` converte deterministicamente essa estrutura para XML BPMN 2.0.

## Consequências

- XML sempre bem-formado e com namespaces corretos
- Separação entre raciocínio (LLM) e serialização (lxml)
- Facilita validação via Camunda
- Requer mapeamento explícito FlowModel → XML (trabalho de implementação)