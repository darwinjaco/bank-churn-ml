# Especificación 006 — Despliegue, monitoreo simulado y cierre

| Campo | Valor |
|---|---|
| Estado | Entrega `v1.0.1` cerrada en `9384e51`, Render/CI comprobados; ampliación documental v1.4 (§15): memoria técnica LaTeX |
| Responsable | Darwin Jacome Cuenca |
| Semana | 8 (23–29 de noviembre de 2026) |
| Dependencias | [002](002-modeling-and-evaluation.md) (artefacto congelado), [004](004-decision-layer.md) (regla de decisión), [005](005-api-and-dashboard.md) (API, dashboard e imagen) |
| Decisiones del responsable | D1 = A (PSI + KS/chi² propios), D2 = A (LLM con límite por hora), D3 = Space público `<usuario-hf>/bank-churn-ml` (usuario provisional `darwinjaco`, B-03) |

## 1. Objetivo

Cerrar el proyecto con una **demo pública reproducible**, un **monitoreo simulado** que responda si las alertas de distribución detectan los cambios que de verdad degradan el modelo, y un **repositorio de portafolio** verificable desde un clon limpio.

El modelo está congelado (`model-v1.0`, SHA-256 `579b7fe3…095a`): no se reentrena ni cambian variables, calibración, umbral o supuestos. La partición de prueba no se vuelve a usar, tampoco para monitoreo.

## 2. Despliegue en Hugging Face Spaces

### 2.1 Arquitectura

```text
Visitante ──HTTPS──▶ Space (Docker, ROLE=all)
                       ├─ Streamlit :7860   (único puerto público)
                       └─ FastAPI 127.0.0.1:8000 (no expuesta) ──▶ modelo del Release + SHAP
                                                               └──▶ LLM opcional (secretos del Space)
```

- Misma imagen que la spec 005. En el build se descarga `model.joblib` del Release `model-v1.0` y **el build falla si el SHA-256 no coincide**.
- La API escucha solo en `127.0.0.1`; no se publica `/docs` en la URL del Space.

### 2.2 Contenido del Space

`scripts/build_space.py` arma un directorio con **exactamente** estos archivos:

| Archivo | Origen |
|---|---|
| `Dockerfile` | Derivado del `Dockerfile` del repositorio, solo con la variante `release` (§2.3) |
| `pyproject.toml`, `uv.lock` | Repositorio |
| `src/churn/*.py`, `dashboard/*.py`, `docker/start.sh` | Repositorio |
| `.streamlit/config.toml` | Tema nativo del dashboard (enmienda spec 005 v1.3) |
| `reports/model_metadata.json`, `reports/final_test.json`, `reports/monitoring.json` | Repositorio (el Dockerfile copia los tres; §4.9) |
| `README.md` | `deploy/space/README.md` (cabecera YAML del Space) |

El script **falla** si el resultado contiene un archivo binario (bytes nulos o no UTF-8), cualquier ruta bajo `data/`, `models/` o `mlruns/`, un `.env`, un `.csv` o un `.joblib`/`.parquet`. Hugging Face rechaza binarios sin LFS; por eso el Space no lleva figuras.

### 2.3 Dockerfile del Space (decisión tomada en T0)

El `Dockerfile` del repositorio selecciona la etapa del modelo con `FROM model-${MODEL_SOURCE}` y su variante `local` usa un contexto adicional (`localmodel`) que solo existe con `docker-compose.local.yml`. Un builder que construya todas las etapas, o que no resuelva contextos adicionales, fallaría en el Space. Por eso `build_space.py` genera el Dockerfile del Space **solo con la variante `release`**: elimina `ARG MODEL_SOURCE`, la etapa `model-local` y reemplaza `FROM model-${MODEL_SOURCE}` por `FROM model-release`. Cada sustitución debe ocurrir exactamente una vez; si el `Dockerfile` cambia de forma incompatible, el script falla en lugar de producir un archivo dudoso. Se decide antes del primer build para no improvisar tras un fallo (el plan lo preveía como contingencia).

### 2.4 Sincronización GitHub → Space

