# Especificação Funcional dos Agentes

> **Projeto:** bpmn-multiagent  
> **Documento:** Especificação funcional dos agentes do pipeline  
> **Status:** Vigente — Sprint 1  
> **Última atualização:** 08/05/2025  
> **Derivado de:** ADR-001, ADR-002, ADR-003, ADR-004

---

## 1. Visão Geral da Arquitetura

O sistema converte descrições textuais de processos de negócio em diagramas BPMN 2.0 válidos. A abordagem central é um **pipeline de 5 agentes especializados**, cada um responsável por uma etapa bem delimitada do raciocínio.

Essa decomposição é a principal diferença em relação ao artigo de referência, que usa um único LLM em modo *one-shot*. Conforme documentado no ADR-001, a abordagem monolítica sobrecarrega o modelo com múltiplas responsabilidades simultâneas — extração semântica, modelagem lógica e serialização XML —, resultando em alta taxa de erros e baixa consistência entre execuções.

O fluxo completo é:

```
Texto de entrada
      │
      ▼
[ExtractionAgent]   →  identifica elementos do processo
      │
      ▼
[ModelingAgent]     →  define o fluxo entre os elementos
      │
      ▼
[BPMNAgent]         →  serializa em XML BPMN 2.0 (via lxml)
      │
      ▼
[ValidationAgent]   →  verifica corretude estrutural
      │
   válido? ──não──► [RefinementAgent] ──► volta ao ModelingAgent ou BPMNAgent
      │
    sim
      │
      ▼
  BPMN final
```

O estado de todo o processo é mantido em um único objeto — o `ProcessModel` (ADR-004) — que flui entre os agentes e é atualizado incrementalmente a cada etapa.

---

## 2. Agentes

---

### 2.1 ExtractionAgent

**Arquivo:** `src/agents/extraction_agent.py`  
**Prompt:** `prompts/extraction.txt`

#### Papel no pipeline
Primeiro agente executado. Faz a ponte entre linguagem natural e estrutura de dados.

#### Responsabilidade principal
Receber o texto bruto do processo e identificar todos os seus elementos semânticos relevantes, produzindo um `ProcessModel` parcialmente preenchido.

#### Entrada esperada
| Campo | Tipo | Descrição |
|---|---|---|
| `ProcessModel.raw_input` | `str` | Texto do processo em linguagem natural |
| `ProcessModel.input_type` | `str` | `freetext`, `structured` ou `noisy` |

#### Saída produzida
Popula os seguintes campos do `ProcessModel`:

| Campo | Tipo | Exemplo |
|---|---|---|
| `activities` | `list[str]` | `["verificar estoque", "aprovar pedido"]` |
| `start_events` | `list[str]` | `["pedido recebido"]` |
| `end_events` | `list[str]` | `["pedido concluído"]` |
| `gateways` | `list[Gateway]` | `[{type: "exclusive", condition: "estoque disponível?"}]` |
| `actors` | `list[str]` | `["cliente", "gerente"]` |

O LLM é instruído via `prompts/extraction.txt` a retornar **apenas JSON válido** com exatamente esses campos. O agente faz parse da resposta e popula o `ProcessModel`.

#### Regras e restrições
- **Não define** a ordem ou o fluxo entre os elementos — isso é responsabilidade do `ModelingAgent`.
- **Não gera** XML ou qualquer representação BPMN.
- **Não inventa** elementos ausentes no texto. Se o texto não menciona um gateway, `gateways` fica vazio.
- Se o LLM retornar JSON malformado, o agente deve lançar `ValueError` com a resposta bruta para facilitar o debug.

#### Justificativa
O artigo de referência identificado na análise de gargalos (seção 2.3) demonstra que a qualidade varia drasticamente conforme o formato do input. Ao isolar a extração em um agente dedicado, é possível tratar cada tipo de entrada (`freetext`, `structured`, `noisy`) com prompts específicos sem afetar o restante do pipeline. Deriva diretamente do gargalo 2.1 (arquitetura monolítica) documentado na análise de gargalos.

