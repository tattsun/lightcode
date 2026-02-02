# lightcode

Tool Calling対応のシンプルなCoding Agent

## セットアップ

```bash
rye sync
```

## 環境変数

```bash
export OPENAI_API_KEY=sk-xxxxx
export TAVILY_API_KEY=tvly-xxxxx  # Web検索を使う場合
```

## 使い方

```bash
# ローカル実行
make run

# Docker実行
make docker-build
make docker-run
```

## オプション

| オプション | 説明 |
|-----------|------|
| `--no-permissions` | ツール実行時の許可確認をスキップ |
| `--web-search` | Web検索ツールを有効化 |
| `--log-file <path>` | セッションログをJSONLファイルに保存 |