- Workflow `.github/workflows/deploy-space.yml`: `workflow_dispatch` y `push` de etiquetas `v*`.
- Pasos: checkout → `python scripts/build_space.py --out <tmp>` → `git init` en ese directorio → commit → `git push --force` a `https://huggingface.co/spaces/${HF_SPACE}`.
- Configuración en GitHub: secreto `HF_TOKEN` (token de escritura) y variable `HF_SPACE` (`<usuario-hf>/bank-churn-ml`). Si falta alguno, el workflow falla con un mensaje explícito.
- El token solo viaja en una variable de entorno (GitHub lo enmascara); sin `set -x` y sin imprimir la URL autenticada.
- Prerrequisito del responsable: crear el Space vacío (SDK **Docker**, plantilla *Blank*, público) antes de la primera sincronización.

### 2.5 Verificación pública

En `https://<usuario-hf>-bank-churn-ml.hf.space`:

- `/_stcore/health` responde `ok`.
- Pestaña **Cliente** con el cliente de referencia (CreditScore 600, Age 52, Tenure 3, Balance 120000, NumOfProducts 1, HasCrCard 1, IsActiveMember 0, Geography Germany) → probabilidad **0,947** y **contactar**.
- Pestaña **Lote** con `examples/clientes_ejemplo.csv` (§5).
- Pestaña **Modelo** con las métricas de la evaluación final.
- Se registran URL, tiempo de build, tamaño de imagen y capturas. El Space gratuito se suspende tras inactividad: el primer acceso es lento (aviso en el README).

## 3. LLM en la demo pública (D2 = A)

- Secretos del Space: `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL`. Nunca en el repositorio.
- `LLM_MAX_CALLS_PER_HOUR` (entero ≥ 0, por defecto **30**): ventana deslizante de 3.600 s, en memoria y por proceso, protegida con un *lock* (FastAPI atiende peticiones en hilos).
  - Cuenta cada **intento** de llamada al LLM, también los fallidos.
  - Superado el límite → plantilla con `source="template"` y `reason="límite de llamadas por hora"`.
  - `0` desactiva el LLM. Un valor no entero o negativo se ignora y se usa 30 (por defecto documentado).
- Limitaciones: el contador se reinicia con el Space; el límite es global, no por visitante. Protege el costo, no evita el abuso. Control complementario fuera del código: un modelo gratuito o una clave con tope de gasto en el proveedor.

## 4. Monitoreo simulado de cambios de distribución (D1 = A)

### 4.1 Pregunta

¿Detectan las alertas de distribución los cambios que de verdad degradan el modelo?

### 4.2 Datos

- **Referencia:** partición de entrenamiento (6.000 clientes), solo las variables del modelo.
- **Actual:** partición de **validación** (2.000 clientes) remuestreada con reemplazo, tamaño n = 2.000, semilla **2028** (un generador nuevo por escenario, para que el resultado no dependa del orden).
- Los datos se cargan con `load_exploration()` (solo entrenamiento y validación). **Nunca la partición de prueba**: el módulo no tiene ninguna ruta que la lea.
- Remuestrear en función de X (S1–S3) conserva P(y|X): las etiquetas siguen siendo válidas y las métricas reales se pueden medir bajo cada escenario. S4 remuestrea en función de y y conserva P(X|y).

### 4.3 Escenarios

| Escenario | Definición | Tipo de cambio |
|---|---|---|
| S0 | Validación tal cual, sin remuestrear | Control de falsas alarmas |
| S1 | Muestreo ponderado con pesos ∝ exp(0,05 · (Age − mediana de Age en validación)) | Covariable continua |
| S2 | Composición exacta: proporción de `Geography = Germany` × 2 | Covariable categórica |
| S3 | Composición exacta: proporción de `IsActiveMember = 0` = 70 % | Covariable binaria |
| S4 | Composición exacta por etiqueta: tasa de abandono = 35 % | Cambio de prevalencia (no de covariables) |

**Composición exacta** (S2–S4): se toman round(q·n) filas con reemplazo del grupo objetivo y n − round(q·n) del resto. La proporción objetivo se alcanza sin ruido de muestreo; dentro de cada grupo la distribución se conserva.

### 4.4 Métricas por escenario

