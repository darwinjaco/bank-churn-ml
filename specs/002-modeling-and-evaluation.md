# Especificación 002 — Modelado y evaluación

| Campo | Valor |
|---|---|
| Estado | Diseño documentado; implementación pendiente en semanas 3–5 |
| Responsable | Darwin Jacome Cuenca |
| Dependencia | [Especificación 001](001-overview-and-data-contract.md) |
| Última revisión documental | 6 de octubre de 2026 |

## 1. Objetivo

Seleccionar un modelo que **ordene adecuadamente el riesgo y produzca probabilidades calibradas**, como entrada de la futura capa de decisión por beneficio esperado (especificación 003). La selección prioriza calidad de ordenamiento, calibración y simplicidad; el umbral de contacto se justificará mediante beneficio, no mediante F1.

## 2. División de datos

| Conjunto | Proporción | Uso |
|---|---|---|
| Entrenamiento | 60 % | Ajuste de pipelines, validación cruzada, hiperparámetros y ajuste de calibradores mediante predicciones fuera de muestra |
| Validación | 20 % | Comprobación del modelo seleccionado, comparación de calibración y elección del umbral de decisión |
| Prueba | 20 % | **Una evaluación final**, con todas las decisiones ya fijadas |

- División estratificada por `Exited`, con `random_state = 42`.
- Guardar índices en `data/processed/`, junto con el hash del dataset; comprobar ausencia de solapamiento entre conjuntos.
- Todo preprocesamiento se implementará dentro de un `sklearn.Pipeline`. En validación cruzada, se ajustará únicamente con la partición de entrenamiento de cada pliegue.
- El conjunto de prueba no se usará para crear variables, seleccionar modelos, ajustar calibración ni elegir umbrales. El acceso exploratorio previo al dataset completo se documentará como limitación.
- La validación es un conjunto de desarrollo: las métricas empleadas para elegir calibración o umbral no son estimaciones finales independientes. Estas se obtendrán en prueba.

## 3. Preprocesamiento y variables

| Grupo | Columnas | Transformación prevista |
|---|---|---|
| Numéricas | `CreditScore`, `Age`, `Tenure`, `Balance`, `EstimatedSalary` | `StandardScaler` solo para modelos lineales |
| Ordinal | `NumOfProducts` | Entero; auditar el comportamiento de 3–4 productos |
| Binarias | `HasCrCard`, `IsActiveMember` | Sin transformación |
| Categórica | `Geography` | `OneHotEncoder(handle_unknown="error")`, coherente con el contrato cerrado |
| Derivadas candidatas | `has_balance`, `balance_to_salary`, `age_band` | Documentar definición; admitirlas solo con justificación en validación cruzada |

`RowNumber`, `CustomerId` y `Surname` se excluyen. `Gender` se conserva exclusivamente para auditoría: nunca se incorpora como feature, tampoco en experimentos ni mediante variables derivadas. E-01 compara resultados por grupos sin entrenar con `Gender`. `EstimatedSalary` permanece como candidata hasta E-03; la variante que la excluya también excluirá `balance_to_salary` para evitar conservar indirectamente su información.

## 4. Modelos

| Orden | Modelo | Propósito |
|---|---|---|
| 0 | `DummyClassifier(strategy="prior")` | Referencia mínima |
| 1 | Regresión logística (LogReg) | Referencia interpretable y candidata válida para selección |
| 2 | Random Forest (RF) | Referencia no lineal |
| 3 | XGBoost | Candidato de árboles con boosting |

Las redes neuronales quedan fuera del alcance del proyecto para mantener un experimento acotado con 10.000 filas tabulares.

## 5. Protocolo de evaluación

### 5.1. Validación cruzada y trazabilidad

- `StratifiedKFold` de 5 pliegues sobre entrenamiento, con mezcla, semilla 42 e idénticas particiones para comparar modelos.
- Reportar **media ± desviación estándar muestral** entre pliegues para cada métrica de la tabla de comparación.
- Ajuste acotado con `RandomizedSearchCV`: como máximo 50 iteraciones por búsqueda, espacio pequeño y documentado, semilla fija y `scoring="average_precision"`.
- Registrar en MLflow parámetros, métricas, semilla, particiones, commit de Git y hash de datos.
- Las métricas de pliegues reutilizados para ajustar hiperparámetros son estimaciones de desarrollo y pueden ser optimistas. Identificarlas como tales; la evaluación final independiente corresponde a prueba.

### 5.2. Métricas

| Rol | Métrica | Justificación |
|---|---|---|
| Principal | Precisión promedio (AP, `average_precision_score`) | Calidad de ordenamiento de la clase positiva con objetivo desbalanceado |
| Secundaria | ROC-AUC | Ordenamiento global |
| Calibración | Puntuación de Brier y curva de fiabilidad | Las probabilidades alimentan decisiones monetarias |
| Reporte final | Precisión, sensibilidad (recall), F1 y matriz de confusión al umbral elegido | Interpretación de la política fijada por beneficio |