---

### 2.2 ModelingAgent

**Arquivo:** `src/agents/modeling_agent.py`  
**Prompt:** `prompts/modeling.txt`

#### Papel no pipeline
Segundo agente. Transforma os elementos extraídos em um grafo de fluxo lógico.

#### Responsabilidade principal
Receber a lista de elementos do processo e definir as conexões entre eles — quais atividades se sucedem, como os gateways ramificam o fluxo e onde os caminhos se unem.

#### Entrada esperada
Os campos populados pelo `ExtractionAgent`:

| Campo | Tipo |
|---|---|
| `ProcessModel.activities` | `list[str]` |
| `ProcessModel.start_events` | `list[str]` |
| `ProcessModel.end_events` | `list[str]` |
| `ProcessModel.gateways` | `list[Gateway]` |
| `ProcessModel.raw_input` | `str` (texto original, para referência semântica) |

#### Saída produzida
| Campo | Tipo | Exemplo |
|---|---|---|
| `ProcessModel.sequences` | `list[SequenceFlow]` | `[{source: "pedido recebido", target: "verificar estoque"}]` |

Cada `SequenceFlow` contém `source`, `target` e opcionalmente `condition` (para arestas saindo de gateways).

#### Regras e restrições
- **Não extrai** novos elementos do texto — trabalha apenas com o que o `ExtractionAgent` já identificou.
- **Não gera** XML.
- Cada elemento de `start_events` deve aparecer como `source` em pelo menos um fluxo.
- Cada elemento de `end_events` deve aparecer como `target` em pelo menos um fluxo.
- Gateways exclusivos devem ter pelo menos 2 arestas de saída com `condition` definida.

#### Justificativa
A separação entre "o que existe no processo" (extração) e "como o processo flui" (modelagem) resolve o gargalo 2.4 (ausência de estado intermediário). Ao manter as sequências como estrutura explícita no `ProcessModel`, o pipeline pode reprocessar apenas o fluxo sem refazer a extração semântica, o que é essencial para o loop de refinamento da Sprint 2.

---

### 2.3 BPMNAgent

**Arquivo:** `src/agents/bpmn_agent.py`  
**Prompt:** nenhum — este agente **não usa LLM**

#### Papel no pipeline
Terceiro agente. Serializa a representação interna para o formato BPMN 2.0.

#### Responsabilidade principal
Converter deterministicamente o `ProcessModel` em XML BPMN 2.0 válido usando a biblioteca `lxml`.

#### Entrada esperada
O `ProcessModel` com todos os campos preenchidos pelos agentes anteriores:

| Campo | Condição |
|---|---|
| `activities` | não vazio |
| `start_events` | não vazio |
| `end_events` | não vazio |
| `sequences` | não vazio |

#### Saída produzida
| Campo | Tipo | Descrição |
|---|---|---|
| `ProcessModel.bpmn_xml` | `str` | XML BPMN 2.0 completo com declaração, namespaces e todos os elementos |

O XML inclui os namespaces obrigatórios (`bpmn`, `bpmndi`, `dc`, `di`) e os elementos correspondentes a cada campo do `ProcessModel`.

#### Regras e restrições
- **Não chama o LLM** em nenhuma circunstância — geração de XML é totalmente determinística.
- **Não toma decisões semânticas** — se `sequences` está incompleto, gera o XML com o que tem e deixa a validação apontar o problema.
- O XML gerado deve ser sempre bem-formado (garantido pelo `lxml`).
- IDs dos elementos BPMN são gerados automaticamente a partir dos nomes (`Task_1`, `StartEvent_1`, etc.).

