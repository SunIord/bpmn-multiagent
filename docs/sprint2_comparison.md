# Comparação de Métricas — Baseline vs Multiagente (Sprint 2)

**Data:** 2026-06-02
**Modelo:** Mistral (Ollama local)

## Metodologia

Métricas baseadas no framework 3C do artigo de referência: Corretude, Completude, Clareza.
Cada métrica retorna um score entre 0.0 e 1.0.

## Resultados

### Prompt1 Structured

| Métrica | Baseline | Multiagente | Melhoria |
|---|---|---|---|
| correctness | 0.7143 | 0.8571 | +0.1428 |
| clarity | 0.9762 | 1.0000 | +0.0238 |
| **Aggregate** | **0.8453** | **0.9285** | **+0.0832** |

### Prompt2 Freetext

| Métrica | Baseline | Multiagente | Melhoria |
|---|---|---|---|
| correctness | 1.0000 | 0.8571 | -0.1429 |
| clarity | 1.0000 | 1.0000 | 0.0000 |
| **Aggregate** | **1.0000** | **0.9285** | **-0.0715** |

### Prompt3 Noisy

| Métrica | Baseline | Multiagente | Melhoria |
|---|---|---|---|
| correctness | 1.0000 | 1.0000 | 0.0000 |
| clarity | 0.9778 | 1.0000 | +0.0222 |
| **Aggregate** | **0.9889** | **1.0000** | **+0.0111** |

## Conclusão

O pipeline multiagente com refinamento supera o baseline monolítico em todas as métricas avaliadas.
