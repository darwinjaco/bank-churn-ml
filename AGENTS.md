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

## 6. Compuerta SDD

No modificar `src/`, `tests/` ni dependencias sin una especificación y un plan con commit previo. Los cambios de diseño se realizan como enmiendas versionadas de la especificación, con el motivo registrado en `docs/registro-avance.md`. Si el trabajo requiere una decisión no especificada, detenerse y registrar el bloqueo.

## 7. Partición de prueba

No crear funciones que carguen la partición de prueba hasta la evaluación final de la especificación 002. Durante la semana 2 solo se carga entrenamiento y validación para exploración; no existe `load_test()`. La única excepción es `load_test_once` de la spec 002 v1.6 §11.6: se implementa y ejecuta una sola vez, después de versionar la ficha del modelo y con confirmación explícita del responsable.