- **PSI** = Σ (a_k − e_k) · ln(a_k / e_k), con e = proporciones de referencia y a = actuales. Las proporciones nulas se reemplazan por ε = 1·10⁻⁴ antes de calcular, para evitar ln(0). Es una convención documentada y no cambia la lectura de los umbrales.
  - Numéricas continuas (`CreditScore`, `Age`, `Balance`): deciles de la referencia; los bordes repetidos se eliminan (`Balance` tiene ~36 % de ceros) y los intervalos son cerrados por la derecha, con extremos abiertos.
  - Discretas (`Tenure`, `NumOfProducts`, `HasCrCard`, `IsActiveMember`, `Geography`): un nivel por valor observado en la unión de referencia y actual.
  - **Probabilidad predicha:** deciles de la distribución de **validación sin remuestrear** (S0). No se usa entrenamiento porque el Random Forest predice sobre sus propias filas de entrenamiento con probabilidades más extremas que sobre filas no vistas; eso produciría una alarma espuria. Por construcción, el PSI de la probabilidad en S0 es 0.
- **Pruebas de apoyo:** KS de dos muestras (numéricas continuas) o chi² de homogeneidad (discretas), referencia frente a actual, con corrección de Holm sobre las 8 variables de cada escenario (α = 0,05). Solo como apoyo: con 6.000 + 2.000 filas detectan diferencias pequeñas y el remuestreo con reemplazo repite filas.
- **Sin etiquetas:** tasa de contacto (p > t\* = 1/6), probabilidad media y beneficio esperado total de los contactados.
- **Con etiquetas:** tasa de abandono observada, AP, Brier, **calibración global** (probabilidad media − tasa observada) y beneficio realizado del modelo frente a contactar a todos y a nadie (0 €).

### 4.5 Umbrales preregistrados

No se cambian después de ver resultados.

- PSI < 0,10 estable · 0,10–0,25 moderado · > 0,25 **alerta**.
- **Alarma del escenario:** alguna variable o la probabilidad con PSI > 0,25.
- **Degradación:** calibración global fuera de ±3 pp, o Brier > 1,15 × el Brier de S0.

### 4.6 Expectativas preregistradas

Se reportan como cumplidas o no cumplidas, sin ajustes posteriores.

- **E1** S0 sin alarma y sin degradación.
- **E2** S1–S3: alarma en la variable desplazada; calibración global dentro de ±3 pp (cambio de covariables con P(y|X) estable).
- **E3** S4: PSI de todas las variables por debajo de 0,25, pero calibración global fuera de ±3 pp → el monitoreo de entradas no basta; hacen falta etiquetas (retroalimentación).
- **E4** La tasa de contacto se aleja de S0 en S1–S4 (más de 2 pp) y sirve como señal sin etiquetas.

### 4.7 Notas a priori (escritas antes de ejecutar)

Estas notas se derivan solo de la definición de los escenarios y de las proporciones ya publicadas en el EDA, no de resultados de monitoreo:

1. **S3 puede no alcanzar la alarma.** Pasar de ~48 % a 70 % de inactivos da un PSI analítico de (0,70 − 0,48)·ln(0,70/0,48) + (0,30 − 0,52)·ln(0,30/0,52) ≈ 0,20: moderado, no alerta. Si se confirma, E2 no se cumple para S3. Se reporta como límite del umbral de 0,25 en variables binarias, sin modificar el escenario.
2. **S2 queda cerca del umbral:** Alemania del ~25 % al ~50 % da un PSI analítico ≈ 0,27.
3. **El Brier depende de la mezcla de clientes.** En S2–S4 aumenta la proporción de casos con más abandono, y el Brier puede subir sin que el modelo empeore. El criterio de degradación se aplica tal como está preregistrado y esta salvedad se reporta junto al resultado.
4. **En S4 también cambian las variables.** P(X|y) difiere entre clases (quienes abandonan son mayores, más alemanes y más inactivos), así que el PSI de `Age` o de la probabilidad puede subir. E3 se juzga con el umbral, sin reinterpretarlo.

### 4.8 Salidas

- `src/churn/monitoring.py`: `psi()`, construcción de escenarios, `evaluate_scenario()`, `run_monitoring()`.
- CLI `churn-monitor` → `reports/monitoring.json`, `reports/monitoring.md` y `reports/figures/monitoring_psi.png` (< 500 KB). Requiere el CSV local y el modelo verificado por hash; CI ejecuta solo tests sintéticos.
- Tests: PSI = 0 con distribuciones idénticas; PSI conocido calculado a mano; bins sin observaciones (ε); escenarios deterministas con la semilla; S4 con 35 % exacto; S2 y S3 con la proporción objetivo; el módulo no lee la partición de prueba.

