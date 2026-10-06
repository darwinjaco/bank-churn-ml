# Registro de avance

Documento de seguimiento del proyecto **Abandono bancario → Decisiones de retención**. Se actualiza al terminar cada sección de trabajo y enlaza la evidencia que permite cerrar una fase.

| Campo | Valor |
|---|---|
| Responsable | Darwin Jacome Cuenca |
| Inicio previsto | 5 de octubre de 2026 |
| Fin previsto | 29 de noviembre de 2026 |
| Dedicación estimada | 8 horas por semana; 64 horas en total |
| Última actualización | 6 de octubre de 2026 |
| Fase actual | Semana 1: documentación y preparación de la verificación técnica |

Referencias: [README](../README.md), [especificación 001](../specs/001-overview-and-data-contract.md) y [especificación 002](../specs/002-modeling-and-evaluation.md).

## 1. Cómo usar este registro

- Una **fase** corresponde a una semana del cronograma; una **sección** es un bloque de trabajo con objetivo y alcance concretos.
- Estados: **pendiente**, **en curso**, **completada** o **bloqueada**. Una base implementada puede tener su cierre todavía pendiente.
- Al terminar una sección, registrar fecha, cambios, comprobaciones realmente ejecutadas, decisiones y siguiente paso.
- Marcar un criterio de cierre solo cuando su evidencia esté disponible. Diferenciar resultados históricos, comprobaciones locales y ejecuciones de CI.
- Si cambia el alcance o el calendario, conservar el plan inicial y anotar el ajuste en la sección correspondiente.

## 2. Seguimiento de fases

Todas las fechas corresponden a 2026 y representan objetivos de planificación.

| Fase | Fechas | Entregable | Criterio de cierre | Estado |
|---|---|---|---|---|
| Semana 1 | 5–11 oct | Repo, uv, Ruff, pytest, pre-commit, CI mínimo, specs 001–002 y Pandera | Tests pasan en CI | En curso; base implementada y cierre técnico pendiente |
| Semana 2 | 12–18 oct | EDA, hipótesis y auditoría de productos 3–4 y balance cero | Hipótesis contrastadas con pruebas estadísticas, tamaños de efecto e incertidumbre | Pendiente |
| Semana 3 | 19–25 oct | Pipeline, división estratificada, Dummy/LogReg y MLflow | Modelos de referencia registrados en MLflow | Pendiente |
| Semana 4 | 26 oct–1 nov | RF, XGBoost, validación cruzada y ajuste acotado | Tabla de media ± desviación estándar por modelo | Pendiente |
| Semana 5 | 2–8 nov | Calibración, umbral monetario, lift y beneficio por decil, sensibilidad | Umbral justificado por beneficio esperado bajo supuestos explícitos | Pendiente |
| Semana 6 | 9–15 nov | SHAP, errores, segmentos y ficha del modelo | Limitaciones documentadas | Pendiente |
| Semana 7 | 16–22 nov | FastAPI, Streamlit, tests de API y Docker Compose | `docker compose up` funciona desde cero | Pendiente |
| Semana 8 | 23–29 nov | Cambio de distribución simulado, despliegue y README final | URL pública y reproducibilidad verificadas | Pendiente |

**Prioridad de alcance:** proteger la capa de decisión de la semana 5. Si hay retrasos, reducir primero el monitoreo de cambios de distribución de la semana 8 y registrar el ajuste.

## 3. Seguimiento de especificaciones

| Especificación | Tema | Estado | Momento previsto |
|---|---|---|---|
| 001 | Visión general y contrato de datos | Documentada en español; cierre técnico pendiente | Semana 1 |
| 002 | Modelado y evaluación | Documentada en español; implementación pendiente | Semanas 3–5 |
| 003 | Capa de decisión y beneficio esperado | Pendiente de redacción | Antes de implementar la semana 5 |
| 004 | API y dashboard | Pendiente de redacción | Antes de implementar la semana 7 |
| 005 | Operación: tests, Docker, CI y monitoreo | Pendiente de redacción | Antes de ampliar operación y serving |

## 4. Punto de partida — 6 de octubre de 2026

### Evidencia disponible

- Commit inicial: `6037f9e` (`chore: week 1 scaffold, data contract and validation`).
- Repositorio local en `master`; el CI de push está configurado para `main` y no hay remoto de GitHub.
- Código de carga y validación implementado; herramientas y workflow configurados.
- CSV localizado en la carpeta de Descargas del usuario como `Churn_Modelling.csv`. La revisión del archivo muestra 10.000 registros y la cabecera esperada de 14 columnas, sin `Complain`.
- CSV pendiente de copia a `data/raw/` y validación completa en este entorno.
- [Reporte de calidad existente](../reports/data_quality.json): 20,37 % de abandono, 36,17 % de balances cero y 326 clientes con 3–4 productos.
- Resultados del contexto anterior: 22 tests, cobertura del 97 % y comprobaciones de Ruff/pre-commit satisfactorias. **Pendientes de reproducción local y de confirmación en CI.**

