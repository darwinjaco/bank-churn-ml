# Especificación 005 — API y dashboard

| Campo | Valor |
|---|---|
| Estado | Base v1.2 publicada; v1.3 implementada y verificada en local en `feat/dashboard-redesign` (S20), vista previa disponible; publicación y build Docker nuevos pendientes |
| Responsable | Darwin Jacome Cuenca |
| Semana | 7 (16–22 de noviembre de 2026) |
| Dependencias | [002](002-modeling-and-evaluation.md) (artefacto congelado), [004](004-decision-layer.md) (regla de decisión) |

## 1. Objetivo

Servir el modelo congelado como una API y un dashboard reproducibles con un solo comando, sin reentrenar y sin el CSV, para que cualquier persona pueda probar la decisión de retención.

## 2. Arquitectura

```text
Navegador ──▶ Streamlit (dashboard) ──HTTP──▶ FastAPI ──▶ CalibratedModel + SHAP
                                                   └──▶ (opcional) LLM compatible con OpenAI
```

- El dashboard **no carga el modelo**: toda predicción pasa por la API.
- Local: `docker compose up` levanta dos servicios (`api`, `dashboard`).
- Hugging Face Spaces (semana 8): una sola imagen que arranca ambos procesos; el dashboard escucha en el puerto público 7860 y la API en `localhost:8000`.

## 3. Distribución del modelo

- El artefacto `model.joblib` se publica como asset de un **GitHub Release** (`model-v1.0`) del repositorio.
- `artifact.py` fija la URL y el SHA-256 esperado (`579b7fe3…095a`). `ensure_model()` descarga el archivo si falta y **falla si el hash no coincide**; la API verifica el hash otra vez al arrancar.
- La metadata se lee de `reports/model_metadata.json` (versionada). El CSV nunca entra en la imagen.

## 4. Endpoints

| Método y ruta | Entrada | Salida |
|---|---|---|
| `GET /health` | — | `status`, SHA-256 del artefacto, commit del modelo |
| `GET /model` | — | Variables, calibrador, umbral, supuestos y métricas de la evaluación final |
| `POST /predict` | Un cliente | `churn_probability` (calibrada), `contact` (bool), `expected_benefit_eur`, `threshold`, `top_reasons` (3 contribuciones SHAP con signo) |
| `POST /predict/batch` | Lista de 1 a 1.000 clientes | Lista de predicciones (sin razones) y resumen: contactados y beneficio esperado total |
| `POST /explain` | Un cliente | Texto breve en español con la recomendación y sus razones; `source` = `llm` o `template` |
| `GET /monitoring` | — | Reporte del monitoreo simulado (spec 006 §4.9); 404 si no existe (v1.1) |

## 5. Contrato de entrada (Pydantic)

Mismos rangos que el contrato de datos (spec 001): `CreditScore` 300–900, `Age` 18–100, `Tenure` 0–10, `Balance` ≥ 0, `NumOfProducts` 1–4, `HasCrCard` y `IsActiveMember` ∈ {0, 1}, `Geography` ∈ {France, Germany, Spain}. `EstimatedSalary` es opcional y se ignora (excluida por E-03). **Campos extra prohibidos**: un `Gender` o un identificador devuelve 422. Los números no finitos (NaN, ±infinito) también devuelven 422 (v1.1).

## 6. Reglas

- Umbral, supuestos y calibrador salen de la metadata, no se escriben en la API.
- El modelo y el explicador SHAP se cargan una vez al arrancar.
- Las razones SHAP explican la probabilidad sin calibrar (spec 002 §11.1); se presentan como factores del modelo, no como causas.
- **LLM opcional** (`/explain`): cliente compatible con OpenAI configurado por `LLM_BASE_URL`, `LLM_API_KEY` y `LLM_MODEL` (por ejemplo, NVIDIA NIM u OpenRouter). Solo recibe las variables del cliente, la probabilidad, la decisión y las razones SHAP: nunca identificadores. Sin clave, con error o con tiempo de espera superado (10 s), se usa una plantilla determinista. La clave vive solo en variables de entorno o secretos del Space, nunca en el repositorio.
- Sin autenticación: es una demo de portafolio (limitación documentada). El LLM tiene límite de llamadas por hora desde la spec 006 §3.

## 7. Dashboard

1. **Cliente individual:** formulario → probabilidad, decisión, beneficio esperado, razones y explicación textual.
2. **Lote:** subir un CSV con las columnas del contrato → tabla con decisiones y resumen (contactados, beneficio esperado), descargable.
3. **Modelo:** métricas de la evaluación final, supuestos y enlace a la ficha del modelo.

## 8. Tests

- `TestClient`: `/health`, `/model`, `/predict` con la misma probabilidad que el artefacto, 422 por rango inválido, categoría desconocida y campo `Gender`, lote vacío o con más de 1.000 filas.
- `artifact.py`: descarga simulada, hash correcto e incorrecto.
- LLM: cliente simulado; sin clave → plantilla; error → plantilla; nunca se envían identificadores.
- Dashboard: funciones de formato puras con tests; la interfaz se prueba manualmente.
- Docker: `docker compose up` desde cero y una petición real a `/predict` (verificación manual registrada).

