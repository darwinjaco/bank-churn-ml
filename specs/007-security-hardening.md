# Especificación 007 — Correcciones de seguridad de la demo

| Campo | Valor |
|---|---|
| Versión | v1.1 — escaneos CI y verificación pública (§9) |
| Estado | v1.0 publicada en `3419a65`, CI verde; v1.1 implementada y comprobada en local, CI nuevo y verificación pública pendientes |
| Base | `a2598ee`, CI remoto en verde |
| Dependencias | Specs 002, 005 y 006; auditoría SEC-01 a SEC-13 |

## 1. Alcance e invariantes

Corregir los hallazgos de la auditoría con cambios compatibles con la demo.
El responsable aprobó aparcar las siete rutas de preparación para Render en
`git stash push -u -m "render-prep" -- <rutas>` y versionar esta especificación
y su plan antes de modificar código. Render no forma parte de esta corrección.

No cambiar dependencias Python, artefacto, variables, calibrador, umbral,
supuestos económicos ni métricas. No ejecutar entrenamiento, auditoría real,
MLflow ni la evaluación final real. Los tests de esas rutas usan datos sintéticos.
`Gender` sigue siendo exclusivamente una variable de auditoría.

## 2. CSV y minimización (SEC-01, SEC-04, SEC-05)

- Subida máxima: **1 MiB**, tanto en Streamlit como en el lector del dashboard.
- El lector consume como máximo el límite más un byte antes de rechazar. Lee
  como máximo 1.001 filas; más de 1.000 se rechazan. Cabeceras duplicadas se
  rechazan; solo las ocho columnas del contrato se materializan con pandas.
- El CSV original puede contener columnas extra, pero se descartan antes de
  mostrar o exportar resultados: nunca se exportan identificadores, apellidos,
  `Gender`, salario ni texto adicional. La tabla y la descarga se construyen con
  entradas normalizadas y salidas del modelo.
- La serialización CSV entrecomilla campos y neutraliza texto cuyo inicio,
  incluidos espacios o controles, pueda interpretarse como fórmula (`= + - @`,
  variantes de ancho completo). Los números negativos siguen siendo números.
- Los reportes locales SHAP usan únicamente el nombre del caso. Eliminar los
  tres identificadores del JSON y del Markdown existentes sin recalcular SHAP
  ni tocar métricas. El generador deja de publicar identificadores.
- Esta minimización no borra el historial Git; no reescribirlo. Registrar el
  límite: los identificadores anteriores pertenecen al dataset público.

## 3. Artefacto y errores (SEC-02, SEC-12)

- API, build, monitoreo, auditoría y evaluación final usan la misma carga de
  `artifact.py`, que comprueba el SHA-256 fijo antes de `joblib.load`.
- Las CLI de auditoría y evaluación final requieren el archivo local existente;
  no descargan silenciosamente. Con hash incorrecto, no deserializar ni leer datos.
- Los errores 422 publican únicamente ubicación, tipo y mensaje. No incluir
  `input`, `ctx`, valores rechazados ni URLs de documentación con datos añadidos.
  Las columnas extra se describen genéricamente en la ubicación.
- La CLI de validación informa del número de fallos sin imprimir sus valores.
- Las respuestas de API llevan `Cache-Control: no-store`,
  `X-Content-Type-Options: nosniff` y `Referrer-Policy: no-referrer`.

## 4. Consumo aprobado (SEC-03, SEC-04)

| Control | Valor |
|---|---|
| Inferencia | 60 intentos/minuto, ventana deslizante global del proceso |
| Concurrencia | 2 peticiones de inferencia simultáneas |
| Cuerpo de petición | 512 KiB, contando bytes recibidos incluso sin `Content-Length` |
| CSV | 1 MiB; hasta 1.000 clientes |
| LLM | 30 intentos/hora por defecto; `LLM_MAX_CALLS_PER_HOUR` conserva su configuración |

- Aplicar frecuencia y concurrencia a POST `/predict`, `/predict/batch` y
  `/explain` antes de inferencia. Un rechazo devuelve 429 y `Retry-After`.
  `/health`, `/model`, `/monitoring` y la documentación siguen disponibles.
- Un cuerpo demasiado grande devuelve 413 antes de analizar JSON. La limitación
  cuenta bytes reales y no confía exclusivamente en la cabecera del cliente.
- La imagen arranca Uvicorn con **un worker**. El presupuesto API es compartido
  por todos los visitantes de ese proceso; no confiar en `X-Forwarded-For`.
