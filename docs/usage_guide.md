# Guia de Uso — bpmn-multiagent

Este guia explica como utilizar o pipeline multiagente para gerar modelos BPMN a partir de descrições textuais de processos e comparar os resultados com o baseline monolítico.

---

## Instalação

> Se já seguiu o guia de setup, pule para o [Passo 1](#passo-1-criar-os-textos-de-entrada).

1. Instale o Ollama: https://ollama.com/download
2. Baixe o modelo Mistral: `ollama pull mistral`
3. Clone o repositório e entre na pasta
4. Crie ambiente virtual: `python -m venv .venv`
5. Ative o ambiente:
   - Windows: `.venv\Scripts\Activate.ps1`
   - Linux/macOS: `source .venv/bin/activate`
6. Instale dependências: `pip install -e ".[dev]"`

> Para instruções detalhadas, consulte também [`docs/setup_ollama.md`](setup_ollama.md).

---

## Passo 1: Criar os textos de entrada

Crie arquivos `.txt` com a descrição textual de cada processo que deseja modelar. Coloque-os em:

```
data/inputs/freetext/
```

Exemplos de nomes de arquivo:

```
data/inputs/freetext/processo_compra.txt
data/inputs/freetext/processo_contratacao.txt
data/inputs/freetext/processo_reembolso_medico.txt
```

Cada arquivo deve conter a descrição completa do processo em português. Exemplo de conteúdo:

```
O cliente solicita a compra de um produto. O vendedor verifica a
disponibilidade no estoque. Se houver disponibilidade, o vendedor
emite a nota fiscal e encaminha para o financeiro. Se não houver,
o vendedor informa o prazo de reposição ao cliente. O financeiro
processa o pagamento e encerra o pedido.
```

---

## Executando os Pipelines

### Baseline Monolítico (one-shot)

```bash
python experiments/run_baseline.py
```

### Pipeline Multiagente

```bash
python experiments/run_multiagent.py
```

Ambos oferecem menu interativo para escolher o tipo de input:

- `[1]` freetext
- `[2]` structured
- `[3]` noisy
- `[4]` TODOS
- `[5]` Escolher arquivo específico

Os XMLs BPMN gerados são salvos em:

```
data/outputs/baseline/      # abordagem one-shot (artigo original)
data/outputs/multiagent/    # pipeline multiagente com validação
```

---

## Passo 2: Gerar os modelos BPMN

Execute os dois pipelines:

```bash
python experiments/run_baseline.py
python experiments/run_multiagent.py
```

Os arquivos gerados estarão em:

```
data/outputs/baseline/      # abordagem one-shot (artigo original)
data/outputs/multiagent/    # pipeline multiagente com validação
```

---

## Passo 3: Criar os ground truths (modelos de referência)

Para cada processo, crie um modelo BPMN de referência (o "gabarito") usando o Camunda Modeler ou qualquer editor BPMN. Salve os arquivos `.bpmn` em `data/ground_truth/` com o mesmo nome base dos arquivos de entrada:

```
data/ground_truth/processo_compra.bpmn
data/ground_truth/processo_contratacao.bpmn
data/ground_truth/processo_reembolso_medico.bpmn
```

> **Importante:** o ground truth deve incluir `<laneSet>` com `<lane>` e `<flowNodeRef>` para cada tarefa, seguindo o padrão dos arquivos existentes no diretório.

---

## Passo 4: Atualizar o script de comparação

Edite o arquivo `experiments/compare_results.py` e adicione os novos processos ao dicionário `PROCESS_GROUND_TRUTHS` (aproximadamente na linha 35):

```python
PROCESS_GROUND_TRUTHS = {
    "processo_compra": PROJECT_ROOT / "data" / "ground_truth" / "processo_compra.bpmn",
    "processo_contratacao": PROJECT_ROOT / "data" / "ground_truth" / "processo_contratacao.bpmn",
    "processo_reembolso_medico": PROJECT_ROOT / "data" / "ground_truth" / "processo_reembolso_medico.bpmn",
}
```

---

## Comparação de Métricas

```bash
python experiments/compare_results.py
```

Gera `docs/sprint3_comparison.md` com métricas de **Corretude**, **Completude** e **Clareza** para cada processo, comparando baseline vs multiagente.


O relatório será salvo em `docs/sprint3_comparison.md` com as métricas de **Corretude**, **Completude** e **Clareza** para cada processo, comparando baseline vs multiagente.

---

## Visualização BPMN Renderizada

Os BPMNs gerados podem ser visualizados interativamente via **bpmn-js**.

### Abrir um arquivo específico

Abra o arquivo `data/outputs/rendered/<process_id>.html` no seu navegador.

### Abrir todos de uma vez

**Windows (PowerShell):**

```powershell
Get-ChildItem "data\outputs\rendered\*.html" | ForEach-Object { Start-Process $_.FullName }
```

**Linux/macOS:**

```bash
for f in data/outputs/rendered/*.html; do xdg-open "$f"; done
```

### Como gerar os HTMLs renderizados

O agente `RenderAgent` (`src/agents/render_agent.py`) converte os XMLs BPMN em HTMLs interativos via bpmn-js. Execute o pipeline multiagente e os HTMLs serão gerados automaticamente em `data/outputs/rendered/`.

### Estrutura do RenderAgent

O `RenderAgent` é o sexto agente do pipeline. Ele:

- Lê `state.bpmn_xml`
- Gera um HTML completo com bpmn-js embutido (CDN)
- Salva em `data/outputs/rendered/<process_id>.html`
- **Não usa LLM** — é determinístico

### Abrir o gráfico comparativo final

O gráfico comparativo da Sprint 3 está disponível em `docs/chart/index.html`. Abra no navegador:

**Windows:**
```powershell
start docs/chart/index.html
```

**Linux/macOS:**
```bash
xdg-open docs/chart/index.html
```

---

## Observações

- Não é necessário editar código Python além do dicionário no Passo 4.
- Não é necessário mexer nos prompts: o sistema já está calibrado.
- O pipeline multiagente é mais lento que o baseline (3–5 chamadas ao LLM por processo), mas produz resultados estruturalmente corretos.
- Em caso de dúvidas, consulte a documentação em `docs/`.