"""Retención bancaria: decisiones, evidencia y gráficos (spec 005 v1.3). Solo API."""

from __future__ import annotations

import httpx
import pandas as pd
import streamlit as st

from churn import presentation as visual
from churn.examples import generate
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
DEFAULT_CUSTOMER = {
    "CreditScore": 650,
    "Age": 45,
    "Tenure": 4,
    "Balance": 90000.0,
    "NumOfProducts": 1,
    "Geography": "France",
    "HasCrCard": 1,
    "IsActiveMember": 0,
}
EXAMPLE_CUSTOMER = {
    "CreditScore": 600,
    "Age": 52,
    "Tenure": 3,
    "Balance": 120000.0,
    "NumOfProducts": 1,
    "Geography": "Germany",
    "HasCrCard": 1,
    "IsActiveMember": 0,
}
MODEL_CARD = "https://github.com/darwinjaco/bank-churn-ml/blob/main/reports/model_card.md"

st.set_page_config(page_title="Retención bancaria", page_icon="🏦", layout="wide")


@st.cache_resource
def get_client() -> ApiClient:
    """Solo se comparte el transporte HTTP, nunca perfiles ni resultados."""
    return ApiClient()


def error_message(error: Exception) -> None:
    st.error(
        "No se pudo completar el análisis. Revisa los datos o vuelve a intentarlo en un momento."
    )
    st.caption(str(error) or type(error).__name__)


def show_chart(spec: dict, description: str) -> None:
    st.vega_lite_chart(spec=spec, width="stretch", alt=description)


def wrap_columns(widths: list[int], *, gap: str = "medium") -> list:
    """Paneles nativos que se apilan cuando no hay ancho suficiente, también con zoom."""
    with st.container(horizontal=True, wrap=True, gap=gap):
        return [st.container(width=width) for width in widths]


def load_example() -> None:
    st.session_state["client_inputs"] = dict(EXAMPLE_CUSTOMER)
    st.session_state.pop("client_result", None)
    for name, value in EXAMPLE_CUSTOMER.items():
        st.session_state[f"customer_{name}"] = (
            bool(value) if name in {"HasCrCard", "IsActiveMember"} else value
        )


def clear_batch() -> None:
    for name in ("batch_payload", "batch_result"):
        st.session_state.pop(name, None)
    st.session_state["upload_version"] = st.session_state.get("upload_version", 0) + 1


def methodology(model: dict) -> None:
    assumptions = model["assumptions"]
    with st.expander("Metodología y supuestos"):
        st.write(
            "Modelo entrenado con datos bancarios públicos, probablemente sintéticos. "
            "La decisión combina una probabilidad calibrada con supuestos económicos "
            "ilustrativos; el beneficio mostrado no es un ingreso garantizado."
        )
        st.write(
            f"Valor del cliente: **{eur(assumptions['customer_value_eur'])}**. "
            f"Coste de contacto: **{eur(assumptions['contact_cost_eur'])}**. "
            "Éxito supuesto de retención: "
            f"**{visual.percent(assumptions['retention_success_rate'])}**."
        )
        st.write(
            f"Contactar solo si p > c / (s * V) = **{visual.percent(model['threshold'])}**. "
            "Los factores del modelo describen asociaciones, no efectos causales."
        )
        st.link_button("Consultar ficha del modelo", MODEL_CARD)


