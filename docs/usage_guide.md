# Guia de Uso — bpmn-multiagent

Este guia explica como utilizar o pipeline multiagente para gerar modelos BPMN a partir de descrições textuais de processos e comparar os resultados com o baseline monolítico.

---

## Pré-requisitos (instalação única)

Siga o guia completo em [`docs/setup_ollama.md`](setup_ollama.md) para:

1. Instalar o Ollama
2. Baixar o modelo Mistral (`ollama pull mistral`)
3. Criar ambiente virtual e instalar dependências (`pip install -e ".[dev]"`)

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

## Passo 5: Gerar o relatório de métricas

```bash
python experiments/compare_results.py
```

O relatório será salvo em `docs/sprint2_comparison.md` com as métricas de **Corretude**, **Completude** e **Clareza** para cada processo, comparando baseline vs multiagente.

---

## Observações

- Não é necessário editar código Python além do dicionário no Passo 4.
- Não é necessário mexer nos prompts: o sistema já está calibrado.
- O pipeline multiagente é mais lento que o baseline (3–5 chamadas ao LLM por processo), mas produz resultados estruturalmente corretos.
- Em caso de dúvidas, consulte a documentação em `docs/`.