# lightcode

Tool Calling対応のシンプルなCoding Agent

## セットアップ

```bash
# 依存関係のインストール
rye sync
```

## 環境変数

```bash
export OPENAI_API_KEY=sk-xxxxx
```

## 使い方

### ローカル実行

```bash
make run
```

### Docker実行

```bash
make docker-build
make docker-run
```

### オプション

- `--no-permissions`: ツール実行時の許可確認をスキップ
