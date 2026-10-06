# Especificación 004 — Capa de decisión por beneficio esperado

| Campo | Valor |
|---|---|
| Estado | Implementada v1.0 (semana 5) |
| Responsable | Darwin Jacome Cuenca |
| Semana | 5 (2–8 de noviembre de 2026) |
| Dependencias | [002](002-modeling-and-evaluation.md) §5.3 (calibración, v1.5) |
| Alcance aprobado | **Opción A únicamente**: umbral analítico por beneficio esperado |

## 1. Objetivo

Convertir la probabilidad calibrada de abandono de cada cliente en una decisión **contactar / no contactar** mediante una regla económica explícita, y medir cuánto dinero aporta frente a políticas sin modelo.

## 2. Supuestos económicos

El dataset no contiene ingresos ni costos. Los valores son **supuestos ilustrativos**, no datos de ninguna institución.

| Símbolo | Supuesto | Valor |
|---|---|---|
| V | Valor de un cliente retenido (CLV) | 1.000 € |
| c | Costo de contactar a un cliente | 50 € |
| s | Probabilidad de que la campaña retenga a un cliente que iba a irse | 30 % |

## 3. Regla de decisión

Beneficio esperado de contactar al cliente i con probabilidad calibrada pᵢ:

```text
EBᵢ = pᵢ · s · V − c
```

Se contacta si y solo si EBᵢ > 0, es decir:

```text
pᵢ > t* = c / (s · V) = 50 / (0,30 · 1.000) = 1/6 ≈ 0,1667
```

El umbral es **analítico**: no se ajusta con datos de validación ni de prueba. Por eso no hay riesgo de sobreajustar el umbral.

## 4. Supuestos implícitos y limitaciones

1. La campaña solo cambia el resultado de quienes iban a irse; contactar a quien se iba a quedar cuesta c y no aporta ingreso.
2. s es igual para todos los clientes: no hay modelo de *uplift* ni datos de tratamiento.
3. V es igual para todos los clientes: el dataset no tiene ingresos por cliente.
4. No hay efectos negativos del contacto (por ejemplo, clientes que se van por ser contactados).
5. La regla solo es válida si p es una probabilidad bien calibrada (spec 002 §5.3, E-04).

## 5. Alcance

| Incluido | Excluido por decisión del responsable |
|---|---|
| Umbral analítico t* | Política por presupuesto o capacidad, lift y beneficio por decil (opción B) |
| Evaluación del beneficio en validación frente a políticas de referencia | Umbral robusto y análisis de sensibilidad de los supuestos (opción C) |
| Métricas de clasificación en t* | Optimización del umbral con datos |

Las opciones B y C quedan registradas como trabajo futuro.

## 6. Evaluación (validación, desarrollo)

Beneficio realizado esperado de una política que contacta al conjunto C:

```text
B(C) = Σ_{i ∈ C} (yᵢ · s · V − c)
```

donde yᵢ es la etiqueta real. Políticas comparadas, todas sobre las 2.000 filas de validación:

| Política | Definición |
|---|---|
| Nadie | No contactar: B = 0 |
| Todos | Contactar a los 2.000 clientes |
| Aleatoria 20 % | Valor esperado analítico: 0,20 × B(Todos) |
| **Modelo** | Contactar si p calibrada > t* |
| Oráculo (cota superior) | Contactar solo a quienes realmente se van |

Reportar para la política del modelo: clientes contactados (n y %), abandonos capturados, precisión, sensibilidad (recall), F1, matriz de confusión, beneficio total, beneficio por cliente contactado, diferencia frente a la mejor referencia sin modelo y fracción del beneficio del oráculo capturada.

Estas cifras son de **desarrollo**: la validación ya se usó para seleccionar el modelo (spec 002 §6) y para elegir el calibrador (§5.3). La estimación independiente corresponde a la evaluación final en prueba, con todo congelado.

## 7. Salidas

| Archivo | Contenido | En Git |
|---|---|---|
| `reports/decision.json` | Supuestos, t*, políticas, métricas | Sí |
| `reports/decision.md` | Reporte legible generado desde el JSON | Sí |
| `reports/model_metadata.json` | Copia de la metadata del artefacto (sin binarios) | Sí |
| `models/` | Pipeline ajustado, calibrador y `metadata.json` | No |

## 8. Decisiones técnicas

| ID | Decisión | Motivo |
|---|---|---|
| D-13 | Solo opción A | Decisión del responsable: regla simple y explicable |
| D-14 | Umbral analítico, sin ajuste con datos | Evita sobreajustar el umbral a validación |
| D-15 | Evaluación del beneficio en validación marcada como desarrollo | Validación ya se usó para seleccionar modelo y calibrador |
| D-16 | Supuestos en `config.py` como constantes únicas | Una sola fuente; la metadata del artefacto los copia |

## 9. Criterios de aceptación

- [x] t* calculado desde las constantes de `config.py` y verificado por test (1/6).
- [x] Beneficio de cada política reproducible desde `reports/decision.json`, con tests sobre un caso de valores conocidos.
- [x] La política del modelo usa la probabilidad calibrada elegida en E-04.
- [x] Reporte sin lenguaje causal y con las limitaciones de §4.
- [x] Prueba sin usar.

## 10. Definición de cierre

Regla implementada y testeada, beneficio en validación reportado frente a las referencias, artefacto congelado con metadata y registro actualizado.