#### Justificativa
Conforme ADR-003, pedir ao LLM que gere XML diretamente introduz erros de formatação, namespaces incorretos e inconsistências estruturais que são difíceis de detectar e corrigir. O `lxml` garante XML sempre bem-formado e com namespaces corretos, separando o raciocínio semântico (LLM) da serialização (código determinístico). Isso também facilita a validação posterior via Camunda.

---

### 2.4 ValidationAgent

**Arquivo:** `src/agents/validation_agent.py`  
**Módulo de regras:** `src/validation/rules.py`  
**Prompt:** nenhum — este agente **não usa LLM**

#### Papel no pipeline
Quarto agente. Verifica a corretude estrutural do BPMN gerado antes de entregar o resultado.

#### Responsabilidade principal
Aplicar regras de validação determinísticas sobre o `bpmn_xml` e registrar erros e avisos no `ProcessModel`.

#### Entrada esperada
| Campo | Tipo |
|---|---|
| `ProcessModel.bpmn_xml` | `str` — XML gerado pelo `BPMNAgent` |

#### Saída produzida
| Campo | Tipo | Descrição |
|---|---|---|
| `ProcessModel.validation.is_valid` | `bool` | `True` se nenhum erro crítico foi encontrado |
| `ProcessModel.validation.errors` | `list[str]` | Erros que impedem uso do BPMN |
| `ProcessModel.validation.warnings` | `list[str]` | Problemas não críticos |

#### Regras aplicadas (implementadas em `src/validation/rules.py`)

| Regra | Tipo | Descrição |
|---|---|---|
| XML bem-formado | Erro | O XML deve ser parseável pelo lxml |
| Presença de `startEvent` | Erro | Obrigatório em BPMN 2.0 |
| Presença de `endEvent` | Erro | Obrigatório em BPMN 2.0 |
| Presença de `sequenceFlow` | Erro | Sem fluxos, os elementos são ilhas |
| Conectividade básica | Warning | Todo nó deve ser referenciado em pelo menos um fluxo |
| Saídas de gateways | Warning | Gateways exclusivos devem ter ≥ 2 saídas |

#### Regras e restrições
- **Não modifica** o `bpmn_xml` — apenas lê e reporta.
- **Não chama o LLM**.
- Apenas erros em `validation.errors` tornam `is_valid = False` e disparam o loop de refinamento. Warnings são informativos.
- Novas regras devem ser adicionadas em `src/validation/rules.py`, não no agente.

#### Justificativa
O artigo de referência não possui validação formal (gargalo 2.2). Sem este agente, modelos com deadlocks, elementos desconectados ou ausência de eventos de início/fim seriam entregues silenciosamente. O `ValidationAgent` é o mecanismo que habilita o loop de refinamento — sem ele, o `RefinementAgent` não tem base para corrigir o que está errado.

---

### 2.5 RefinementAgent

**Arquivo:** `src/agents/refinement_agent.py`  
**Prompt:** `prompts/refinement.txt`

#### Papel no pipeline
Quinto agente. Atua apenas quando a validação falha, fechando o ciclo de autocorreção.

#### Responsabilidade principal
Receber o relatório de validação com erros e corrigir o `ProcessModel` para que uma nova passagem pelo `BPMNAgent` produza um BPMN válido.

#### Entrada esperada
| Campo | Tipo |
|---|---|
| `ProcessModel.bpmn_xml` | `str` — XML com problemas |
| `ProcessModel.validation.errors` | `list[str]` — erros identificados |
| `ProcessModel.validation.warnings` | `list[str]` — avisos |
| `ProcessModel.sequences` | `list[SequenceFlow]` — fluxo atual |
| `ProcessModel.iteration` | `int` — número da iteração atual |

#### Saída produzida
O agente pode modificar qualquer um dos campos estruturais do `ProcessModel` que sejam necessários para corrigir os erros:

| Campo modificável | Quando |
|---|---|
| `ProcessModel.sequences` | Para corrigir problemas de conectividade |
| `ProcessModel.activities` | Para adicionar elementos ausentes |
| `ProcessModel.start_events` / `end_events` | Se ausentes no BPMN gerado |