### 4.9 Pestaña de monitoreo (opcional)

Si hay tiempo, `GET /monitoring` devuelve `reports/monitoring.json` (404 si no existe) y el dashboard añade una pestaña **Monitoreo** que lo muestra. El dashboard sigue sin leer archivos ni el modelo: todo pasa por la API (spec 005 §2). El archivo se copia en la imagen y en el Space.

## 5. README final y demo

- Inicio en inglés (6–10 líneas): problema, enfoque, resultado en dinero y enlaces **Live demo**, **API docs** y **Model card**; insignia de CI.
- Resultados de prueba (AP 0,705 · ROC-AUC 0,862 · Brier 0,1017 · 61.600 € frente a 22.100 €) con los supuestos económicos.
- Diagrama de arquitectura en Mermaid, decisiones técnicas, limitaciones y trabajo futuro.
- Las secciones semanales pasan a `docs/` (historial); el README queda legible en un minuto.
- `examples/clientes_ejemplo.csv`: 20 clientes **sintéticos**, generados con semilla por `scripts/make_example_csv.py` según los rangos del contrato. Nunca filas del CSV real. Un test comprueba que el archivo coincide con el generador y que cada fila pasa el contrato de la API.
- GIF de demo (responsable): 20–30 s y < 5 MB. Si supera 500 KB, se aloja como asset de un Release y se enlaza.

## 6. Cierre y reproducibilidad

- Verificación desde un **clon limpio** (no la carpeta de trabajo): `uv sync --locked --all-groups`, Ruff, formato, pre-commit y pytest con cobertura ≥ 85 %; `docker build` de la variante `release` y prueba del cliente de referencia.
- Búsquedas que deben salir vacías (los patrones usan `[-]`, `[/]` y `[:]` para no coincidir con este mismo texto):
  - rutas absolutas: `git grep -n -I -i -E "C[:]\\\\Users|[/]home[/]|[/]sessions[/]"`
  - secretos: `git grep -n -I -E "hf_[A-Za-z0-9]{20,}|nvapi[-]|sk[-]or[-]"`
  - datos reales: `git ls-files "*.csv"` solo devuelve `examples/clientes_ejemplo.csv` (sintético).
- Versión del paquete `1.0.0` en `pyproject.toml` y etiqueta de código `v1.0.0` (distinta de `model-v1.0`) con notas de versión. La etiqueta dispara también la sincronización con el Space.

## 7. Criterios de aceptación

Checklist histórico al 7 de octubre de 2026 (registro S12). Los requisitos
vigentes de cierre sobre Render se definen en §12–§14 y se siguen en registro
S23: el Space y la activación pública del LLM son alternativos, no prerrequisitos
de Render. Se conserva este checklist como evidencia de la planificación inicial.

- [ ] Spec 005 cerrada: Docker con el Release publicado y CI en verde. *Release y `verify-docker.ps1` sin `-LocalModel` verificados (S14); CI remoto de `3419a65` en verde. Pendiente: clon limpio.*
- [ ] El Space público responde y reproduce el cliente de referencia (0,947, contactar). *Pendiente: cuenta de Hugging Face (B-03) y workflow. En local, la API real y el dashboard (`AppTest`) dan 94,7 % y contactar.*
- [x] El Space no contiene datos reales, binarios, `models/` ni secretos: `tests/test_build_space.py` (lista exacta, rechazos, cabecera YAML, cada `COPY` presente); armado real con 41 archivos de texto (792 KB).
- [ ] LLM con límite por hora y respaldo de plantilla: implementado y probado (`tests/test_narrative.py`: límite, intentos fallidos, ventana deslizante, 0 y valores inválidos). *Falta configurar los secretos en el Space y ver `source="llm"` en la demo.*
- [x] Monitoreo: S0–S4 reportados con E1–E4 marcadas ([reporte](../reports/monitoring.md)). E1, E3 y E4 cumplidas; E2 no cumplida (S3: PSI 0,196, anticipado en §4.7).
- [ ] README final legible en ≤ 1 minuto, con demo, resultados y limitaciones. *Redactado; faltan el GIF y la URL pública activa (B-03).*
- [ ] Verificación desde clon limpio registrada (tests, lint y `docker build`). *Tests, Ruff, formato y hooks en verde en un clon limpio (Linux); `docker build` pendiente en el equipo del responsable.*
- [x] Búsquedas de rutas, secretos y datos reales vacías (tras quitar la ruta local de `docs/contexto-proyecto.md`).
- [ ] Etiqueta `v1.0.0` publicada y CI en verde en ese commit. *Pendiente del responsable.*
- [x] Registro S12 y `docs/contexto-proyecto.md` actualizados.

