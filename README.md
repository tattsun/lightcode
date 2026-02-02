# lightcode

A simple coding agent with tool calling support.

## Setup

```bash
rye sync
```

## Environment Variables

```bash
export OPENAI_API_KEY=sk-xxxxx
export TAVILY_API_KEY=tvly-xxxxx  # Required for web search
```

## Usage

```bash
# Local
make run

# Docker
make docker-build
make docker-run
```

## Options

| Option | Description |
|--------|-------------|
| `--no-permissions` | Skip permission prompts for tool execution |
| `--web-search` | Enable web search tools |
| `--log-file <path>` | Save session log to JSONL file |
