# Imagen única para la API, el dashboard o ambos (Hugging Face Spaces). Spec 005.
# MODEL_SOURCE=release (por defecto) descarga el modelo del GitHub Release;
# MODEL_SOURCE=local lo copia del contexto adicional "localmodel" (docker-compose.local.yml).
ARG MODEL_SOURCE=release

FROM python:3.11-slim@sha256:e88e9763f943ec1834f992a4b51e0f24500486803e8bc534e5767af9ea65f6ce AS base

COPY --from=ghcr.io/astral-sh/uv:0.12.13@sha256:b485bd65cc2cf1c9a93b3554012c9c3778cf7b1b5fd3d3096ce9e1226c97e1e6 /uv /uvx /bin/

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
COPY reports/model_metadata.json reports/final_test.json reports/monitoring.json ./reports/
RUN uv sync --locked --no-dev

# 3) Modelo. En ambas variantes el build falla si el SHA-256 no coincide.
FROM base AS model-release
ARG MODEL_URL=https://github.com/darwinjaco/bank-churn-ml/releases/download/model-v1.0/model.joblib
RUN MODEL_URL="${MODEL_URL}" python -m churn.artifact

FROM base AS model-local
COPY --from=localmodel model.joblib ./models/model.joblib
RUN python -m churn.artifact

FROM model-${MODEL_SOURCE} AS final
RUN install -d -o user -g user -m 700 /app/.runtime
USER user
ENV ROLE=all \
    API_URL=http://127.0.0.1:8000 \
    PORT=7860
EXPOSE 7860 8000
CMD ["bash", "docker/start.sh"]
