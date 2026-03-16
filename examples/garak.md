# Garak quickstart (local Ollama: unsafe vs guarded)

This uses the same local Ollama model for both endpoints:

- `unsafe`: direct passthrough.
- `guarded`: same model call wrapped by `agentsafe` + Nemotron safety checks.

## 1) Install project deps

From `agentsafe/`:

```bash
uv sync --extra openai --extra ui
```

Set required env:

```bash
export NVIDIA_API_KEY="nvapi-..."
export MODEL_NAME="dolphin-mistral:7b"
export MODEL_BASE_URL="http://localhost:11434/v1"
```

## 2) Start local scan endpoints

```bash
uv run python examples/garak_servers.py
```

Default endpoints:

- Unsafe: `http://127.0.0.1:8011/v1`
- Guarded: `http://127.0.0.1:8012/v1`

Default backend model in `garak_servers.py` is `dolphin-mistral:7b` (override with `MODEL_NAME`).

## 3) Run garak manually (visible progress)

`garak` openai target expects `OPENAI_API_KEY` by env var name, so use dummy key for local endpoints:

```bash
export OPENAI_API_KEY=dummy
```

If you open a new terminal tab/session, export it again. To avoid that, each command below includes it inline.

### Quick scan (fast)

For local Ollama, keep scans serial (no `--parallel_attempts`) for stability.
Use `-v` for more visible CLI output while scanning.

Unsafe:

```bash
OPENAI_API_KEY=dummy OPENAI_BASE_URL=http://127.0.0.1:8011/v1 uvx --python 3.12 garak \
  -v \
  --target_type openai \
  --target_name dolphin-mistral:7b \
  --generations 1 \
  --probes dan.DanInTheWild
```

Guarded:

```bash
OPENAI_API_KEY=dummy OPENAI_BASE_URL=http://127.0.0.1:8012/v1 uvx --python 3.12 garak \
  -v \
  --target_type openai \
  --target_name dolphin-mistral:7b \
  --generations 1 \
  --probes dan.DanInTheWild
```

### Full scan (slower)

Unsafe:

```bash
OPENAI_API_KEY=dummy OPENAI_BASE_URL=http://127.0.0.1:8011/v1 uvx --python 3.12 garak \
  -v \
  --target_type openai \
  --target_name dolphin-mistral:7b \
  --generations 1 \
  --probes dan,malwaregen,promptinject
```

Guarded:

```bash
OPENAI_API_KEY=dummy OPENAI_BASE_URL=http://127.0.0.1:8012/v1 uvx --python 3.12 garak \
  -v \
  --target_type openai \
  --target_name dolphin-mistral:7b \
  --generations 1 \
  --probes dan,malwaregen,promptinject
```

## 4) Watch logs while running

```bash
tail -f ~/.local/share/garak/garak.log
```

Tip: use `-vv` instead of `-v` if you want even more CLI detail.

Reports are written under:

`~/.local/share/garak/garak_runs/`