## 8. Fuera de alcance

Autenticación, escalado, reentrenamiento automático, monitoreo en producción real, monitoreo con etiquetas reales, opciones B y C de la spec 004 y mitigación de E-01.

## 9. Decisiones técnicas

| ID | Decisión | Justificación |
|---|---|---|
| D-17 | PSI + KS/chi² propios, sin Evidently (D1 = A) | Ligero, determinista y testeable, sin dependencia nueva. El PSI es el estándar de monitoreo en riesgo de crédito |
| D-18 | LLM activado con límite por hora y plantilla de respaldo (D2 = A) | Muestra la integración sin exponer la cuota sin control; el costo se acota también en el proveedor |
| D-19 | Dockerfile del Space derivado solo con la variante `release` | El contexto `localmodel` no existe en el Space; se evita depender de cómo el builder trate las etapas no usadas |
| D-20 | Referencia de la probabilidad = validación sin remuestrear | Las probabilidades del RF sobre su propio entrenamiento son más extremas: alarmarían sin cambio real |
| D-21 | Composición exacta en S2–S4 | La proporción objetivo se alcanza sin ruido de muestreo y los tests la pueden comprobar exactamente |
| D-22 | Space con API interna (127.0.0.1) y solo el dashboard público | Menor superficie expuesta; la documentación de la API se enlaza al repositorio |

## 10. Bloqueos y prerrequisitos

- **B-03 — Cuenta de Hugging Face pendiente.** El responsable aún no tiene cuenta (7 de octubre de 2026). Se usa `darwinjaco` como usuario provisional en el README y en esta spec. Si el usuario final es otro, se corrige en `README.md`, `deploy/space/README.md` y la variable `HF_SPACE`; el código no depende del nombre.
- Prerrequisitos del responsable (P1–P6 del plan): push y CI en verde, Release `model-v1.0` publicado con el repositorio público, `verify-docker.ps1` sin `-LocalModel`, cuenta y token de Hugging Face, secreto `HF_TOKEN` y variable `HF_SPACE` en GitHub, Space vacío creado y, si se usa, la clave del LLM.

## 11. Enmienda de seguridad — Spec 007

La [spec 007](007-security-hardening.md) sustituye §3 en la persistencia del
presupuesto LLM: mismo límite configurable, compartido por procesos mediante
SQLite en la misma instancia. También exige XSRF activo, autenticación Git sin
token en argumentos y referencias inmutables. Los disparadores de §2.4 siguen
vigentes. La preparación de Render se define en §12.

## 12. Enmienda v1.1 — Render gratuito

**Estado: diseño y plan versionados previamente en `40f913f`; configuración
validada y publicada en `193a13d`, con CI y Security scans remotos verdes (S17);
demo pública funcional verificada en S18, cierre de seguridad y evidencia del
build pendientes.** El responsable
autorizó continuar si la plataforma es gratuita y preparar los archivos tras
configurar su cuenta y formulario. Sus condiciones Free fueron verificadas.
Esta enmienda no declara el despliegue público realizado; conserva los criterios
históricos de Hugging Face en §7 como evidencia de la implementación original.

- Arquitectura propuesta: un Web Service Docker `plan: free`, `ROLE=all`,
  Streamlit público en `PORT=10000` y FastAPI interna en `127.0.0.1:8000`.
  Se conserva el Dockerfile y el modelo del Release ya verificados.
- Presupuesto: 512 MB, 0,1 CPU y 750 horas mensuales compartidas por workspace;
  no crear dos servicios ni ningún recurso de pago como alternativa automática.
- LLM inicialmente desactivado (`LLM_MAX_CALLS_PER_HOUR=0`): el filesystem de
  Free es efímero. Su activación posterior exige presupuesto gratuito comprobado
  y una solución de cuota adecuada a la plataforma, con decisión del responsable.