def render_client(api: ApiClient, model: dict) -> None:
    st.header("Análisis del cliente")
    st.write("Evalúa el riesgo de abandono y la conveniencia económica de una acción de retención.")
    form_column, result_column = wrap_columns([390, 530])
    with form_column, st.container(border=True):
        st.subheader("Perfil del cliente")
        st.button(
            "Cargar ejemplo",
            on_click=load_example,
            help="Perfil ilustrativo que reproduce la referencia del modelo.",
        )
        defaults = st.session_state.get("client_inputs", DEFAULT_CUSTOMER)
        for name, value in defaults.items():
            key = f"customer_{name}"
            if key not in st.session_state:
                st.session_state[key] = (
                    bool(value) if name in {"HasCrCard", "IsActiveMember"} else value
                )
        with st.form("cliente"):
            c1, c2 = st.columns(2)
            customer = {
                "CreditScore": c1.number_input(
                    "Puntuación crediticia",
                    300,
                    900,
                    key="customer_CreditScore",
                    help="CreditScore: puntuación del contrato, entre 300 y 900.",
                ),
                "Age": c1.number_input(
                    "Edad", 18, 100, key="customer_Age", help="Age: edad del cliente en años."
                ),
                "Tenure": c1.number_input(
                    "Antigüedad (años)",
                    0,
                    10,
                    key="customer_Tenure",
                    help="Tenure: años de relación con el banco.",
                ),
                "Balance": c2.number_input(
                    "Saldo (€)",
                    min_value=0.0,
                    step=1000.0,
                    key="customer_Balance",
                    help="Balance: saldo no negativo; no existe un máximo en el contrato.",
                ),
                "NumOfProducts": c2.selectbox(
                    "Productos",
                    [1, 2, 3, 4],
                    key="customer_NumOfProducts",
                    help="NumOfProducts: número de productos contratados.",
                ),
                "Geography": c2.selectbox(
                    "País",
                    list(visual.COUNTRIES),
                    format_func=visual.COUNTRIES.get,
                    key="customer_Geography",
                    help="Geography: país del contrato.",
                ),
                "HasCrCard": int(c1.checkbox("Tarjeta de crédito", key="customer_HasCrCard")),
                "IsActiveMember": int(
                    c2.checkbox(
                        "Miembro activo",
                        key="customer_IsActiveMember",
                        help="IsActiveMember: indicador de actividad registrado por el banco.",
                    )
                ),
            }
            submitted = st.form_submit_button("Analizar cliente", type="primary", width="stretch")
        if submitted:
            st.session_state["client_inputs"] = customer
            st.session_state.pop("client_result", None)
            try:
                with st.spinner("Calculando recomendación…"):
                    result = api.explain(customer)
                st.session_state["client_result"] = {"customer": customer, "result": result}
            except API_ERRORS as error:
                error_message(error)
    with result_column:
        saved = st.session_state.get("client_result")
        if saved is None:
            with st.container(border=True):
                st.subheader("Una decisión con contexto")
                st.write(
                    "Al analizar el perfil verás el riesgo, la recomendación "
                    "y los factores que la explican."
                )
                st.info("Completa los datos o carga el ejemplo y selecciona «Analizar cliente».")
            return
        result = saved["result"]
        prediction = result["prediction"]
        st.subheader("Resultado del análisis")
        st.caption(
            "Corresponde al perfil evaluado. Los cambios en el formulario "
            "se aplican al analizar de nuevo."
        )
        if customer != saved["customer"]:
            st.info(
                "El formulario contiene cambios sin analizar; se muestra el último perfil evaluado."
            )
        m1, m2, m3 = wrap_columns([160, 160, 160], gap="small")
        m1.metric("Riesgo de abandono", visual.percent(prediction["churn_probability"]))
        m2.metric("Decisión", "Contactar" if prediction["contact"] else "No contactar")
        m3.metric(
            "Valor esperado (€)",
            eur(prediction["expected_benefit_eur"]),
            help="Beneficio esperado si se contacta a este cliente, "
            "bajo los supuestos económicos del modelo.",
        )
        threshold = prediction.get("threshold", model["threshold"])
        show_chart(
            visual.risk_chart(prediction["churn_probability"], threshold),
            f"Riesgo {visual.percent(prediction['churn_probability'])}; "
            f"umbral de contacto {visual.percent(threshold)}.",
        )
        st.caption(
            f"Línea discontinua: umbral {visual.percent(threshold)}. "
            "Se recomienda contactar solo por encima de él."
        )
        st.subheader("Factores de la predicción")
        if prediction.get("top_reasons"):
            show_chart(
                visual.reasons_chart(prediction),
                "Tres contribuciones SHAP con signo; sus valores y efectos "
                "están en la tabla de detalle.",
            )
        else:
            st.info("No hay factores locales disponibles para esta respuesta.")
        st.caption(
            "Contribuciones en puntos porcentuales de la probabilidad sin calibrar. "
            "No son causas ni suman al porcentaje calibrado mostrado arriba."
        )
        st.text(result["text"])
        with st.expander("Datos evaluados y detalle"):
            st.dataframe(
                pd.DataFrame(
                    [
                        {"Dato": visual.feature_label(name), "Valor": str(value)}
                        for name, value in saved["customer"].items()
                    ]
                ),
                hide_index=True,
                width="stretch",
            )
            if prediction.get("top_reasons"):
                st.dataframe(
                    pd.DataFrame(reason_rows(prediction)).rename(
                        columns={"Contribución (pp)": "Contribución sin calibrar (pp)"}
                    ),
                    hide_index=True,
                    width="stretch",
                )
            st.caption(
                "Origen de la explicación: "
                + ("LLM" if result["source"] == "llm" else "plantilla determinista")
            )


