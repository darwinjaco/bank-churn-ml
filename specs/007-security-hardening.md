# Especificación 007 — Correcciones de seguridad de la demo

| Campo | Valor |
|---|---|
| Versión | v1.0 |
| Estado | Aprobada por el responsable; implementación pendiente del commit de compuerta |
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
