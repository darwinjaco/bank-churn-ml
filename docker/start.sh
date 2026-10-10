#!/usr/bin/env bash
# ROLE=api | dashboard | all (por defecto; Hugging Face Spaces expone solo el puerto 7860).
set -euo pipefail

ROLE="${ROLE:-all}"
PORT="${PORT:-7860}"

run_api() {
    exec uvicorn churn.api:app --host "${API_HOST:-0.0.0.0}" --port "${API_PORT:-8000}" --workers 1
}

run_dashboard() {
    exec streamlit run dashboard/app.py \
        --server.port "${PORT}" \
        --server.address 0.0.0.0 \
        --server.headless true \
        --server.enableXsrfProtection true \
        --server.enableCORS true \
        --server.maxUploadSize 1 \
        --client.showErrorDetails none \
        --browser.gatherUsageStats false \
        "$@"
}

wait_for_api() {
    for _ in $(seq 1 90); do
        if python -c "import urllib.request; urllib.request.urlopen('${API_URL}/health', timeout=2)" 2>/dev/null; then
            return 0
        fi
        sleep 1
    done
    echo "La API no respondió en ${API_URL}/health" >&2
    return 1
}

case "${ROLE}" in
    api) run_api ;;
    dashboard) run_dashboard ;;
    all)
        uvicorn churn.api:app --host 127.0.0.1 --port 8000 --workers 1 &
        wait_for_api
        # En iframe HTTPS, configurar xsrfCookieSameSite=none y los orígenes permitidos.
        run_dashboard
        ;;
    *)
        echo "ROLE desconocido: ${ROLE} (usar api, dashboard o all)" >&2
        exit 2
        ;;
esac
