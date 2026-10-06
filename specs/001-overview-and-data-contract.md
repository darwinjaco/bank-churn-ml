# Especificación 001 — Visión general y contrato de datos

| Campo | Valor |
|---|---|
| Estado | Completada: verificación local y CI remoto satisfactorios |
| Responsable | Darwin Jacome Cuenca |
| Semana | 1 |
| Última revisión documental | 6 de octubre de 2026 |

## 1. Objetivo

Construir un **sistema de decisiones de retención**. Para cada cliente, el sistema debe responder:

1. ¿Cuál es la probabilidad de que abandone el banco? Probabilidad calibrada.
2. ¿Conviene contactarlo, considerando el costo de campaña, su valor y la eficacia supuesta de la retención? Beneficio esperado.
3. ¿Qué variables explican la predicción? Explicación local.

El éxito se medirá mediante el **beneficio esperado frente a políticas de referencia**: no contactar a nadie, contactar a todos y contactar a un 20 % al azar. La comparación respetará las mismas restricciones presupuestarias cuando correspondan; la exactitud y F1 serán métricas complementarias.

## 2. Contexto

- Fuente declarada: *Churn Modelling* de Kaggle (`shrutimechlearn/churn-modelling`), descrito como 10.000 clientes de un banco europeo, con 14 columnas.
- La versión esperada no tiene `Complain`; el caso de fuga asociado a esa columna no aplica a este archivo.
- Los patrones de productos y salarios suscitan una **hipótesis de origen sintético**, pendiente de verificar con la procedencia y la auditoría de datos (§6).
- El dataset no contiene ingresos del banco, CLV, costos de campaña ni datos de tratamiento. Los valores monetarios y la eficacia de contacto serán **supuestos explícitos**, sujetos a sensibilidad en la futura especificación 004.
- Los resultados serán evidencia de este ejercicio de modelado; no demostrarán impacto causal ni beneficio real de una campaña bancaria.

## 3. Alcance

| Incluido | Fuera del alcance |
|---|---|
| Predicción binaria de abandono, calibración y umbral por beneficio | Supervivencia o tiempo hasta el abandono |
| Explicabilidad global y local con SHAP | Afirmaciones causales o de efecto incremental (uplift) sin datos de tratamiento |
| Auditoría de segmentos y equidad | Incorporación de datos privados de una institución |
| API, dashboard, Docker, CI y cambio de distribución simulado | Autenticación, escalado y acuerdos de servicio de nivel productivo |

## 4. Contrato de datos

