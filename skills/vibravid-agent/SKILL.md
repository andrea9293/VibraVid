# VibraVid Agent Skill

Use this skill to interact with VibraVid media downloader via CLI for AI agents.

## Installation

```bash
curl -sL https://raw.githubusercontent.com/andrea9293/VibraVid/main/install.sh | bash
```

## Usage

All commands output JSON to stdout. Exit code 0 = success, 1 = error.

### List Providers

```bash
vibravid-agent providers
```

### Search Titles

```bash
vibravid-agent search --query "interstellar" --provider streamingcommunity
```

### Download Media

**Provider-based:**
```bash
vibravid-agent download --provider streamingcommunity --id "123" \
  --season 1 --episode "1-5" --video 1080 --audio "ita|eng"
```

**Direct URL:**
```bash
vibravid-agent download --url "https://example.com/video.m3u8" \
  --header "User-Agent:Mozilla" --key "KID:KEY"
```

**Background download:**
```bash
vibravid-agent download --provider streamingcommunity --id "123" --background
```

### Check Job Status

```bash
vibravid-agent status --job-id job_20260623_103000
vibravid-agent status --all
```

### Cancel Job

```bash
vibravid-agent cancel --job-id job_20260623_103000
```

### Configuration

```bash
vibravid-agent config --show
vibravid-agent config --get DOWNLOAD.thread_count
vibravid-agent config --set DOWNLOAD.thread_count=20
vibravid-agent config --dependencies
```

## Output Format

```json
{
  "success": true,
  "data": {...},
  "error": null,
  "metadata": {
    "version": "1.0.0",
    "timestamp": "2026-06-23T10:30:00Z"
  }
}
```

## Workflow Example

1. List providers: `vibravid-agent providers`
2. Search: `vibravid-agent search --query "title" --provider streamingcommunity`
3. Download: `vibravid-agent download --provider streamingcommunity --id "123" --background`
4. Monitor: `vibravid-agent status --job-id <job_id>`

## Notes for AI Agents

- All output is JSON format — pipe through `jq` for pretty formatting
- Use `--background` for long downloads to get a job_id immediately
- Poll status with `vibravid-agent status --job-id <id>` to check progress
- On error, check the `error` field for the error message