## 9. Criterios de aceptación

- [ ] `docker compose up` levanta API y dashboard desde un clon limpio (con el Release publicado).
  - Verificado en Docker Desktop con el Release publicado: `pwsh -File scripts/verify-docker.ps1` termina en «VERIFICACIÓN COMPLETA» (registro S14). Falta registrar el procedimiento desde un clon limpio.
- [x] `/predict` devuelve la misma probabilidad que `models/model.joblib` para el mismo cliente.
- [x] Hash del artefacto verificado en build y al arrancar (build real y descarga del Release verificados, S14).
- [x] Sin clave de LLM, `/explain` responde con la plantilla.
- [x] CI en verde con cobertura ≥ 85 % (CI remoto en `fd78f59`; local: 243 tests, 98,25 %).

## 10. Enmienda v1.1 (7 de octubre de 2026, semana 8)

Motivo: revisión completa del código antes del cierre (registro S12). No cambia el modelo, el umbral ni los supuestos; los criterios de §9 se mantienen.

- **Contrato:** `allow_inf_nan=False` y manejador de errores de validación que serializa NaN e infinitos como texto. Antes, un `Balance` o `EstimatedSalary` NaN o infinito devolvía **500**: la validación lo rechazaba, pero FastAPI no podía serializar el error. Ahora devuelve 422, también en el lote.
- **§6 cumplida literalmente:** el explicador SHAP se crea una vez por proceso, al arrancar (antes se creaba en cada petición; ~0,02 s, sin cambio en los resultados).
- **`GET /monitoring`** y pestaña **Monitoreo** del dashboard (spec 006 §4.9).
- **Dashboard:** un cliente HTTP por proceso (`st.cache_resource`); los errores 422 de la API se muestran por fila en lugar de una traza; el lote rechaza celdas vacías y decimales en columnas enteras antes de enviar (antes `Age = 52.7` se truncaba a 52 sin aviso).
- **`scripts/verify-docker.ps1`:** cada comprobación es una aserción (SHA-256 servido, probabilidad 0,947 y contactar para el cliente de referencia, 422 con `Gender`, `/explain` y `/monitoring`) y se añade la imagen del Space (Dockerfile derivado, `ROLE=all`, puerto 7860, API interna).

## 11. Enmienda v1.2 — Seguridad (spec 007)

El responsable aprobó la [spec 007](007-security-hardening.md) y su perfil de
límites. Esta enmienda sustituye la exportación de todas las columnas del CSV
por las ocho entradas del contrato y los resultados, redacta los errores 422
y añade controles de tamaño, frecuencia y concurrencia. El LLM se muestra como
texto literal. Modelo, calibración, umbral y respuestas válidas de inferencia
conservan sus valores. Compuerta versionada en `6343526`; controles implementados
y comprobados según S14. Código publicado en `3419a65`, con CI remoto en verde;
verificación formal desde clon limpio pendiente.

## 12. Enmienda v1.3 — Presentación profesional y gráficos

**Motivo:** el responsable pide recuperar una presentación Streamlit atractiva,
ordenada y gráfica, con lenguaje de herramienta bancaria. Autoriza construirla
en `feat/dashboard-redesign` y ver una previsualización local antes de decidir
su publicación. Plan: [plan-dashboard-redesign.md](../docs/plan-dashboard-redesign.md).

### 12.1 Diseño y navegación

- Título «Retención bancaria», subtítulo orientado a priorizar acciones mediante
  riesgo y beneficio esperado. El contexto del dataset y los supuestos pasa a
  «Metodología y supuestos»; no se presentan datos sintéticos como una campaña real.
- Tema claro nativo, sin HTML inseguro ni selectores CSS internos: azul
  `#1D4ED8`, tinta `#14243B`, fondo `#F5F7FB`, superficie `#FFFFFF`, verde azulado
  `#0F766E` y ámbar `#B45309`. Tipografía sans serif, números legibles, espacios
  consistentes, títulos alineados a la izquierda y bordes discretos.
- Navegación lateral: Cliente, Lote, Modelo y Monitoreo. Solo se ejecuta el
  contenido de la vista activa. Cliente es la entrada, con formulario compacto,
  ejemplo explícito y panel de resultados; no se infiere automáticamente.
- Controles nativos con etiquetas y ayudas en español, unidades y estados
  vacíos/carga/error con siguiente acción. Saldo ≥ 0 sin el máximo visual de
  300.000 €: se alinea con el contrato existente, sin cambiar la API.
- Las referencias técnicas se conservan en ayudas/tablas de detalle. Los
  colores se acompañan siempre de valores, texto o tablas. No se usan gauges
  decorativos, animaciones autónomas ni nuevas librerías.

### 12.2 Gráficos y fuentes exactas