Após a modificação, o orquestrador redireciona o fluxo para o `BPMNAgent` (nova serialização) e depois para o `ValidationAgent` novamente.

#### Regras e restrições
- **Não é executado** se `validation.is_valid == True`.
- **Máximo de 3 iterações** (controlado pelo orquestrador via `ProcessModel.iteration`). Se após 3 tentativas o BPMN ainda for inválido, o pipeline retorna o melhor resultado obtido com o relatório de erros.
- Antes de modificar o estado, deve chamar `ProcessModel.snapshot()` para registrar o estado anterior no histórico.
- **Não reescreve o processo inteiro** — corrige apenas o que os erros de validação apontam.
- O prompt em `prompts/refinement.txt` deve incluir os erros e o estado atual para que o LLM saiba o que corrigir.

#### Justificativa
O artigo de referência usa geração *one-shot* sem possibilidade de correção (gargalo 2.5). O `RefinementAgent` implementa o ciclo **Gerar → Validar → Corrigir** proposto na análise de gargalos, seção 3.5. É o mecanismo central da Sprint 2 e, junto com o `ValidationAgent`, representa o principal diferencial técnico do projeto em relação ao baseline.

---

## 3. Justificativa da Abordagem Multiagente

A decisão de usar múltiplos agentes especializados em vez de um único LLM (ADR-001) parte de um diagnóstico claro: o modelo monolítico falha não por limitação de capacidade, mas por sobrecarga de responsabilidades simultâneas.

Quando um único LLM precisa ao mesmo tempo identificar atividades, determinar o fluxo entre elas, lidar com gateways condicionais e serializar tudo em XML BPMN válido, a taxa de erros cresce com a complexidade do processo. Qualquer erro em uma dessas etapas contamina o resultado final sem possibilidade de isolamento.

**Trade-offs da abordagem multiagente:**

| Aspecto | Ganho | Custo |
|---|---|---|
| Qualidade | Cada agente foca em uma tarefa bem definida | Mais chamadas ao LLM por execução |
| Rastreabilidade | Erros são isolados na etapa que os causou | Maior complexidade de implementação |
| Manutenção | Agentes podem ser melhorados ou trocados individualmente | Curva de aprendizado do LangGraph |
| Refinamento | Loop de correção é possível e controlável | Latência maior em casos com múltiplas iterações |
| Comparação | Baseline monolítico mantido para experimentos | Dois sistemas para manter em paralelo |

A decisão foi aceita com plena consciência dos custos, priorizando qualidade e a possibilidade de demonstrar ganho mensurável em relação ao artigo de referência.

---

## 4. Orquestração e Estado Compartilhado

### LangGraph (ADR-002)

O LangGraph gerencia o fluxo de execução entre os agentes como um **grafo de estados**. Cada agente é um nó; as transições entre nós são arestas condicionais.

O grafo completo do pipeline:

```
EXTRACT → MODEL → GENERATE → VALIDATE ─── válido ──► DONE
                                  │
                               inválido
                                  │
                               REFINE → GENERATE → VALIDATE
                                  │         (loop, máx. 3x)
                            iteração > 3
                                  │
                                DONE (com erros no relatório)
```

O LangGraph garante que:
- O fluxo é explícito e auditável — não há mágica implícita.
- Loops de correção têm critério de parada definido.
- Se um agente falha com exceção, o pipeline para e reporta em qual nó o erro ocorreu.

### ProcessModel (ADR-004)

O `ProcessModel` é o único objeto que transita entre os agentes. Ele funciona como um contrato: cada agente conhece quais campos vai ler e quais vai preencher.

**Crescimento do estado ao longo do pipeline:**

