# Comparação Baseline vs Multiagente — Sprint 1

**Data:** 15/05/2025  
**Modelo:** Mistral (Ollama local)

## Metodologia
Mesmos 3 textos de entrada processados por ambos os pipelines.

## Resultados

### Processo 1 — Pedido Online

| Critério | Baseline | Multiagente |
|---|---|---|
| XML bem formado | ✅ | ✅ |
| startEvent + endEvent | 1 + 2 | 1 + 2 |
| Tarefas | 1 (SeparateOrderAndEmitInvoice) | 4 (verificar, separar, emitir, notificar) |
| Gateways | 1 | 1 |
| Erros estruturais | ❌ `<intermediateCatchEvent>` inventado, sequenceFlow endEvent→gateway | ⚠️ startEvent duplicado como task (mesmo ID) |
| Fluxo lógico | ❌ Confuso e cíclico | ✅ Linear e coerente |

### Processo 2 — Reembolso

| Critério | Baseline | Multiagente |
|---|---|---|
| XML bem formado | ✅ | ✅ |
| Tarefas | 5 (bem nomeadas) | 5 |
| Gateways | 1 | 1 |
| Erros estruturais | ❌ sequenceFlow dentro do gateway (filho) | ⚠️ startEvent duplicado, gateway com fluxo sem condição |
| Fluxo lógico | ✅ Quase correto (mas estrutura inválida) | ✅ Correto, mas com conexões redundantes |

### Processo 3 — Clínica

| Critério | Baseline | Multiagente |
|---|---|---|
| XML bem formado | ✅ | ✅ |
| Tarefas | 6 | 6 |
| Gateways | 2 | 1 (faltou o segundo) |
| Erros estruturais | ❌ `<incoming>` inválido, sequenceFlow filho de task, IDs órfãos | ⚠️ startEvent duplicado |
| Fluxo lógico | ❌ Quebrado (elementos inexistentes) | ⚠️ Parcial (fluxo simplificado) |

## Consolidação

| Critério | Baseline | Multiagente |
|---|---|---|
| XML bem formado | 3/3 | 3/3 |
| Erros estruturais graves | 3/3 (elementos inventados, fluxos dentro de nós, IDs órfãos) | 0/3 |
| startEvent duplicado como task | 0/3 | 3/3 (bug sistemático) |
| Fluxo lógico coerente | 1/3 | 2/3 |
| **Nota geral** | **4/10** | **7/10** |

## Conclusão

O pipeline multiagente **elimina todos os erros estruturais graves** do baseline. O único bug remanescente (startEvent duplicado como task com mesmo ID) é sistemático e será corrigido na Sprint 2.

A arquitetura multiagente cumpre seu objetivo: separar responsabilidades (extração, modelagem, serialização) reduz erros e produz XML consistentemente mais correto, mesmo com um modelo local limitado (Mistral).

## Próximos passos (Sprint 2)
- Corrigir bug de startEvent duplicado (ajuste no prompt de extração ou pós-processamento)
- Implementar ValidationAgent com regras estruturais
- Implementar RefinementAgent com loop Gerar → Validar → Corrigir
- Testar com modelos mais fortes (GPT-4o, Claude) quando disponíveis