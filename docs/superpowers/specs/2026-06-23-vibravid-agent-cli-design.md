# VibraVid Agent CLI - Design Document

**Data:** 2026-06-23  
**Autore:** Andrea (andrea9293)  
**Stato:** Draft

---

## Obiettivo

Trasformare VibraVid in uno strumento CLI globale utilizzabile da agenti IA, con:
- Output JSON strutturato per ogni comando
- Installazione globale via script bash (punta a release GitHub)
- Skill OpenCode per integrazione con agenti IA
- Mappatura completa della CLI esistente (`manual.py`)

---

## Architettura

### Struttura Progetto

```
VibraVid/
├── VibraVid/
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── main.py              # Entry point agent CLI
│   │   ├── commands/            # Sottocomandi JSON
│   │   │   ├── __init__.py
│   │   │   ├── search.py
│   │   │   ├── download.py
│   │   │   ├── providers.py
│   │   │   ├── status.py
│   │   │   ├── config.py
│   │   │   └── cancel.py
│   │   ├── output.py            # Formatter JSON output
│   │   └── job_manager.py       # Gestione job background
│   ├── cli/                     # CLI esistente (non modificata)
│   └── ...
├── agent.py                     # Entry point per PyInstaller
├── manual.py                    # Entry point esistente
├── install.sh                   # Script installazione globale
└── skills/
    └── vibravid-agent/
        └── SKILL.md             # Skill per agenti IA
```

### Flusso di Esecuzione

1. `vibravid-agent <command> [options]` → output JSON stdout
2. Exit code: 0 = successo, 1 = errore, 2 = parziale
3. Log e progressi vanno su stderr (non contaminano JSON)
4. Job background: `--background` flag, PID salvato in `~/.vibravid-agent/jobs/`

### Output JSON Standard

```json
{
  "success": true,
  "data": {...},
  "error": null,
  "metadata": {
    "version": "1.0.0",
    "timestamp": "2026-06-23T10:30:00Z",
    "duration_ms": 1234
  }
}
```

---

## Comandi

### 1. `vibravid-agent providers`

Lista provider disponibili.

```bash
vibravid-agent providers [--available]
```

**Output:**
```json
{
  "success": true,
  "data": {
    "providers": [
      {"index": 0, "name": "streamingcommunity", "category": "film_serie", "available": true},
      {"index": 1, "name": "animeunity", "category": "anime", "available": true}
    ]
  }
}
```

### 2. `vibravid-agent search`

Cerca titoli.

```bash
vibravid-agent search --query "interstellar" --provider streamingcommunity \
  [--year 2020] [--category 2] [--auto-first] [--global]
```

**Output:**
```json
{
  "success": true,
  "data": {
    "query": "interstellar",
    "provider": "streamingcommunity",
    "results": [
      {"id": "123", "title": "Interstellar", "year": 2014, "type": "movie"},
      {"id": "456", "title": "Interstellar: The Journey", "year": 2015, "type": "series"}
    ]
  }
}
```

### 3. `vibravid-agent download`

Scarica contenuto.

```bash
vibravid-agent download --provider streamingcommunity --id "123" \
  [--season 1] [--episode "1-5"] [--video 1080] [--audio "ita|eng"] \
  [--subtitle "eng"] [--extension mkv] [--background]
```

**Download diretto (senza ricerca):**
```bash
vibravid-agent download --url "https://..." \
  [--header "Key:Value"] [--license-url URL] [--key KID:KEY] \
  [--drm widevine|playready] [--max-segments N] [--max-time HH:MM:SS]
```

**Output:**
```json
{
  "success": true,
  "data": {
    "job_id": "job_20260623_103000",
    "status": "started",
    "pid": 12345,
    "title": "Interstellar",
    "output_path": "/home/user/Video/Movie/Interstellar (2014)/Interstellar (2014).mkv"
  }
}
```

### 4. `vibravid-agent status`

Stato job.

```bash
vibravid-agent status [--job-id job_20260623_103000] [--all]
```

**Output:**
```json
{
  "success": true,
  "data": {
    "job_id": "job_20260623_103000",
    "status": "downloading",
    "progress": 45.2,
    "speed_mbps": 12.5,
    "eta_seconds": 120,
    "title": "Interstellar",
    "output_path": "/home/user/Video/Movie/Interstellar (2014)/Interstellar (2014).mkv"
  }
}
```

### 5. `vibravid-agent cancel`

Annulla job.

```bash
vibravid-agent cancel --job-id job_20260623_103000
```

