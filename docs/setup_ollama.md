# Guia de Setup — Ollama + Mistral (Local)

Este documento explica como instalar e configurar o Ollama com o modelo Mistral em qualquer máquina (Windows, Linux ou macOS) para executar o projeto `bpmn-multiagent` sem depender de APIs pagas.

---

## 1. Instalar o Ollama

### Windows

Baixe o instalador oficial e execute:
```
https://ollama.com/download/windows
```

Após instalar, o Ollama roda como serviço em segundo plano automaticamente.

Para verificar:
```powershell
ollama --version
```

### Linux / WSL2

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

Após instalar, o serviço não inicia automaticamente. Rode em um terminal separado:
```bash
ollama serve
```

### macOS

Baixe de:
```
https://ollama.com/download
```

Arraste para `/Applications` e abra o aplicativo.

---

## 2. Baixar o modelo Mistral

```bash
ollama pull mistral
```

Tamanho: ~4.4 GB. O download é feito uma única vez.

Verificar se o modelo está disponível:
```bash
ollama list
```

Saída esperada:
```
NAME      ID              SIZE      MODIFIED
mistral   f5074b1221da    4.4 GB    2 days ago
```

---

## 3. Testar o modelo

```bash
ollama run mistral "Responda em português: 1+1 é igual a?"
```

Se responder `2`, está funcionando.

---

## 4. Configurar o projeto

### 4.1 Criar ambiente virtual

**Windows (PowerShell):**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**Linux/macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 4.2 Instalar dependências

```bash
pip install -e ".[dev]"
```

### 4.3 Testar o provider

```bash
python -c "from src.llm.provider import generate; print(generate('Responda em português: 1+1 é igual a?'))"
```

Deve imprimir a resposta do Mistral.

---

## 5. Executar o projeto

### Baseline monolítico
```bash
python experiments/run_baseline.py
```

### Pipeline multiagente
```bash
python experiments/run_multiagent.py
```

### Testes automatizados
```bash
pytest tests/ -v
```

---

## 6. Solução de problemas

| Problema | Solução |
|---|---|
| `ollama: command not found` | Reinstale o Ollama ou adicione ao PATH |
| `connection refused` | Execute `ollama serve` em outro terminal (Linux/macOS). No Windows, o serviço inicia automaticamente. |
| `model not found` | Execute `ollama pull mistral` |
| `out of memory` | O Mistral precisa de ~8 GB de RAM livre. Feche outros aplicativos ou use um modelo menor: `ollama pull phi` |
| Respostas muito lentas | O Mistral roda em CPU. Em máquinas sem GPU, cada chamada pode levar 30-90 segundos. É normal. |

---

## 7. Trocar de modelo

Para usar outro modelo (ex.: Llama 3, Phi, Gemma), mude o parâmetro `model` no provider:

```bash
ollama pull llama3
```

Depois altere o default em `src/llm/provider.py`:
```python
def generate(prompt: str, model: str = "llama3", ...) -> str:
```