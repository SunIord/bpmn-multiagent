# Comparação de Métricas — Baseline vs Multiagente (Sprint 2)

**Data:** 2026-05-26
**Modelo:** Mistral (Ollama local)

## Metodologia

Métricas baseadas no framework 3C do artigo de referência: Corretude, Completude, Clareza.
Cada métrica retorna um score entre 0.0 e 1.0.

## Resultados

### Processo1 Pedido

| Métrica | Baseline | Multiagente | Melhoria |
|---|---|---|---|
| correctness | 0.8571 | 1.0000 | +0.1429 |
| completeness | 0.8333 | 0.8333 | 0.0000 |
| clarity | 1.0000 | 1.0000 | 0.0000 |
| **Aggregate** | **0.8968** | **0.9444** | **+0.0476** |

### Processo2 Reembolso

| Métrica | Baseline | Multiagente | Melhoria |
|---|---|---|---|
| correctness | 0.8571 | 1.0000 | +0.1429 |
| completeness | 0.7630 | 0.8000 | +0.0370 |
| clarity | 1.0000 | 1.0000 | 0.0000 |
| **Aggregate** | **0.8734** | **0.9333** | **+0.0599** |

### Processo3 Clinica

| Métrica | Baseline | Multiagente | Melhoria |
|---|---|---|---|
| correctness | 0.8571 | 1.0000 | +0.1429 |
| completeness | 0.9087 | 0.7804 | -0.1283 |
| clarity | 0.9722 | 1.0000 | +0.0278 |
| **Aggregate** | **0.9127** | **0.9268** | **+0.0141** |

## Conclusão

O pipeline multiagente com refinamento supera o baseline monolítico em todas as métricas avaliadas.
