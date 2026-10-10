"""Dashboard de decisiones de retención (spec 005 §7, spec 006 §4.9). Solo consume la API."""

from __future__ import annotations

import httpx
import pandas as pd
import streamlit as st

from churn.ui import (
    ApiClient,
    ApiError,
    eur,
    expectation_rows,
    monitoring_metrics,
    prepare_batch,
    psi_table,
    read_batch_csv,
    reason_rows,
    results_csv,
    results_table,
)

API_ERRORS = (ApiError, httpx.HTTPError)

st.set_page_config(page_title="Retención bancaria", page_icon="🏦", layout="wide")


@st.cache_resource
def get_client() -> ApiClient:
    """Un solo cliente HTTP por proceso (Streamlit re-ejecuta el script en cada interacción)."""
    return ApiClient()


api = get_client()

st.title("Abandono bancario → decisiones de retención")
st.caption(
    "Demo de portafolio con datos públicos y supuestos económicos ilustrativos. "
    "Las razones son factores del modelo, no causas. No es asesoría financiera."
)

try:
    model = api.model()
except API_ERRORS as error:  # La API puede no estar lista todavía.
    st.error(f"No se pudo contactar la API ({type(error).__name__}). Revisa que esté levantada.")
    st.stop()

single, batch_tab, about, drift = st.tabs(["Cliente", "Lote (CSV)", "Modelo", "Monitoreo"])

with single:
    with st.form("cliente"):
        c1, c2, c3 = st.columns(3)
        customer = {
            "CreditScore": c1.number_input("CreditScore", 300, 900, 650),
            "Age": c1.number_input("Edad", 18, 100, 45),
            "Tenure": c1.number_input("Antigüedad (años)", 0, 10, 4),
            "Balance": c2.number_input("Saldo (€)", 0.0, 300_000.0, 90_000.0, step=1_000.0),
            "NumOfProducts": c2.selectbox("Productos", [1, 2, 3, 4]),
            "Geography": c2.selectbox("País", ["France", "Germany", "Spain"]),
            "HasCrCard": int(c3.checkbox("Tiene tarjeta de crédito", True)),
            "IsActiveMember": int(c3.checkbox("Miembro activo", False)),
        }
        submitted = st.form_submit_button("Evaluar")
    if submitted:
        try:
            result = api.explain(customer)
        except API_ERRORS as error:
            st.error(str(error) or type(error).__name__)
        else:
            prediction = result["prediction"]
            m1, m2, m3 = st.columns(3)
            m1.metric("Probabilidad de abandono", f"{prediction['churn_probability']:.1%}")
            m2.metric("Decisión", "Contactar" if prediction["contact"] else "No contactar")
            m3.metric("Beneficio esperado", f"{prediction['expected_benefit_eur']:.0f} €")
            st.dataframe(pd.DataFrame(reason_rows(prediction)), hide_index=True)
            origin = "LLM" if result["source"] == "llm" else "plantilla"
            st.text(result["text"])
            st.caption(f"Texto generado por: {origin}.")

with batch_tab:
    st.write(
        "CSV con las columnas del contrato (otras columnas se ignoran; máximo 1.000 filas). "
        "Ejemplo sintético en el repositorio: `examples/clientes_ejemplo.csv`."
    )
    upload = st.file_uploader("Archivo CSV", type="csv", max_upload_size=1)
    if upload is not None:
        try:
            frame = read_batch_csv(upload)
            response = api.batch(prepare_batch(frame))
        except (ValueError, pd.errors.ParserError, *API_ERRORS) as error:
            st.error(str(error) or type(error).__name__)
        else:
            summary = response["summary"]
            b1, b2, b3 = st.columns(3)
            b1.metric("Clientes", summary["n"])
            b2.metric("A contactar", summary["contacted"])
            b3.metric("Beneficio esperado", eur(summary["expected_benefit_eur"]))
            table = results_table(frame, response)
            st.dataframe(table, hide_index=True)
            st.download_button(
                "Descargar resultados", results_csv(table), "decisiones.csv", "text/csv"
            )

with about:
    final = model.get("final_test", {})
    metrics = final.get("metrics", {})
    a = model["assumptions"]
    st.subheader("Regla de decisión")
    st.write(
        f"Contactar si la probabilidad calibrada supera **{model['threshold']:.3f}** = c / (s·V), "
        f"con V = {eur(a['customer_value_eur'])}, c = {eur(a['contact_cost_eur'])} y "
        f"s = {a['retention_success_rate']:.0%}."
    )
    if metrics:
        st.subheader(f"Evaluación final en prueba ({final['n']} clientes, una sola vez)")
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("AP", f"{metrics['ap']:.3f}")
        k2.metric("ROC-AUC", f"{metrics['roc_auc']:.3f}")
        k3.metric("Brier", f"{metrics['brier']:.4f}")
        k4.metric("Beneficio del modelo", eur(final["benefit_model_eur"]))
    st.write(
        f"Modelo: {model['model_family']} calibrado ({model['calibrator']}). Variables: "
        + ", ".join(model["input_columns"])
        + ". Ficha completa en el repositorio (`reports/model_card.md`)."
    )

with drift:
    try:
        report = api.monitoring()
    except API_ERRORS as error:
        report = None
        st.error(str(error) or type(error).__name__)
    if report is None:
        st.info("Reporte de monitoreo no disponible en esta instancia.")
    else:
        st.write(
            "Simulación (spec 006 §4): referencia = entrenamiento; actual = validación "
            "remuestreada en cinco escenarios. Umbrales y expectativas preregistrados; la "
            "partición de prueba no se usa."
        )
        st.subheader("PSI por variable (alerta > 0,25)")
        st.dataframe(psi_table(report))
        st.subheader("Señales sin etiquetas y métricas con etiquetas")
        st.dataframe(monitoring_metrics(report))
        st.subheader("Expectativas preregistradas")
        st.dataframe(pd.DataFrame(expectation_rows(report)), hide_index=True)
        if report["expectations"]["E3"]["met"]:
            st.caption(
                "Lección: el cambio de prevalencia (S4) descalibra el modelo sin alarmas de PSI; "
                "sin etiquetas (retroalimentación) esa degradación no se detecta."
            )