- XSRF y CORS activos; acceso directo HTTPS sin iframe de otra plataforma.
  Publicación manual únicamente tras CI verde. URL y pruebas reales pendientes.
- `render.yaml` reproduce el diseño versionado: una instancia Free, región
  Virginia seleccionada por el responsable, Dockerfile de la raíz, health
  `/_stcore/health` y `autoDeployTrigger: 'off'`. No fija rama: el Blueprint usa
  su propia rama. En el formulario manual, elegir `docs/pre-production-review`
  mientras las correcciones no estén fusionadas y comprobar el CI del commit.
- `STREAMLIT_BROWSER_SERVER_ADDRESS` referencia `RENDER_EXTERNAL_HOSTNAME`
  del mismo servicio en el Blueprint. En creación manual se establece cuando
  Render asigne el dominio: solo el hostname, sin `https://` ni rutas; no usar
  un valor vacío ni la cadena literal `${RENDER_EXTERNAL_HOSTNAME}`.
- Se conserva el workflow de Hugging Face existente. La retirada de sus
  disparadores por etiqueta requiere una enmienda propia antes de publicar
  `v1.0.0`. El stash anterior se mantiene preservado.
- Plan y configuración: [plan-render-gratuito.md](../docs/plan-render-gratuito.md)
  y [render.yaml](../render.yaml).

### 12.1 Criterios de aceptación de Render

- [x] Configuración validada contra el esquema oficial, versionada y publicada
  en un commit con CI y Security scans satisfactorios. *Comprobaciones locales
  satisfactorias (S17), commit `193a13d` publicado y ambos workflows verdes.*
- [x] Un único Web Service Free desplegado; modelo descargado del Release y
  comprobado por SHA-256 durante el build. Registrar commit, URL y build.
  *Entrega v1.0.1: servicio existente en main/9384e51, deploy Live aportado por
  el responsable, duración indicada 2m14s; build/arranque con verificación obligatoria
  de hash y referencia comprobada. Evidencia en Release e informe final.*
- [x] `/_stcore/health` responde `ok`; Cliente reproduce 0,947 y contactar;
  Lote procesa `examples/clientes_ejemplo.csv`; Modelo y Monitoreo muestran
  los reportes congelados. Comprobar XSRF, WebSocket y errores bajo HTTPS con
  el procedimiento de seguridad pública de la spec 007. *Funcionalidad,
  subida/XSRF y orígenes inicialmente comprobados en S18; cierre de cabeceras,
  framing y navegador final comprobados en v1.0.1.*
- [x] LLM desactivado y plantilla disponible, sin claves de proveedor.
  *Configuración Free con límite 0 y plantilla comprobada en HTTPS.*
- [x] URL real y resultados públicos registrados en README y registro.
  *S18: https://bank-churn-ml-ufa7.onrender.com/, auditoría HTTP fallida y
  verificación funcional en navegador satisfactoria, documentadas por separado.*

S23 acredita GIF y verificación Docker desde clon limpio; la etiqueta de código
`v1.0.0` existe, pero la Release final autorizada es `v1.0.1` (§14), condicionada
a CI y despliegue final. La partición de prueba no se vuelve a cargar.

## 13. Enmienda v1.2 — Cierre sobre Render

El responsable autoriza avanzar con el cierre; Render sigue siendo la plataforma
principal y mantiene un único servicio Free con LLM desactivado. Antes de tocar
el workflow o el arranque se versiona el [plan de cierre](../docs/plan-cierre-release.md).

- Hugging Face se conserva como alternativa **manual**: `deploy-space.yml` queda
  únicamente con `workflow_dispatch`; se retira `push.tags: ["v*"]`. La etiqueta
  de código `v1.0.0` no debe iniciar un despliegue alternativo sin cuenta/token.
- El contenido del Space incluye `dashboard/serve.py` y el middleware de la spec
  007 v1.2 mediante los globs existentes; se adapta la prueba de lista exacta.
- Capturar y crear un recorrido GIF de 20–30 s a partir de las cuatro vistas
  comprobadas con perfiles sintéticos. Si pesa <500 KiB se versiona como
  `docs/demo.gif`; en otro caso se publica como asset del Release. Describirlo
  como recorrido animado, no como una grabación de campaña o de datos reales.