Todos los datos se reciben desde la API; Streamlit no abre reportes ni el modelo.
`src/churn/presentation.py` prepara registros/especificaciones Vega-Lite pequeños
y números localizados; no importa Streamlit ni aprende parámetros.

| Vista | Gráfico | Fuente y significado |
|---|---|---|
| Cliente | Probabilidad y umbral en escala 0–100 % | `prediction.churn_probability` calibrada y umbral de metadata; contactar solo si p > t |
| Cliente | Barras de las tres razones SHAP con signo | `top_reasons`, contribución ×100 en pp de probabilidad **sin calibrar**; no waterfall completo, no causas ni suma al porcentaje calibrado |
| Lote | Histograma de probabilidades | Predicciones del lote, diez intervalos fijos de 0,1; p=1 incluido en el último, recuentos conservados; línea de umbral exacta |
| Lote | Recuento de decisiones | `contact` devuelto por la API; no recalcular con probabilidades redondeadas |
| Modelo | Beneficio por política | Reporte final ya congelado, modelo/todos/nadie; euros bajo los supuestos, no ingresos de una campaña real |
| Monitoreo | PSI por variable del escenario seleccionado | `monitoring.json` servido por la API; límites 0,10 y 0,25 del reporte, sin modificar umbrales |
| Monitoreo | Desviación de calibración por escenario | `calibration_gap` ×100 en pp y banda ±tolerancia del reporte; simulación sobre validación, no prueba nueva |

`GET /model` añade de forma compatible `final_test.evaluated_on` y
`final_test.policies` para `model`, `everyone` y `nobody`, únicamente
`contacted` y `benefit_eur` de los agregados existentes. Conserva las claves
previas y no expone datos por cliente. Si el reporte no contiene una política,
no se inventa: se muestra la evidencia disponible con estado informativo.

### 12.3 Estado, privacidad y rendimiento

- Resultados individuales y de lote en `st.session_state`, exclusivamente por
  sesión. Cada resultado individual conserva el perfil evaluado; su panel lo
  identifica y no afirma corresponder a campos editados sin enviar.
- Lote: carga y validación local acotada → botón explícito «Procesar lote» →
  resultado. Se conserva solo el contrato normalizado y las salidas; se descartan
  extras antes de calcular identidad/guardar. Un nuevo contenido normalizado
  invalida el resultado anterior. Filtrar, navegar y descargar no reenvían la
  inferencia. No hay caché global de clientes ni CSV originales en disco.
- Descarga de ejemplo generada en memoria con el generador sintético existente;
  no se copian datasets ni CSV al Space. Exportación de resultados conserva
  minimización, formatos y protección de fórmulas de v1.2.
- Metadata y reporte público se reutilizan por sesión, con reintento explícito
  ante error. El cliente HTTP compartido sigue siendo el único recurso global.
- `.streamlit/config.toml` contiene exclusivamente el tema y se copia en Docker
  y en el armado del Space. El builder mantiene sus rechazos de CSV, binarios y
  secretos. Se admiten sus cambios y tests en esta misma compuerta.
- Sin cambios en dependencias, features, modelo, calibrador, umbral, supuestos,
  reportes o cargadores. `Gender` no aparece en controles predictivos ni gráficos
  de inferencia. No se carga de nuevo la partición de prueba.

### 12.4 Aceptación del rediseño

- [x] Especificación y plan con commit previo a código/tests; trabajo en rama aislada.
  *Compuerta `ca498f2`, desde la base `d9b0f85` con CI verde.*
- [x] Cuatro vistas, tema aplicado, contexto metodológico accesible y gráficos
  acompañados por números/tablas sin afirmaciones causales incorrectas.
- [x] Referencia 0,947/contactar y plantilla; caso no contactar; errores recuperables.
- [x] Lote sintético, cambio de archivo, filtrado, retorno de navegación y descarga
  sin inferencias involuntarias; no se guardan/exportan extras ni identificadores.
- [x] Gráficos conservan signos, unidades, recuentos y umbrales; políticas de
  `/model` corresponden exactamente al reporte congelado.
- [x] Navegador local en escritorio/móvil, teclado, foco y zoom revisados;
  capturas de la vista previa. Sin acreditar WCAG completa por inspección parcial.
  *Escritorio 1440 px, móvil 390 px, reflow equivalente al 200 % mediante ancho
  720 px; foco visible muestreado. No se certifica zoom nativo ni lector de pantalla.*
- [x] Ruff, formato, hooks y pytest ≥85 %; pruebas del empaquetado con el tema.
  *313 tests, 98,18 %; Space armado con 45 archivos. Build de imagen bloqueado
  por Docker Desktop sin motor activo, no presentado como satisfactorio.*
- [x] Registro actualizado, resultados locales distinguidos de CI/despliegue.

Las cabeceras públicas/framing pendientes en S18 requieren su propia solución
aprobada; el rediseño no los declara resueltos. El despliegue de esta rama se
decide después de revisar la vista previa.
