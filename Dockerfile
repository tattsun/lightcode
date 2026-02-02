FROM python:3.12-slim

WORKDIR /app

# ryeのインストール
RUN apt-get update && apt-get install -y curl && \
    curl -sSf https://rye.astral.sh/get | RYE_INSTALL_OPTION="--yes" bash && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

ENV PATH="/root/.rye/shims:${PATH}"

# 依存関係のインストール
COPY pyproject.toml README.md requirements.lock requirements-dev.lock ./
RUN rye sync --no-dev

# ソースコードのコピー
COPY src/ src/
RUN rye sync --no-dev

CMD ["rye", "run", "lightcode"]