```
Início:     { raw_input: "..." }
Após Agente 1: + activities, start_events, end_events, gateways, actors
Após Agente 2: + sequences
Após Agente 3: + bpmn_xml
Após Agente 4: + validation { is_valid, errors, warnings }
Após Agente 5: sequences/activities atualizados → volta ao Agente 3
```

Os campos são aditivos — nenhum agente apaga o que o anterior escreveu, exceto o `RefinementAgent` que pode corrigir campos específicos após salvar o snapshot no histórico via `ProcessModel.snapshot()`.

---

## 5. Alinhamento com o Planejamento Ágil

### Sprint 1 (08/05 → 18/05) — MVP funcional

O objetivo da Sprint 1 é ter um pipeline ponta a ponta funcionando, mesmo que com qualidade básica. Os agentes prioritários são os três primeiros, que formam o caminho mínimo para gerar um BPMN:

| Agente | Status na Sprint 1 | Observação |
|---|---|---|
| `ExtractionAgent` | ✅ Implementar completo | Crítico — sem ele nada funciona |
| `ModelingAgent` | ✅ Implementar completo | Crítico — define o fluxo |
| `BPMNAgent` | ✅ Implementar completo | Crítico — produz o output |
| `ValidationAgent` | ⚠️ Implementar básico | Regras mínimas: start/end/flows |
| `RefinementAgent` | ❌ Adiar para Sprint 2 | Não bloqueia o MVP |

Ao final da Sprint 1, o sistema deve ser capaz de: receber texto → gerar BPMN → validar estruturalmente → retornar XML. O loop de refinamento ainda não precisa funcionar.

O baseline monolítico (`src/baseline/monolithic.py`) também é entregue na Sprint 1 para viabilizar a primeira comparação.

### Sprint 2 (18/05 → 28/05) — Qualidade e refinamento

O foco muda para corretude e autocorreção. Os agentes que ficaram incompletos na Sprint 1 são finalizados:

| Agente | Status na Sprint 2 | Observação |
|---|---|---|
| `ExtractionAgent` | 🔧 Melhorar prompts | Melhor identificação de decisões e condições |
| `ModelingAgent` | 🔧 Melhorar prompts | Tratamento de caminhos alternativos |
| `BPMNAgent` | 🔧 Suporte a lanes (opcional) | Depende de tempo disponível |
| `ValidationAgent` | ✅ Completar regras | Adicionar verificações de gateway, conectividade |
| `RefinementAgent` | ✅ Implementar completo | Principal entrega da Sprint 2 |

Ao final da Sprint 2, o loop **Gerar → Validar → Corrigir** deve estar funcionando e produzindo redução perceptível de erros em relação à Sprint 1.

### Por que essa ordem?

Os três primeiros agentes formam o caminho crítico: sem extração, modelagem e geração, não há nada para validar ou refinar. O `ValidationAgent` básico é incluído na Sprint 1 porque ele é a entrada do `RefinementAgent` — mas suas regras completas e o `RefinementAgent` em si são entregues na Sprint 2, quando já existe um pipeline estável para iterar sobre.

---

## 6. Referências

| Documento | Localização | Conteúdo |
|---|---|---|
| ADR-001 | `docs/decisions/ADR-001-multiagent.md` | Justificativa e trade-offs da arquitetura multiagente |
| ADR-002 | `docs/decisions/ADR-002-langgraph.md` | Escolha do LangGraph como orquestrador |
| ADR-003 | `docs/decisions/ADR-003-lxml.md` | Geração determinística de XML com lxml |
| ADR-004 | `docs/decisions/ADR-004-processmodel.md` | Estado intermediário compartilhado (ProcessModel) |
| Arquitetura | `docs/architecture.md` | Visão geral de componentes, API e persistência |
| Análise de gargalos | `docs/bottleneck-analysis.pdf` | Diagnóstico do artigo base e propostas de melhoria |
| Planejamento ágil | `docs/planning.pdf` | Sprints, datas e priorização |