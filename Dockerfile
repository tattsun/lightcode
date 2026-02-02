FROM python:3.12-slim

WORKDIR /app

# ryeのインストール
RUN apt-get update && apt-get install -y curl && \
    curl -sSf https://rye.astral.sh/get | RYE_INSTALL_OPTION="--yes" bash && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

ENV PATH="/root/.rye/shims:/app/.venv/bin:${PATH}"
ENV VIRTUAL_ENV="/app/.venv"
ENV PYTHONPATH="/app/src"

# 依存関係のインストール
COPY pyproject.toml README.md requirements.lock requirements-dev.lock ./
RUN rye sync --no-dev

# ソースコードのコピー
COPY src/ src/
RUN rye sync --no-dev

ENTRYPOINT ["/app/.venv/bin/python", "-m", "lightcode.repl"]