Cuando se use la etiqueta PR-AUC en resultados, se indicará que corresponde a **AP**, no a integración trapezoidal de la curva precisión-sensibilidad. Las métricas que requieren umbral en la tabla inicial usarán 0,5, identificado como referencia técnica; el umbral operativo se fijará en la semana 5.

### 5.3. Calibración sin solapamiento de ajuste y evaluación

La calibración se implementará en la semana 5, una vez seleccionado el modelo:

1. Con hiperparámetros fijados, generar predicciones fuera de muestra (OOF) en entrenamiento mediante 5 pliegues estratificados. Cada observación se predice con un pipeline que no se ajustó con ella.
2. Ajustar los calibradores sigmoidal e isotónico con esas predicciones OOF y las etiquetas de entrenamiento. Después, ajustar el pipeline base con todo el entrenamiento.
3. Comparar la salida sin calibrar y las variantes calibradas en validación mediante Brier y curvas de fiabilidad. Elegir la variante con menor Brier; ante igualdad, preferir sin calibración adicional y luego sigmoidal sobre isotónica.
4. Fijar en validación el umbral por beneficio esperado según la especificación 003. No ajustar el calibrador con las etiquetas de validación.
5. Congelar pipeline, calibrador, supuestos y umbral antes de la evaluación final en prueba. No reajustar con validación antes de esa evaluación.

El uso de validación para elegir calibración y umbral se registrará como selección de desarrollo, no como medición independiente de rendimiento.

## 6. Regla de selección del modelo, fijada antes de entrenar

1. Obtener el mayor promedio de AP en validación cruzada entre LogReg, RF y XGBoost; Dummy es únicamente una referencia mínima.
2. Considerar cercanos los candidatos cuya diferencia respecto al mejor promedio sea menor que la desviación estándar del mejor candidato. Si los promedios son iguales, también se consideran cercanos. Elegir entre ellos el más simple: LogReg, luego RF, luego XGBoost. Esta es una heurística de parsimonia, no una prueba de significación estadística.
3. Comprobar en validación que el candidato elegido supera a Dummy en AP. Si no lo supera, registrar el fallo del criterio y revisar el desarrollo sin consultar prueba.
4. Si se elige RF o XGBoost, exigir además que supere a LogReg en AP de validación. Si no lo logra, conservar LogReg siempre que supere a Dummy; de lo contrario, el criterio de aceptación queda sin cumplir.
5. Si se elige LogReg, compararla con Dummy y reportar las diferencias frente a los modelos complejos; no exigir que supere a sí misma.

Registrar cada aplicación de esta regla en MLflow. La selección en validación no reemplaza la evaluación final en prueba.

## 7. Experimentos requeridos

| ID | Experimento | Pregunta |
|---|---|---|
| E-01 | Auditoría de equidad por `Gender`, siempre excluido de las features | ¿Qué diferencias de rendimiento, calibración y decisiones aparecen entre grupos? El costo predictivo de excluirlo no se estima porque no se entrena un modelo con esa variable |
| E-02 | Con y sin la información de `NumOfProducts` | ¿Cuánto depende el modelo del patrón Q-03? La ablación completa se complementará con análisis separado de los clientes con 3–4 productos |
| E-03 | Con y sin `EstimatedSalary` y sus derivadas | ¿Aporta utilidad en combinación con otras variables o introduce ruido? |
| E-04 | Probabilidad original frente a calibración isotónica y sigmoidal | ¿Se reduce Brier en validación con calibradores ajustados únicamente en entrenamiento? |

Los experimentos usarán las mismas particiones y semillas. Cada conclusión incluirá métricas, tamaño de los segmentos pertinentes y limitaciones. Las decisiones de variables se fijarán antes de la evaluación final.

## 8. Criterios de aceptación

- [ ] Tabla de comparación en el README con media ± desviación estándar y protocolo de cálculo.
- [ ] Experimentos E-01 a E-04 documentados con resultados y conclusión breve.
- [ ] División reproducible y ausencia de solapamientos verificada mediante tests.
- [ ] Modelo seleccionado conforme a §6 y calibración conforme a §5.3; decisiones registradas en MLflow.
- [ ] Conjunto de prueba utilizado en una única evaluación final, registrada con la etiqueta `final=true`.
- [ ] Artefacto guardado: pipeline completo, calibrador elegido si aplica y `metadata.json`, con variables, versiones, hash de datos y referencia a la política de decisión.

## 9. Definición de cierre

Modelo y calibración justificados, experimentos documentados y artefacto cargable por el futuro módulo `predict.py`, con un test de predicción reproducible. La capa de decisión y su umbral monetario deberán satisfacer además la especificación 003. La evidencia y los pendientes se mantendrán en el [registro de avance](../docs/registro-avance.md).