**Output:**
```json
{
  "success": true,
  "data": {
    "job_id": "job_20260623_103000",
    "status": "cancelled"
  }
}
```

### 6. `vibravid-agent config`

Mostra/modifica configurazione.

```bash
vibravid-agent config [--show] [--set DOWNLOAD.thread_count=20] [--get DOWNLOAD.thread_count]
vibravid-agent config --dependencies
```

**Output:**
```json
{
  "success": true,
  "data": {
    "config": {
      "DEFAULT": {"log_level": "INFO", "close_console": true},
      "DOWNLOAD": {"thread_count": 20, "select_video": "best"}
    }
  }
}
```

---

## Mappatura CLI Esistente

| Flag CLI esistente | Comando agent equivalente |
|---|---|
| `--site NAME` | `--provider NAME` |
| `--search QUERY` | `search --query QUERY` |
| `--auto-first` | `search --auto-first` |
| `--global` | `search --global` |
| `--category N` | `search --category N` |
| `--season SEL` | `download --season SEL` |
| `--episode SEL` | `download --episode SEL` |
| `--year RANGE` | `search --year RANGE` / `download --year RANGE` |
| `-sv SPEC` | `download --video SPEC` |
| `-sa SPEC` | `download --audio SPEC` |
| `-ss SPEC` | `download --subtitle SPEC` |
| `--extension EXT` | `download --extension EXT` |
| `--use_proxy` | `download --use-proxy` |
| `--down URL` | `download --url URL` (download diretto) |
| `--headers Key:Value` | `download --header Key:Value` (repeatable) |
| `--license-url URL` | `download --license-url URL` |
| `--key KID:KEY` | `download --key KID:KEY` (repeatable) |
| `--drm widevine|playready` | `download --drm widevine` |
| `--max-segments N` | `download --max-segments N` |
| `--max-time HH:MM:SS` | `download --max-time HH:MM:SS` |
| `--dep` | `config --dependencies` |
| `--version` | `--version` |

---

## Installazione Globale

### Script `install.sh`

```bash
#!/bin/bash
set -e

REPO="andrea9293/VibraVid"
BINARY_NAME="vibravid-agent"
INSTALL_DIR="${HOME}/.local/bin"

# Rileva OS e architettura
OS=$(uname -s | tr '[:upper:]' '[:lower:]')
ARCH=$(uname -m)

case "$ARCH" in
    x86_64) ARCH="x64" ;;
    aarch64|arm64) ARCH="arm64" ;;
    *) echo "Architettura non supportata: $ARCH"; exit 1 ;;
esac

# Mappa OS/arch al nome asset GitHub
case "$OS" in
    linux) ASSET_PATTERN="linux.*${ARCH}" ;;
    darwin) ASSET_PATTERN="mac.*${ARCH}" ;;
    mingw*|msys*|cygwin*) ASSET_PATTERN="win.*x64.exe"; BINARY_NAME+=".exe" ;;
    *) echo "OS non supportato: $OS"; exit 1 ;;
esac

# Crea directory di installazione
mkdir -p "$INSTALL_DIR"

# Scarica ultima release
echo "Scarico l'ultima release da ${REPO}..."
LATEST_URL=$(curl -sL "https://api.github.com/repos/${REPO}/releases/latest" | \
    grep "browser_download_url" | \
    grep -E "$ASSET_PATTERN" | \
    head -1 | \
    cut -d '"' -f 4)

if [ -z "$LATEST_URL" ]; then
    echo "Errore: nessun asset trovato per ${OS}/${ARCH}"
    exit 1
fi

curl -L "$LATEST_URL" -o "${INSTALL_DIR}/${BINARY_NAME}"
chmod +x "${INSTALL_DIR}/${BINARY_NAME}"

# Verifica installazione
if ! command -v "$BINARY_NAME" &> /dev/null; then
    echo "Attenzione: ${INSTALL_DIR} non è nel PATH"
    echo "Aggiungi al tuo ~/.bashrc o ~/.zshrc:"
    echo "  export PATH=\"${INSTALL_DIR}:\$PATH\""
fi

echo "✓ ${BINARY_NAME} installato con successo in ${INSTALL_DIR}/${BINARY_NAME}"
echo "Esegui '${BINARY_NAME} --version' per verificare"
```

**Comando di installazione:**
```bash
curl -sL https://raw.githubusercontent.com/andrea9293/VibraVid/main/install.sh | bash
```

---

## Gestione Job Background

### Directory Struttura