- El presupuesto LLM usa SQLite de la biblioteca estándar: archivo privado en
  un directorio de estado, configurable mediante `LLM_RATE_LIMIT_DB`; transacción
  `BEGIN IMMEDIATE`, purga de intentos expirados y reserva antes de la llamada.
  Cuenta fallos, persiste reinicios del proceso y se comparte entre procesos que
  usan el mismo archivo. El reloj persistido es tiempo Unix; solo se guardan
  marcas temporales, nunca datos de cliente ni credenciales.
- Límite 0: no llamar al LLM ni crear su base. Si el presupuesto no puede
  comprobarse, usar la plantilla: no efectuar llamadas sin límite.
- No garantiza cuotas entre hosts ni tras pérdida del volumen; documentar la
  necesidad de un control de plataforma para réplicas. No añadir Redis.

## 5. Navegador y red (SEC-06, SEC-07, SEC-09)

- Mostrar respuesta del LLM con `st.text`, sin interpretar Markdown ni HTML.
- Mantener CORS y XSRF de Streamlit activos. Por defecto, cookie SameSite `lax`.
  Para iframe HTTPS, permitir configurar `STREAMLIT_SERVER_XSRF_COOKIE_SAME_SITE=none`
  junto con la lista de orígenes CORS y el dominio público; no desactivar XSRF.
- Ocultar trazas no controladas en el navegador (`client.showErrorDetails=none`).
- Compose publica API y dashboard solo en `127.0.0.1`; la comunicación entre
  contenedores continúa por `http://api:8000`. `ROLE=all` mantiene API interna.
- La validación real de iframe, TLS y cabeceras del proxy queda pendiente hasta
  disponer del despliegue público; no presentarla como realizada.

## 6. Configuración y cadena de suministro (SEC-08, SEC-10, SEC-11, SEC-13)

- Fijar imágenes por digest multi-arquitectura verificado y Actions/hooks por
  SHA del repositorio oficial, conservando las versiones actuales.
- CI: `permissions: contents: read`; checkout sin credenciales persistidas.
- La sincronización del Space conserva sus disparadores vigentes. La URL de
  push no contiene token; usar un helper temporal de credenciales que obtiene
  el token del entorno y restringe host/ruta. Sin imprimirlo ni guardar su valor.
- Ignorar `.env*`, manteniendo únicamente `.env.example` como plantilla.
- Mantener usuario no root y la verificación SHA-256 del modelo en ambas
  variantes Docker. No reducir ni mover dependencias durante esta corrección.

## 7. Aceptación y evidencia

- Tests de fórmula y descarte de columnas; CSV grande y cabeceras duplicadas.
- Artefacto alterado rechazado antes de deserializar; ambas CLI delegan en la
  carga verificada. La protección de evaluación final sigue funcionando.
- Cuerpo demasiado grande, incluido fragmentado; límite y liberación de
  concurrencia; ventana de frecuencia; respuestas válidas sin cambios numéricos.
- Cuota LLM compartida entre conexiones, persistida y atómica bajo concurrencia;
  no crear estado con límite 0; fallo del almacenamiento produce plantilla.
- Ausencia de `input`, `ctx` y valores sensibles en 422 y logs de validación.
- Reportes sin identificadores y con métricas originales conservadas.
- Comprobaciones exactas de `AGENTS.md` §4, cobertura ≥ 85 %, Docker/configuración
  cuando sea posible y registro actualizado. Distinguir CI previo de verificación
  local nueva. No despliegue ni reescritura del historial.

## 8. Fuentes consultadas

