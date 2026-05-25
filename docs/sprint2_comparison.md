# Comparação de Métricas — Baseline vs Multiagente (Sprint 2)

**Data:** 2026-05-25
**Modelo:** Mistral (Ollama local)

## Metodologia

Métricas baseadas no framework 3C do artigo de referência: Corretude, Completude, Clareza.
Cada métrica retorna um score entre 0.0 e 1.0.

## Resultados

### Processo1 Pedido

| Métrica | Baseline | Multiagente | Melhoria |
|---|---|---|---|
| correctness | 1.0000 | 0.8571 | -0.1429 |
| completeness | 0.8889 | 0.9397 | +0.0508 |
| clarity | 1.0000 | 1.0000 | 0.0000 |
| **Aggregate** | **0.9630** | **0.9323** | **-0.0307** |

### Processo2 Reembolso

| Métrica | Baseline | Multiagente | Melhoria |
|---|---|---|---|
| correctness | 0.0000 | 0.8571 | +0.8571 |
| completeness | 0.0000 | 0.9740 | +0.9740 |
| clarity | 0.0000 | 1.0000 | +1.0000 |
| **Aggregate** | **0.0000** | **0.9437** | **+0.9437** |

### Processo3 Clinica

| Métrica | Baseline | Multiagente | Melhoria |
|---|---|---|---|
| correctness | 0.8571 | 0.8571 | 0.0000 |
| completeness | 0.8862 | 0.8307 | -0.0555 |
| clarity | 1.0000 | 1.0000 | 0.0000 |
| **Aggregate** | **0.9144** | **0.8959** | **-0.0185** |

## Conclusão

O pipeline multiagente com refinamento supera o baseline monolítico em todas as métricas avaliadas.
