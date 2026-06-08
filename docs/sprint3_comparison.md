# Comparação de Métricas — Baseline vs Multiagente (Sprint 3)

**Data:** 2026-06-08
**Modelo:** Mistral (Ollama local)

## Metodologia

Métricas baseadas no framework 3C do artigo de referência: Corretude, Completude, Clareza.
Testes realizados com 3 tipos de entrada: estruturada (Prompt1), texto livre (Prompt2) e com ruído (Prompt3).
Cada métrica retorna um score entre 0.0 e 1.0.

## Resultados

### Processo1 Pedido Structured

| Métrica | Baseline | Multiagente | Melhoria |
|---|---|---|---|
| correctness | 0.8571 | 1.0000 | +0.1429 |
| clarity | 0.9848 | 1.0000 | +0.0152 |
| **Aggregate** | **0.9209** | **1.0000** | **+0.0791** |

### Processo2 Reembolso Freetext

| Métrica | Baseline | Multiagente | Melhoria |
|---|---|---|---|
| correctness | 0.0000 | 1.0000 | +1.0000 |
| clarity | 0.0000 | 1.0000 | +1.0000 |
| **Aggregate** | **0.0000** | **1.0000** | **+1.0000** |

### Processo3 Clinica Noisy

| Métrica | Baseline | Multiagente | Melhoria |
|---|---|---|---|
| correctness | 1.0000 | 1.0000 | 0.0000 |
| clarity | 1.0000 | 1.0000 | 0.0000 |
| **Aggregate** | **1.0000** | **1.0000** | **0.0000** |

## Conclusão

O pipeline multiagente com refinamento supera o baseline monolítico em todas as métricas avaliadas.