def render_batch(api: ApiClient, model: dict) -> None:
    st.header("Análisis por lote")
    st.write(
        "Procesa una cartera, identifica los contactos recomendados y descarga las decisiones."
    )
    with st.container(border=True):
        left, right = st.columns([2, 1])
        left.write(
            "CSV UTF-8 · máximo 1 MiB y 1.000 clientes. Las columnas adicionales se descartan."
        )
        right.download_button(
            "Descargar CSV de ejemplo",
            generate(),
            "clientes_ejemplo.csv",
            "text/csv",
            on_click="ignore",
            width="stretch",
        )
        with st.expander("Columnas y formato del archivo"):
            st.code(
                "CreditScore,Age,Tenure,Balance,NumOfProducts,HasCrCard,IsActiveMember,Geography",
                language=None,
            )
            st.write(
                "Tarjeta y actividad: 0 o 1. País: France, Germany o Spain. "
                "Decimales con punto y columnas separadas por coma. "
                "El ejemplo contiene 20 perfiles sintéticos."
            )
        upload = st.file_uploader(
            "Archivo CSV",
            type="csv",
            max_upload_size=1,
            key=f"batch_upload_{st.session_state.get('upload_version', 0)}",
        )
        if upload is not None:
            try:
                customers = prepare_batch(read_batch_csv(upload))
                identity = visual.batch_identity(customers)
                previous = st.session_state.get("batch_payload", {})
                if previous.get("identity") != identity:
                    st.session_state.pop("batch_result", None)
                st.session_state["batch_payload"] = {"customers": customers, "identity": identity}
            except (ValueError, pd.errors.ParserError) as error:
                st.session_state.pop("batch_payload", None)
                st.session_state.pop("batch_result", None)
                st.error(str(error))
                st.caption(
                    "Corrige el archivo y vuelve a cargarlo; puedes usar el ejemplo como plantilla."
                )
        payload = st.session_state.get("batch_payload")
        if payload:
            st.caption(
                f"Lote en esta sesión: {visual.number(len(payload['customers']))} clientes. "
                "No se procesa hasta que lo solicites."
            )
        actions = st.columns([1, 1, 2])
        process = actions[0].button(
            "Procesar lote", type="primary", disabled=payload is None, width="stretch"
        )
        actions[1].button(
            "Vaciar lote", on_click=clear_batch, disabled=payload is None, width="stretch"
        )
        if process and payload:
            st.session_state.pop("batch_result", None)
            try:
                with st.spinner("Analizando cartera…"):
                    st.session_state["batch_result"] = api.batch(payload["customers"])
            except API_ERRORS as error:
                error_message(error)
    response = st.session_state.get("batch_result")
    if response is None or payload is None:
        st.info(
            "Carga un archivo y selecciona «Procesar lote» para ver la distribución del riesgo."
        )
        return
    summary = response["summary"]
    a, b, c = wrap_columns([240, 240, 320])
    a.metric("Clientes analizados", visual.number(summary["n"]))
    b.metric("Contactos recomendados", visual.number(summary["contacted"]))
    c.metric(
        "Beneficio esperado de los contactos",
        eur(summary["expected_benefit_eur"]),
        help="Suma del valor esperado de quienes se recomienda contactar; "
        "no incluye los no contactados.",
    )
    charts = wrap_columns([500, 420])
    with charts[0]:
        st.subheader("Distribución del riesgo")
        show_chart(
            visual.histogram_chart(response["predictions"], model["threshold"]),
            "Clientes por intervalo de probabilidad calibrada; línea de umbral de contacto.",
        )
        st.caption(
            "Diez intervalos del lote completo; "
            f"línea de umbral {visual.percent(model['threshold'])}."
        )
    with charts[1]:
        st.subheader("Acciones recomendadas")
        show_chart(
            visual.decisions_chart(response["predictions"]),
            f"Contactar a {summary['contacted']} de {summary['n']} clientes.",
        )
        st.caption("Decisiones de la API; no se recalculan a partir de porcentajes redondeados.")
    table = results_table(pd.DataFrame(payload["customers"]), response)
    st.subheader("Detalle de la cartera")
    only_contacts = st.checkbox("Mostrar solo contactos recomendados", key="only_contacts")
    display = table[table["contactar"] == "sí"].copy() if only_contacts else table.copy()
    display["probabilidad_abandono"] *= 100
    st.dataframe(
        display,
        hide_index=True,
        width="stretch",
        column_config={
            **{
                name: st.column_config.Column(visual.feature_label(name))
                for name in visual.FEATURE_LABELS
                if name in display
            },
            "probabilidad_abandono": st.column_config.ProgressColumn(
                "Riesgo (%)", min_value=0, max_value=100, format="%.1f %%"
            ),
            "contactar": st.column_config.TextColumn("Contactar"),
            "beneficio_esperado_eur": st.column_config.NumberColumn(
                "Valor esperado del contacto (€)", format="%.2f"
            ),
        },
    )
    st.download_button(
        "Descargar resultados completos",
        results_csv(table),
        "decisiones.csv",
        "text/csv",
        on_click="ignore",
        type="primary",
    )
    st.caption(
        "La descarga incluye todo el lote normalizado y ordenado por riesgo, "
        "sin identificadores ni columnas extra."
    )
    with st.expander("Datos de los gráficos"):
        st.dataframe(
            pd.DataFrame(visual.probability_bins(response["predictions"])), hide_index=True
        )
        st.dataframe(pd.DataFrame(visual.decision_counts(response["predictions"])), hide_index=True)


