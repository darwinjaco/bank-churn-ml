# Imagen única para la API, el dashboard o ambos (Hugging Face Spaces). Spec 005.
FROM python:3.11-slim

COPY --from=ghcr.io/astral-sh/uv:0.12.13 /uv /uvx /bin/

ENV PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH" \
    NUMBA_CACHE_DIR=/tmp/numba \
    MPLCONFIGDIR=/tmp/matplotlib

# Hugging Face Spaces ejecuta con el usuario 1000.
RUN useradd --create-home --uid 1000 user
WORKDIR /app

# 1) Dependencias bloqueadas (capa reutilizable), sin grupos de desarrollo.
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --locked --no-dev --no-install-project

# 2) Código y metadatos que sirve la API. El CSV nunca entra en la imagen.
COPY src ./src
COPY dashboard ./dashboard
COPY docker/start.sh ./docker/start.sh
COPY reports/model_metadata.json reports/final_test.json ./reports/
RUN uv sync --locked --no-dev

# 3) Modelo desde el GitHub Release; el build falla si el SHA-256 no coincide.
ARG MODEL_URL=https://github.com/darwinjaco/bank-churn-ml/releases/download/model-v1.0/model.joblib
RUN MODEL_URL="${MODEL_URL}" python -m churn.artifact && chown -R user:user /app

USER user
ENV ROLE=all \
    API_URL=http://127.0.0.1:8000 \
    PORT=7860
EXPOSE 7860 8000
CMD ["bash", "docker/start.sh"]