**Archivo de origen:** `data/raw/Churn_Modelling.csv`, excluido de Git; instrucciones en el [README](../README.md#datos).

**Unidad de observación:** una fila representa un cliente. **Clave primaria:** `CustomerId`. Ninguna columna admite nulos.

| Columna | Tipo | Valores permitidos | Rol | Descripción |
|---|---|---|---|---|
| `RowNumber` | int | ≥ 1, único | Identificador excluido | Índice de fila del archivo |
| `CustomerId` | int | Único | Identificador excluido | Clave del cliente |
| `Surname` | string | No vacío | Identificador excluido | Apellido |
| `CreditScore` | int | 300–900 | Variable candidata | Puntaje crediticio |
| `Geography` | string | France, Germany, Spain | Variable candidata | País |
| `Gender` | string | Female, Male | **Solo auditoría** | Auditoría de equidad; excluido de las entradas |
| `Age` | int | 18–100 | Variable candidata | Edad en años |
| `Tenure` | int | 0–10 | Variable candidata | Años como cliente |
| `Balance` | float | ≥ 0 | Variable candidata | Saldo de cuenta |
| `NumOfProducts` | int | 1–4 | Variable candidata | Número de productos bancarios |
| `HasCrCard` | int | {0, 1} | Variable candidata | Indicador de tarjeta de crédito |
| `IsActiveMember` | int | {0, 1} | Variable candidata | Indicador de actividad |
| `EstimatedSalary` | float | > 0 | Variable candidata; evaluar en E-03 | Salario estimado del cliente; no equivale a ingresos del banco |
| **`Exited`** | int | {0, 1} | **Variable objetivo** | 1 = el cliente abandonó el banco |

**Entradas candidatas:** las 9 columnas de variables declaradas en `MODEL_FEATURES`, en `src/churn/config.py`. Su selección final se justificará con los experimentos de la [especificación 002](002-modeling-and-evaluation.md).

**Salida prevista del sistema:** `churn_probability ∈ [0, 1]`, `contact: bool`, `expected_profit` y `top_reasons`. El modelo aportará la probabilidad, la capa de decisión calculará el contacto y beneficio, y la capa de explicación aportará las razones. Estas salidas aún no están implementadas.

## 5. Reglas de validación

Implementadas en `src/churn/data.py` y `src/churn/validation.py`.

- **Comprobaciones obligatorias:** columnas exactas, tipos, ausencia de nulos, rangos y categorías de §4, unicidad de `RowNumber` y `CustomerId`, y objetivo binario. Una infracción detiene la validación. Pandera recopila los errores del esquema con `lazy=True`; los errores de cabecera o conversión de tipos pueden detener antes la carga del CSV.
- **Comprobaciones informativas:** duplicados ignorando `RowNumber`, proporción de abandono, fracción de `Balance = 0`, abandono por `NumOfProducts`, salarios menores a 1.000, cardinalidad de apellidos y AUC de variables numéricas individuales.
- **Alarma de posible fuga:** `max(AUC, 1 − AUC) ≥ 0,90`, incluyendo relaciones inversas. Es una señal para investigar, no una prueba concluyente de presencia o ausencia de fuga.
- El reporte se escribe en `reports/data_quality.json` al usar `--out`. Sus advertencias no detienen el proceso y deben interpretarse junto con la auditoría documental.

## 6. Hallazgos y limitaciones de los datos

Evidencia: [reporte de calidad](../reports/data_quality.json), reproducido con el CSV local el 6 de octubre de 2026. Las interpretaciones de origen sintético del reporte son hipótesis por contrastar.

| ID | Hallazgo | Evidencia registrada | Tratamiento previsto |
|---|---|---|---|
| Q-01 | Clases desbalanceadas | Abandono del 20,37 % | Divisiones estratificadas; precisión promedio como métrica principal |
| Q-02 | Masa puntual en `Balance = 0` | 36,17 % de las filas | Evaluar el indicador `has_balance` en la semana 3 |
| Q-03 | Abandono muy alto con 3–4 productos en un grupo pequeño | 82,71 % en 266 clientes con 3 productos; 100 % en 60 con 4 | Auditar incertidumbre y dependencia del modelo; experimento E-02. El patrón no demuestra por sí solo un origen sintético |
| Q-04 | Señal individual débil de `EstimatedSalary` y valores bajos | AUC de 0,5087; 59 valores menores a 1.000 | Revisar distribución, unidades y contexto en EDA; medir su aporte combinado mediante E-03 antes de excluirla |
| Q-05 | Sin alarma en el análisis univariado disponible | Máximo de `max(AUC, 1 − AUC)`: `Age`, 0,7321 | Revisar procedencia, disponibilidad de variables y separación de datos; repetir controles después de crear variables |

Hallazgos Q-06 en adelante: [reporte de hipótesis](../reports/eda_hypotheses.md) y [JSON](../reports/hypotheses.json), calculados exclusivamente en 8.000 filas de entrenamiento + validación bajo la especificación 003 v1.1. H1–H5 usan Holm; H6 se evalúa por equivalencia. Son asociaciones, no efectos causales.

| ID | Hallazgo | Evidencia de exploración (IC 95 %) | Tratamiento previsto |
|---|---|---|---|
| Q-06 | Inactividad asociada a mayor abandono (H1) | DR +12,27 pp [10,51; 14,03]; OR 2,1610 | Conservar la evaluación de `IsActiveMember` en el pipeline previsto |
| Q-07 | Relación no monótona con productos (H2) | Tasas 2 < 1 < 3–4: 7,38 % < 27,98 % < 85,60 %; IC no solapados; n(3–4)=257 | Priorizar E-02 y la auditoría del grupo pequeño; el patrón no prueba origen sintético |
| Q-08 | Asociación de Alemania persiste tras ajustar por saldo (H3) | OR ajustado 2,1787 [1,9133; 2,4809]; atenuación del log-OR 17,46 % | Documentar segmentos y límites del ajuste; sin interpretación causal |
| Q-09 | Edad con U invertida en el modelo inferencial fijado (H4) | β cuadrático −0,003429 [−0,003855; −0,003002]; pico puntual 56,58 años | Evaluar `age_band` ya prevista; cualquier incorporación al modelo requiere CV |
| Q-10 | Saldo cero asociado a menor abandono (H5) | DR −10,62 pp [−12,31; −8,88]; saldo cero en 36,14 % de exploración | Evaluar `has_balance` ya propuesto junto al saldo continuo |
| Q-11 | Salario bruto dentro del margen de equivalencia de AUC (H6) | AUC 0,5146 [0,4997; 0,5306] dentro de [0,45; 0,55] | Ejecutar E-03; no descartar utilidad combinada o no lineal por este resultado |

## 7. Decisiones técnicas

| ID | Decisión | Justificación |
|---|---|---|
| D-01 | Excluir `RowNumber`, `CustomerId` y `Surname` | Son identificadores. `Surname` tiene 2.932 valores y puede favorecer sobreajuste o actuar como proxy de nacionalidad u origen |
| D-02 | `Gender` nunca como entrada del modelo, tampoco en experimentos; conservarlo solo para auditoría | Regla del proyecto en `AGENTS.md`. E-01 auditará resultados por grupos; no medirá un modelo que incluya `Gender`. La exclusión no garantiza equidad |
| D-03 | Conservar el CSV original sin modificaciones y fuera de Git | Datos obtenidos por separado bajo las condiciones de su fuente; carga reproducible mediante `load_raw()` |
| D-04 | Ejecutar CI con muestras sintéticas | CI independiente del dataset; el test `realdata` se omite si falta el archivo |
| D-05 | Validar el esquema con Pandera | Contrato declarativo y recopilación de infracciones |
| D-06 | Mantener `EstimatedSalary` como candidata hasta E-03 | La AUC individual no mide interacciones ni demuestra ausencia de utilidad predictiva |

## 8. Criterios de aceptación

La evidencia local está en S02 del [registro de avance](../docs/registro-avance.md), y la remota en S03. El [CI del commit `3c157c0`](https://github.com/darwinjaco/bank-churn-ml/actions/runs/37419500890) pasó en `main` con cobertura del 95,58 % sin el dataset real.

- [x] `uv sync --locked` instala desde el archivo de bloqueo en un entorno nuevo y los tests pasan con y sin el CSV; el test real se omite si falta.
- [x] `uv run churn-validate --out reports/data_quality.json` pasa con el archivo real y reproduce el reporte.
- [x] Rechazo verificado de rangos, categorías, unicidad, nulos, tipos y columnas faltantes o adicionales: tests existentes y comprobación complementaria de S02.
- [x] Ruff y las comprobaciones de pre-commit pasan.
- [x] CI pasa en `main` con cobertura de al menos 85 % y se registra el enlace de la ejecución.

## 9. Definición de cierre

Implementación versionada, comprobaciones locales y CI satisfactorios, hallazgos contrastados con el CSV y documentación de adquisición de datos reproducible. Los criterios se marcan únicamente cuando hay evidencia; el cierre de una sección documental no implica el cierre técnico de la semana 1.