def render_model(model: dict) -> None:
    st.header("Evidencia del modelo")
    st.write(
        "Resultados registrados una sola vez, "
        "con modelo, calibración y regla de contacto congelados."
    )
    final = model.get("final_test", {})
    metrics = final.get("metrics", {})
    if metrics:
        st.caption(
            f"Evaluación final histórica sobre {visual.number(final['n'])} clientes. "
            "No representa una campaña en curso."
        )
        columns = wrap_columns([180, 180, 180, 260])
        for col, key, label, digits, help_text in [
            (
                columns[0],
                "ap",
                "AP",
                3,
                "Precisión promedio: calidad del ordenamiento de los clientes; mayor es mejor.",
            ),
            (
                columns[1],
                "roc_auc",
                "ROC-AUC",
                3,
                "Capacidad de distinguir abandono y permanencia; mayor es mejor.",
            ),
            (columns[2], "brier", "Brier", 4, "Error de las probabilidades; menor es mejor."),
        ]:
            col.metric(
                label,
                visual.number(metrics[key], digits) if key in metrics else "—",
                help=help_text,
            )
        columns[3].metric("Beneficio bajo los supuestos", eur(final["benefit_model_eur"]))
        policies = visual.policy_data(final)
        if policies:
            st.subheader("Valor de la política de retención")
            show_chart(
                visual.policies_chart(final),
                "Comparación histórica de beneficios en euros entre el modelo, "
                "contactar a todos y no contactar; cifras en la tabla de detalle.",
            )
            st.caption(
                "Beneficio calculado con etiquetas históricas y supuestos ilustrativos; "
                "no es valor causal ni una garantía de ingresos."
            )
            with st.expander("Cifras de la comparación"):
                st.dataframe(
                    pd.DataFrame(policies).rename(
                        columns={
                            "policy": "Política",
                            "benefit_eur": "Beneficio (€)",
                            "contacted": "Contactados",
                            "label": "Beneficio formateado",
                        }
                    ),
                    hide_index=True,
                    width="stretch",
                )
        else:
            st.info("Este reporte no incluye el detalle de políticas económicas.")
    else:
        st.info("La evaluación final no está disponible en esta instancia.")
    st.subheader("Cómo se obtiene la recomendación")
    family = {"rf": "Random Forest"}.get(model["model_family"], model["model_family"])
    calibration = {"sigmoid": "sigmoide"}.get(model["calibrator"], model["calibrator"])
    st.write(
        f"**{family}**, con calibración **{calibration}** "
        f"y umbral económico **{visual.percent(model['threshold'])}**."
    )
    st.write(
        "Variables del modelo: "
        + ", ".join(visual.feature_label(name).lower() for name in model["input_columns"])
        + "."
    )