- [OWASP: CSV Injection](https://owasp.org/www-community/attacks/CSV_Injection).
- [scikit-learn: persistencia](https://scikit-learn.org/stable/model_persistence.html).
- [Streamlit: texto literal](https://docs.streamlit.io/develop/api-reference/text/st.text).
- [Streamlit: configuración](https://docs.streamlit.io/develop/api-reference/configuration/config.toml).
- [Python 3.11: SQLite](https://docs.python.org/3.11/library/sqlite3.html).
- [GitHub Actions: seguridad](https://docs.github.com/en/actions/reference/security/secure-use).

## 9. Enmienda v1.1 — Escaneos y verificación pública

Estado: compuerta `40127be` versionada; implementación comprobada en local.
El workflow nuevo no está publicado y no hay URL pública para comprobar Render.
Responsable autorizó añadir escaneos CI y comprobar HTTPS, cookies y orígenes.

### 9.1. Escaneos CI

- Workflow de seguridad separado, sin alterar el job de calidad existente,
  ejecutado en pull requests, push a `main` y manualmente.
- Herramientas externas al entorno de entrenamiento: `pip-audit==2.10.1` en
  entorno aislado de uv y Gitleaks v8.30.1 con distribución oficial verificada
  por SHA-256. Actions por SHA; `permissions: contents: read` y checkout sin
  credenciales persistidas. No usar secretos del repositorio en los jobs.
- Exportar temporalmente los requisitos completos de `uv.lock` con
  `uv export --locked --all-groups --no-emit-project`, conservando hashes.
  Auditar sin resolver ni instalar las dependencias del proyecto, con
  `--require-hashes --disable-pip --strict` (`--require-hashes` evita resolución;
  `--no-deps` es redundante según la herramienta); sin `--fix` ni actualizaciones.
  La cobertura de versiones corresponde al Python/plataforma del runner.
- Escanear todo el historial disponible con checkout completo y Gitleaks
  `git --log-opts=--all --redact=100`. No escanear `.venv`, datos o tracking
  locales mediante este job; no son contenido versionado del checkout.
- Hallazgos o errores de ejecución fallan el job: no convertir un escaneo
  incompleto en verde ni usar `continue-on-error`. Cualquier excepción a un
  hallazgo requiere evidencia, motivo y decisión versionada del responsable.
- Artifacts con retención de 7 días. El informe de secretos contiene únicamente
  regla, ruta, línea y commit: no texto fuente, valores, autor ni mensaje del
  commit. No publicar informes crudos aunque el escáner use redacción.
- No editar `pyproject.toml`, `uv.lock`, modelo ni resultados para remediar
  hallazgos sin la enmienda específica correspondiente.

### 9.2. Verificación pública

- Preparar una comprobación manual para una URL HTTPS explícita del responsable;
  sin URL pública, registrar «no verificado» y no atribuir resultado a Render.
- Comprobar certificado TLS con verificación estándar y redirección HTTP a
  HTTPS. No desactivar TLS ni enviar claves, credenciales o datos de clientes.
- Revisar cabeceras efectivas en el dashboard público: `nosniff`, política de
  referencia, HSTS y controles de framing/CSP cuando estén presentes. Informar
  ausencia o conflicto; no afirmar que las cabeceras de la API interna protegen
  automáticamente las respuestas de Streamlit o del proxy.
- Observar atributos de cookies sin imprimir valores. Para XSRF: SameSite
  válido; `SameSite=None` exige `Secure`; no exigir `HttpOnly` al token que debe
  leer el frontend. Una cookie no observada es evidencia incompleta.
- Confirmar rechazo del handshake WebSocket con origen no autorizado, sin enviar
  mensajes de aplicación, archivos ni peticiones de inferencia. El rechazo de
  origen es distinto de comprobar el token XSRF de una subida.
- Los controles de iframe/subida requieren un navegador y despliegue real; las
  pruebas con respuestas sintéticas no se presentan como validación pública.
- No cambiar autenticación, cookies, TLS o proxy por resultados hipotéticos.
  Primero registrar la evidencia de la URL real y aprobar la solución necesaria.

### 9.3. Aceptación

- Escaneos reales ejecutados con versión fija; errores y hallazgos registrados
  separadamente de resultados satisfactorios y sin revelar secretos.
- Tests sintéticos de minimización del informe, códigos de salida y evaluación
  de cabeceras/cookies, si se añaden helpers de implementación.
- Regresión del dashboard con plazo explícito de 30 s en `AppTest`; conservar
  todas las aserciones y la restauración de `__main__`. Los 3 s por defecto de
  la herramienta no son un SLA de la aplicación y agotan el plazo en Windows
  bajo cobertura. Aplicar este ajuste solo después de versionar la compuerta.
- Comprobaciones locales de AGENTS §4 en verde; CI nuevo solo se acredita tras
  publicar y consultar su ejecución. Revisión pública pendiente si no hay URL.

### 9.4. Fuentes consultadas para esta enmienda

- [pip-audit: usos, formatos y exit codes](https://github.com/pypa/pip-audit).
- [Gitleaks: redacción e historial](https://github.com/gitleaks/gitleaks).
- [uv: exportación de lockfiles](https://docs.astral.sh/uv/concepts/projects/export/).
- [Render: TLS y redirección](https://render.com/docs/tls).
- [Streamlit: configuración de cookies y orígenes](https://docs.streamlit.io/develop/api-reference/configuration/config.toml).
