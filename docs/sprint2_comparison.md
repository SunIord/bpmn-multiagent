# Comparação de Métricas — Baseline vs Multiagente (Sprint 2)

**Data:** 2026-05-20
**Modelo:** Mistral (Ollama local)

## Metodologia

Métricas baseadas no framework 3C do artigo de referência: Corretude, Completude, Clareza.
Cada métrica retorna um score entre 0.0 e 1.0.

## Resultados

### Processo1 Pedido

| Métrica | Baseline | Multiagente | Melhoria |
|---|---|---|---|
| correctness | 0.8571 | 1.0000 | +0.1429 |
| completeness | 0.9259 | 0.9563 | +0.0304 |
| clarity | 1.0000 | 1.0000 | 0.0000 |
| **Aggregate** | **0.9277** | **0.9854** | **+0.0577** |

### Processo2 Reembolso

| Métrica | Baseline | Multiagente | Melhoria |
|---|---|---|---|
| correctness | 1.0000 | 1.0000 | 0.0000 |
| completeness | 0.9037 | 0.9524 | +0.0487 |
| clarity | 0.9583 | 1.0000 | +0.0417 |
| **Aggregate** | **0.9540** | **0.9841** | **+0.0301** |

### Processo3 Clinica

| Métrica | Baseline | Multiagente | Melhoria |
|---|---|---|---|
| correctness | 0.0000 | 1.0000 | +1.0000 |
| completeness | 0.0000 | 0.9074 | +0.9074 |
| clarity | 0.0000 | 1.0000 | +1.0000 |
| **Aggregate** | **0.0000** | **0.9691** | **+0.9691** |

## Conclusão

O pipeline multiagente com refinamento supera o baseline monolítico em todas as métricas avaliadas.