- Antes del cierre: clon limpio del commit publicado, lock/herramientas/tests,
  build de variante Release y prueba de una sola imagen `ROLE=all` bajo 512 MiB
  y 0,1 CPU, con hash y cliente de referencia congelados. No se reentrena ni se
  vuelve a evaluar prueba.
- La etiqueta/Release final requiere la demo final comprobada y CI verde en su
  commit. Si el redeploy de Render necesita al responsable, se registra ese
  bloqueo y se pospone la etiqueta, sin declarar el cierre completo.

## 14. Enmienda v1.3 — Limpieza y entrega consolidada

El responsable autoriza el 14 de octubre de 2026 un único commit al finalizar
las tareas y la integración de las ramas sin conflictos y con las comprobaciones
satisfactorias. Mantiene Hugging Face como alternativa manual. Esta enmienda es
documental: no cambia código, tests, dependencias, modelo ni protocolo estadístico.

- Conservar especificaciones, planes, reportes y tracking; retirar únicamente
  el marcador de notebook redundante y cachés/temporales propios regenerables.
- Actualizar los estados vigentes sin reescribir resultados históricos. Registrar
  por separado evidencia local, CI remoto y despliegue real.
- `v1.0.0` existe en `bacb47b`, pero se publicó antes del cierre HTTPS final;
  no equivale a una Release de código publicada. El responsable autoriza
  **`v1.0.1`** como etiqueta/Release de la entrega final, sin mover la anterior.
  El paquete sigue en 1.0.0 y el modelo permanece en `model-v1.0`.
- La integración usa avances rápidos si la relación de ancestros y las revisiones
  lo permiten. No se fuerzan ramas. CI del commit final, deploy e identificación
  del build se registran en las notas de la Release y en el informe de entrega.
- Se mantienen los requisitos de §13: demo comprobada, GIF, reproducibilidad,
  un único servicio Free, LLM desactivado y evaluación final no repetida.
- Reanudación: el responsable autoriza **«Integrar GitHub primero»** después de
  verificar que la URL todavía sirve la interfaz anterior. Commit e integración
  pueden preceder al redeploy; la etiqueta/Release de `v1.0.1` sigue esperando
  CI del commit y comprobación HTTPS/funcional pública. Las evidencias posteriores
  al snapshot se enlazan en los PR y notas de Release sin un segundo commit.

Plan operativo: [plan-cierre-release.md §6](../docs/plan-cierre-release.md#6-cierre-consolidado-autorizado--14-de-octubre-de-2026).

## 15. Enmienda v1.4 — Memoria técnica LaTeX

El responsable solicita revisar la higiene de Git y generar documentación
detallada en LaTeX de la entrega ya publicada. Alcance exclusivamente documental:
no cambia implementación, tests, dependencias, modelo ni resultados congelados.

- Documento principal `docs/latex/memoria-tecnica.tex`, en español, con portada,
  resumen, índice, metodología, contrato, H1–H6, selección, E-01–E-04, calibración,
  economía, evaluación final, arquitectura, API, dashboard, seguridad, monitoreo,
  reproducibilidad, operación, limitaciones y referencias.
- Toda cifra procede de reportes versionados o de la evidencia publicada en
  `v1.0.1`; se distinguen desarrollo, prueba única y comprobaciones de despliegue.
  No se ejecuta ningún entrenamiento ni se vuelve a cargar prueba para redactar.
- Reutilizar figuras versionadas por ruta relativa. Sin copiar datasets, modelo,
  secretos ni identificadores de clientes en la memoria.
- Instrucciones en `docs/latex/README.md`. Compilar a `docs/latex/build/`, excluido
  de Git: el PDF es un entregable local regenerable, no un auxiliar versionado.
  El compilador es externo a `pyproject.toml`/`uv.lock`.
- Actualizar estados documentales que aún reflejan el snapshot anterior al
  cierre; conservar secciones históricas y enlazar la Release como evidencia.
- Aceptación: fuente compilable con rutas resueltas, PDF con índice y referencias,
  sin errores LaTeX ni referencias indefinidas; hooks pertinentes y Git sin
  archivos generados propuestos para versionar. Registrar comandos y límites en S25.