### Pendientes de cierre de la semana 1

- [ ] Sincronizar el entorno con `uv sync --locked`.
- [ ] Copiar el CSV a `data/raw/Churn_Modelling.csv` y ejecutar `churn-validate`.
- [ ] Verificar tests, cobertura mínima del 85 %, Ruff y pre-commit.
- [ ] Revisar cobertura de las infracciones del contrato indicadas en la especificación 001.
- [ ] Alinear la rama con `main`, completar la preparación para GitHub y configurar el remoto.
- [ ] Publicar cuando se indique y registrar una ejecución satisfactoria de CI.
- [ ] Actualizar los criterios de aceptación con la evidencia obtenida.

## 5. Historial de secciones

### S01 — Documentación en español y revisión del diseño

| Campo | Valor |
|---|---|
| Fecha | 6 de octubre de 2026 |
| Fase | Semana 1 |
| Estado | Completada |
| Objetivo | Establecer documentación en español, coherente con el repositorio, y un registro de avance por fases |

**Trabajo realizado**

- Revisados README, ambas especificaciones, licencia, reporte, código, tests y configuración de herramientas/CI.
- Traducido el README con instrucciones de PowerShell, estado real, adquisición de datos, publicación y cronograma.
- Traducidas y ajustadas las especificaciones 001 y 002.
- Creado este registro para actualizarlo al cerrar cada sección.
- Identificadas las cinco especificaciones previstas y sus momentos de redacción.

**Archivos modificados o creados**

- `README.md`
- `specs/001-overview-and-data-contract.md`
- `specs/002-modeling-and-evaluation.md`
- `docs/registro-avance.md`

**Decisiones documentadas**

- Mantener `EstimatedSalary` como candidata hasta medir su contribución mediante E-03; su AUC individual no basta para excluirla.
- Tratar el posible origen sintético como hipótesis y limitar las conclusiones de la alarma univariada de fuga de información.
- Permitir seleccionar LogReg y exigir mejora frente a LogReg únicamente a candidatos más complejos.
- Ajustar calibradores con predicciones OOF de entrenamiento y evaluarlos en validación; reservar prueba para una evaluación final con decisiones congeladas.
- Conservar nombres de columnas, comandos e identificadores técnicos para mantener trazabilidad con el código.
- Mantener el texto legal de la licencia MIT original.

**Comprobaciones y evidencia**

- Revisión del estado inicial: árbol de trabajo limpio, rama `master` y sin remoto.
- `git diff --check`: satisfactorio, sin errores de espacios en los archivos modificados.
- `git diff --no-index --check -- /dev/null docs/registro-avance.md`: satisfactorio, sin errores de espacios en el documento nuevo.
- Revisión manual de enlaces relativos y del ancla `README.md#datos`: destinos existentes y referencias coherentes.
- Revisión de cifras contra `reports/data_quality.json` y consistencia entre README, especificaciones y cronograma: satisfactoria.
- Las comprobaciones de ejecución del proyecto corresponden a S02 y siguen pendientes.

**Siguiente paso**

Comenzar S02: entorno, CSV y verificación local de la semana 1. El cierre de S01 corresponde a documentación; la fase completa sigue en curso.

### S02 — Entorno, CSV y verificación local

| Campo | Valor |
|---|---|
| Fecha | Pendiente |
| Fase | Semana 1 |
| Estado | Pendiente |
| Objetivo | Reproducir la validación y las comprobaciones de calidad con el entorno y CSV locales |

Registrar aquí los comandos ejecutados, resultados de tests y cobertura, salida de la validación, diferencias respecto al reporte histórico y pendientes descubiertos.

### S03 — Preparación y publicación en GitHub

| Campo | Valor |
|---|---|
| Fecha | Pendiente |
| Fase | Semana 1 |
| Estado | Pendiente |
| Objetivo | Alinear rama y remoto, completar enlaces públicos y verificar CI |

Registrar aquí el repositorio, la rama, el commit publicado y la URL de la ejecución de CI que respalde el cierre de la semana 1.

## 6. Plantilla para nuevas secciones

```markdown
### SXX — Nombre de la sección

| Campo | Valor |
|---|---|
| Fecha | AAAA-MM-DD |
| Fase | Semana N |
| Estado | Pendiente / En curso / Completada / Bloqueada |
| Objetivo | Resultado concreto esperado |

**Trabajo realizado**
- Tareas terminadas.

**Archivos modificados o creados**
- Rutas relevantes.

**Comprobaciones y evidencia**
- Comando o revisión, resultado y enlace o ruta de evidencia.

**Decisiones y pendientes**
- Decisiones adoptadas, limitaciones y bloqueos reales.

**Siguiente paso**
- Próxima acción concreta.
```
