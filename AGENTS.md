# Reglas de trabajo para agentes

Estas reglas se aplican a todo el repositorio. El trabajo y la documentación se realizan en español; se conservan los identificadores técnicos del código y del dataset.

## 1. Especificación antes de implementación

No implementar funcionalidades sin una especificación correspondiente en `specs/`. Leerla antes de trabajar y actualizarla si cambia el diseño. Respetar el alcance y los criterios de aceptación de la fase actual.

## 2. `Gender` nunca como feature

`Gender` nunca se incorpora a las entradas de un modelo, ni a variables derivadas usadas para predecir, ni a experimentos de entrenamiento. Se conserva exclusivamente para auditoría de equidad y análisis de segmentos. E-01 debe respetar esta restricción.

## 3. Conjunto de prueba reservado

El test set se utiliza una sola vez para la evaluación final, con variables, preprocesamiento, modelo, hiperparámetros, calibración, supuestos económicos y umbral ya congelados. No usarlo para exploración dirigida, selección o ajuste. Registrar esa evaluación en MLflow con `final=true`, según la especificación 002.

## 4. CI en verde antes de cada commit

Exigir CI en verde antes de cada commit. Ejecutar además las comprobaciones locales del workflow y los hooks pertinentes:

```powershell
uv sync --locked
uv run ruff check .
uv run ruff format --check .
uv run pre-commit run --all-files
uv run pytest --cov=churn --cov-report=term-missing --cov-fail-under=85
```

La cobertura mínima es del 85 %. No omitir hooks ni ignorar fallos. Los archivos nuevos deben incluirse en las comprobaciones de pre-commit. Si todavía no hay remoto o ejecución de GitHub Actions, registrar el bloqueo: un resultado local satisfactorio no es evidencia de CI remoto en verde.

## 5. Registro actualizado en cada sección

Actualizar `docs/registro-avance.md` al finalizar cada sección. Incluir cambios, comandos realmente ejecutados, resultados resumidos, decisiones, bloqueos y siguiente paso. Marcar como completado solo lo verificado; conservar la distinción entre comprobación local y CI remoto.