def render_monitoring(api: ApiClient) -> None:
    st.header("Monitoreo de distribución")
    st.write(
        "Explora cómo distintos cambios de población afectan al riesgo, "
        "las decisiones y la calibración."
    )
    if "monitoring_report" not in st.session_state:
        try:
            with st.spinner("Cargando escenarios…"):
                st.session_state["monitoring_report"] = api.monitoring()
        except API_ERRORS as error:
            error_message(error)
            return
    report = st.session_state["monitoring_report"]
    if report is None:
        st.info("El reporte de monitoreo no está disponible en esta instancia.")
        st.button(
            "Reintentar informe", on_click=lambda: st.session_state.pop("monitoring_report", None)
        )
        return
    st.caption(
        "Simulación con entrenamiento y validación; la partición de prueba no se vuelve a evaluar."
    )
    names = {
        "S0": "Control sin cambio",
        "S1": "Clientes de mayor edad",
        "S2": "Más clientes en Alemania",
        "S3": "Más clientes inactivos",
        "S4": "Mayor prevalencia de abandono",
    }
    selected = st.selectbox(
        "Escenario",
        list(report["scenarios"]),
        format_func=lambda key: f"{key}: {names.get(key, key)}",
    )
    scenario = report["scenarios"][selected]
    st.caption(scenario["description"])
    c1, c2, c3 = wrap_columns([240, 240, 240])
    c1.metric("Contacto recomendado", visual.percent(scenario["unlabeled"]["contact_rate"]))
    c2.metric("Alarma de distribución", "Sí" if scenario["alarm"] else "No")
    c3.metric("Degradación del modelo", "Sí" if scenario["degradation"]["degraded"] else "No")
    charts = wrap_columns([450, 450])
    with charts[0]:
        st.subheader("Cambio por variable")
        show_chart(
            visual.psi_chart(scenario, report["config"]["psi"]),
            f"PSI por variable para {selected}; valores y niveles en tabla de detalle.",
        )
        limits = report["config"]["psi"]
        st.caption(
            f"PSI: estable < {visual.number(limits['stable_below'], 2)}, "
            f"alerta > {visual.number(limits['alert_above'], 2)}. "
            "Mayor valor indica mayor cambio."
        )
    with charts[1]:
        st.subheader("Desviación de calibración")
        show_chart(
            visual.calibration_chart(report),
            "Desviación de probabilidad media frente al abandono observado, "
            "en puntos porcentuales, para los cinco escenarios.",
        )
        tolerance = report["config"]["degradation"]["calibration_tolerance"] * 100
        st.caption(
            f"Banda de tolerancia: ±{visual.number(tolerance, 1)} pp. "
            "Valores negativos indican que el modelo subestima el abandono."
        )
    st.subheader("Lectura de los resultados")
    e2 = report["expectations"].get("E2")
    if e2 and not e2["met"]:
        st.warning(
            "E2 no se cumplió: el cambio de actividad en S3 quedó por debajo "
            "del umbral de alarma. El criterio se conserva y el resultado se reporta."
        )
    e3 = report["expectations"].get("E3")
    if e3 and e3["met"]:
        st.info(
            "S4 muestra el límite del monitoreo de entradas: la calibración se degrada "
            "sin alarma de PSI. Para detectarlo hacen falta etiquetas de abandono."
        )
    with st.expander("Tablas y expectativas preregistradas"):
        st.dataframe(pd.DataFrame(visual.psi_data(scenario)), hide_index=True, width="stretch")
        st.dataframe(
            pd.DataFrame(visual.calibration_data(report)), hide_index=True, width="stretch"
        )
        st.dataframe(psi_table(report), width="stretch")
        st.dataframe(monitoring_metrics(report), width="stretch")
        st.dataframe(pd.DataFrame(expectation_rows(report)), hide_index=True, width="stretch")


api = get_client()
st.title("Retención bancaria")
st.caption("Prioriza acciones de retención según el riesgo de abandono y el beneficio esperado.")
if "model_info" not in st.session_state:
    try:
        with st.spinner("Conectando con el modelo…"):
            st.session_state["model_info"] = api.model()
    except API_ERRORS:
        st.error(
            "No se pudo conectar con el modelo. El servicio puede estar arrancando; "
            "vuelve a intentarlo en un momento."
        )
        st.button("Reintentar conexión")
        st.stop()
model = st.session_state["model_info"]
with st.sidebar:
    st.header("Retención bancaria")
    st.caption("Análisis y decisiones")
    view = st.radio("Navegación", ["Cliente", "Lote", "Modelo", "Monitoreo"], key="view")
    st.divider()
    st.markdown("**Regla de contacto**")
    st.write(f"Probabilidad > {visual.percent(model['threshold'])}")
    st.caption("Modelo calibrado · supuestos económicos fijos")
    st.link_button("Ficha del modelo", MODEL_CARD)

if view == "Cliente":
    render_client(api, model)
elif view == "Lote":
    render_batch(api, model)
elif view == "Modelo":
    render_model(model)
else:
    render_monitoring(api)

st.divider()
methodology(model)