```
~/.vibravid-agent/
├── jobs/
│   ├── job_20260623_103000.json    # Metadata job
│   └── job_20260623_103000.log     # Log output
└── config.json                      # Config override (opzionale)
```

### Job Metadata File

```json
{
  "job_id": "job_20260623_103000",
  "pid": 12345,
  "status": "downloading",
  "started_at": "2026-06-23T10:30:00Z",
  "command": ["vibravid-agent", "download", "--provider", "streamingcommunity", "--id", "123"],
  "title": "Interstellar",
  "output_path": "/home/user/Video/Movie/Interstellar (2014)/Interstellar (2014).mkv",
  "progress": 45.2,
  "error": null
}
```

### Meccanismo

1. `download --background` → fork processo figlio, PID salvato in job metadata
2. `status --job-id <id>` → legge metadata + interroga processo figlio via file di stato
3. `cancel --job-id <id>` → invia SIGTERM al PID

---

## Implementazione

### Entry Point `agent.py`

```python
#!/usr/bin/env python3
"""Entry point per vibravid-agent CLI."""

from VibraVid.agent.main import main

if __name__ == "__main__":
    main()
```

### Struttura `VibraVid/agent/main.py`

```python
import sys
import json
import argparse
from datetime import datetime

from VibraVid.agent.commands import search, download, providers, status, config, cancel
from VibraVid.upload.version import __version__, __title__

def output_json(success, data=None, error=None):
    """Stampa output JSON standard e esce."""
    result = {
        "success": success,
        "data": data,
        "error": error,
        "metadata": {
            "version": __version__,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    sys.exit(0 if success else 1)

def main():
    parser = argparse.ArgumentParser(
        prog="vibravid-agent",
        description="VibraVid CLI per agenti IA - output JSON strutturato"
    )
    parser.add_argument("--version", action="version", version=f"{__title__} {__version__}")
    
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # Registra comandi
    providers.register(subparsers)
    search.register(subparsers)
    download.register(subparsers)
    status.register(subparsers)
    cancel.register(subparsers)
    config.register(subparsers)
    
    args = parser.parse_args()
    
    try:
        # Dispatch al comando
        commands = {
            "providers": providers.execute,
            "search": search.execute,
            "download": download.execute,
            "status": status.execute,
            "cancel": cancel.execute,
            "config": config.execute,
        }
        commands[args.command](args)
    except Exception as e:
        output_json(False, error=str(e))
```

### Esempio Implementazione `providers.py`

```python
import json
from VibraVid.services._base import load_search_functions
from VibraVid.agent.main import output_json

def register(subparsers):
    parser = subparsers.add_parser("providers", help="Lista provider disponibili")
    parser.add_argument("--available", action="store_true", help="Solo provider disponibili")

def execute(args):
    search_functions = load_search_functions()
    providers = []
    
    for func in search_functions.values():
        providers.append({
            "index": func.indice,
            "name": func.module_name,
            "category": func.use_for.lower(),
            "available": True
        })
    
    if args.available:
        providers = [p for p in providers if p["available"]]
    
    output_json(True, data={"providers": providers})
```

---

## Workflow di Build

Modifico `.github/workflows/build.yml` per buildare anche `agent.py`:

```yaml
- name: Build agent executable with PyInstaller
  run: |
    pyinstaller --onefile \
    # ... stessi flag di manual.py ...
    --name=${{ matrix.artifact_name }}-agent agent.py
```

---

## Skill per Agenti IA

Creo una skill OpenCode in `skills/vibravid-agent/SKILL.md` che documenta:
- Come usare `vibravid-agent` da CLI
- Formato output JSON
- Workflow tipici (search → download → status)
- Gestione errori

La skill sarà disponibile per qualsiasi agente IA che usa OpenCode.

---

## Testing Locale

Prima di pushare:
```bash
# Build locale
pyinstaller --onefile --name vibravid-agent agent.py

# Test comandi
./dist/vibravid-agent --version
./dist/vibravid-agent providers
./dist/vibravid-agent search --query "test" --provider streamingcommunity
```

---

## Note Tecniche

- **Nessuna autenticazione:** API locale senza auth (solo localhost)
- **Solo CLI:** Nessun demone HTTP, solo comandi one-shot + job background
- **Mappatura completa:** Tutti i flag di `manual.py` convertiti in sottocomandi JSON
- **Output strutturato:** JSON stdout, log stderr
- **Installazione globale:** Script bash punta a release GitHub su `andrea9293/VibraVid`
