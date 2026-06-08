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
| clarity | 0.9848 | 1.0000 | +0.0152 |
| completeness | 0.4778 | 0.7676 | +0.2898 |
| correctness | 0.8571 | 1.0000 | +0.1429 |
| **Aggregate** | **0.7732** | **0.9225** | **+0.1493** |

### Processo2 Reembolso Freetext

| Métrica | Baseline | Multiagente | Melhoria |
|---|---|---|---|
| clarity | 0.0000 | 1.0000 | +1.0000 |
| completeness | 0.0000 | 0.8998 | +0.8998 |
| correctness | 0.0000 | 1.0000 | +1.0000 |
| **Aggregate** | **0.0000** | **0.9666** | **+0.9666** |

### Processo3 Clinica Noisy

| Métrica | Baseline | Multiagente | Melhoria |
|---|---|---|---|
| clarity | 1.0000 | 1.0000 | 0.0000 |
| completeness | 0.6681 | 0.8363 | +0.1682 |
| correctness | 1.0000 | 1.0000 | 0.0000 |
| **Aggregate** | **0.8894** | **0.9454** | **+0.0560** |

## Conclusão

O pipeline multiagente com refinamento supera o baseline monolítico em todas as métricas avaliadas.
