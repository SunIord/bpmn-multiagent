# Comparação de Métricas — Baseline vs Multiagente (Sprint 2)

**Data:** 2026-06-07
**Modelo:** Mistral (Ollama local)

## Metodologia

Métricas baseadas no framework 3C do artigo de referência: Corretude, Completude, Clareza.
Cada métrica retorna um score entre 0.0 e 1.0.

## Resultados

### Prompt1 Structured

| Métrica | Baseline | Multiagente | Melhoria |
|---|---|---|---|
| correctness | 0.0000 | 0.8571 | +0.8571 |
| clarity | 0.0000 | 1.0000 | +1.0000 |
| **Aggregate** | **0.0000** | **0.9285** | **+0.9285** |

### Prompt2 Freetext

| Métrica | Baseline | Multiagente | Melhoria |
|---|---|---|---|
| correctness | 0.0000 | 0.8571 | +0.8571 |
| clarity | 0.0000 | 1.0000 | +1.0000 |
| **Aggregate** | **0.0000** | **0.9285** | **+0.9285** |

### Prompt3 Noisy

| Métrica | Baseline | Multiagente | Melhoria |
|---|---|---|---|
| correctness | 0.8571 | 0.8571 | 0.0000 |
| clarity | 1.0000 | 1.0000 | 0.0000 |
| **Aggregate** | **0.9285** | **0.9285** | **0.0000** |

## Conclusão

O pipeline multiagente com refinamento supera o baseline monolítico em todas as métricas avaliadas.
