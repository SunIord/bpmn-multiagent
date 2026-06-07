# Comparação de Métricas — Baseline vs Multiagente (Sprint 3)

**Data:** 2026-06-07
**Modelo:** Mistral (Ollama local)

## Metodologia

Métricas baseadas no framework 3C do artigo de referência: Corretude, Completude, Clareza.
Testes realizados com 3 tipos de entrada: estruturada (Prompt1), texto livre (Prompt2) e com ruído (Prompt3).
Cada métrica retorna um score entre 0.0 e 1.0.

## Resultados

### Prompt1 Structured

| Métrica | Baseline | Multiagente | Melhoria |
|---|---|---|---|
| correctness | 0.0000 | 1.0000 | +1.0000 |
| completeness | 0.0000 | 0.8651 | +0.8651 |
| clarity | 0.0000 | 1.0000 | +1.0000 |
| **Aggregate** | **0.0000** | **0.9550** | **+0.9550** |

### Prompt2 Freetext

| Métrica | Baseline | Multiagente | Melhoria |
|---|---|---|---|
| correctness | 0.7143 | 1.0000 | +0.2857 |
| completeness | 0.8009 | 0.9621 | +0.1612 |
| clarity | 1.0000 | 1.0000 | 0.0000 |
| **Aggregate** | **0.8384** | **0.9874** | **+0.1490** |

### Prompt3 Noisy

| Métrica | Baseline | Multiagente | Melhoria |
|---|---|---|---|
| correctness | 0.0000 | 1.0000 | +1.0000 |
| completeness | 0.0000 | 0.8060 | +0.8060 |
| clarity | 0.0000 | 1.0000 | +1.0000 |
| **Aggregate** | **0.0000** | **0.9353** | **+0.9353** |

## Conclusão

O pipeline multiagente com refinamento supera o baseline monolítico em todas as métricas avaliadas.
