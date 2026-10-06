# Especificación 003 — EDA e hipótesis preregistradas

| Campo | Valor |
|---|---|
| Estado | Aprobada v1.1 |
| Responsable | Darwin Jacome Cuenca |
| Semana | 2 (12–18 de octubre de 2026) |
| Dependencias | [001](001-overview-and-data-contract.md) (contrato), [002](002-modeling-and-evaluation.md) §2 (división) |
| Versión | v1.1 — enmienda B-01: procedimiento exacto R×C; H1–H6 sin cambios (v1.0 congeló las hipótesis) |

## 1. Objetivo

Entender los datos y contrastar hipótesis de negocio **definidas antes de ver los resultados**, con tamaños de efecto e intervalos de confianza. El resultado alimenta el diseño de variables (semana 3) y las auditorías E-02 y E-03.

**Por qué preregistrar:** con unas 8.000 filas, casi cualquier diferencia es estadísticamente significativa. Si las hipótesis se eligen después de mirar los gráficos, los p-valores pierden sentido. Por eso se fija primero qué se prueba, cómo y qué umbral de relevancia práctica se exige.

## 2. Alcance

| Incluido | Excluido |
|---|---|
| Implementar la división 60/20/20 de la spec 002 §2 (se adelanta desde la semana 3) | Entrenar modelos predictivos |
| EDA descriptivo y contraste de H1–H6 **solo en entrenamiento + validación** | Cualquier lectura del conjunto de prueba |
| Funciones estadísticas puras y testeadas en `src/` | Lógica de negocio dentro del notebook |
| Reporte de resultados y conclusiones | Afirmaciones causales |

## 3. Datos de trabajo

- **Partición de exploración:** entrenamiento + validación (8.000 filas). La partición de prueba no tiene ninguna función de carga en esta semana; no existe un camino de código para leerla.
- **Manifiesto de división** (`reports/split_manifest.json`, versionado en Git): tamaño y tasa de abandono por conjunto, semilla, SHA-256 del CSV y SHA-256 de los `CustomerId` ordenados de cada conjunto. Un test regenera la división y comprueba que coincide con el manifiesto. Así se puede demostrar que la prueba no cambió desde la semana 2.
- `data/processed/split.json` (índices completos) sigue fuera de Git, según D-03.
- **Limitación ya existente:** el reporte de calidad de la semana 1 se calculó sobre las 10.000 filas. Son estadísticos univariados agregados, sin modelos ni hipótesis; se documenta y no invalida el protocolo.

## 4. Protocolo estadístico

- Nivel de significación α = 0,05, bilateral.
- **Familia confirmatoria:** H1–H5 (5 contrastes). Los p-valores se corrigen con **Holm**.
- **H6 no entra en la familia:** busca demostrar *ausencia* de señal y se evalúa por equivalencia, no con un p-valor.
- Una hipótesis se **confirma** solo si se cumplen a la vez:
  1. p ajustado < 0,05;
  2. el efecto va en la dirección preregistrada;
  3. el IC 95 % del efecto supera el **umbral de relevancia práctica** de la tabla.
  Si se cumple 1 pero no 3: "estadísticamente detectable, sin relevancia práctica".
- Intervalos: Wilson para proporciones; Newcombe (método 10) para diferencias de riesgo; Woolf (log) para odds ratios crudos; Wald del modelo para odds ratios ajustados; bootstrap percentil con 2.000 réplicas y semilla 42 para AUC.
- χ² de Pearson sin corrección de Yates (n grande). Si alguna frecuencia esperada es < 5:
  - tabla 2×2: Fisher exacto (`scipy.stats.fisher_exact`, bilateral);
  - tabla R×C: test exacto de Freeman–Halton por enumeración completa de las tablas con marginales fijos; p = suma de las probabilidades ≤ p_obs × (1 + 1e-7). Prohibido usar remuestreo Monte Carlo o permutaciones en pruebas confirmatorias.
- Cualquier análisis no listado en H1–H6 se etiqueta **exploratorio** y no puede reportarse como confirmado.

## 5. Hipótesis preregistradas

| ID | Hipótesis (H₁) | Prueba principal | Efecto e IC | Relevancia práctica |
|---|---|---|---|---|
| H1 | Los clientes inactivos (`IsActiveMember = 0`) abandonan más que los activos | χ² 2×2 | Diferencia de riesgo (inactivo − activo); OR | DR ≥ 5 pp |
| H2 | La relación con `NumOfProducts` **no es monótona**: tasa(2) < tasa(1) < tasa(3–4) | χ² 3×2 sobre los niveles {1, 2, 3–4} | V de Cramér; tasa por nivel con IC Wilson | Los tres IC de Wilson no se solapan y siguen el orden indicado |
| H3 | Alemania abandona más que Francia y España **incluso controlando el saldo** | Wald del coeficiente `is_germany` en `logit(Exited) ~ is_germany + has_balance + balance_10k` | OR crudo y OR ajustado; % de atenuación del log-OR | OR ajustado ≥ 1,5 |
| H4 | La edad tiene un efecto **no lineal** con forma de U invertida | Razón de verosimilitud: `~ age_c` frente a `~ age_c + age_c²` (edad centrada en la media) | Coeficiente cuadrático (< 0); tasa por tramo de edad con IC Wilson | Coeficiente cuadrático < 0 y edad de máximo riesgo dentro de 18–92 |
| H5 | Los clientes con `Balance = 0` abandonan **menos** que los clientes con saldo | χ² 2×2 | DR (sin saldo − con saldo) | \|DR\| ≥ 5 pp |
| H6 | `EstimatedSalary` **no** tiene señal univariada útil | Equivalencia por AUC | AUC con IC bootstrap | IC 95 % completamente dentro de [0,45 ; 0,55] |

Definiciones fijas:

- `balance_10k = Balance / 10.000`; `has_balance = Balance > 0`.
- Tramos de edad: 18–29, 30–39, 40–49, 50–59, 60+.
- Edad de máximo riesgo en H4: `−β₁ / (2·β₂)` + media de edad.
- H3 compara Alemania contra el resto (Francia + España juntas).

Análisis secundarios (descriptivos, fuera de la familia):

- H5: Mann-Whitney de `Balance` entre quienes abandonan y quienes no, solo con `Balance > 0` (efecto: AUC).
- H6: KS de `EstimatedSalary` contra una uniforme en [mín, máx]. Es descriptivo porque los parámetros salen de la muestra; no prueba que el dato sea sintético.

## 6. Entradas y salidas

| Tipo | Ruta | En Git |
|---|---|---|
| Entrada | `data/raw/Churn_Modelling.csv` | No |
| Índices de división | `data/processed/split.json` | No |
| Manifiesto de división | `reports/split_manifest.json` | Sí |
| Resultados | `reports/hypotheses.json` (generado por `churn-hypotheses`) | Sí |
| Conclusiones | `reports/eda_hypotheses.md` (redactado; las cifras salen del JSON) | Sí |
| Figuras (máx. 6, PNG < 200 KB) | `reports/figures/` | Sí |
| Narrativa | `notebooks/01_eda.ipynb` (salidas eliminadas por nbstripout) | Sí |

Figuras previstas: abandono por `NumOfProducts` con IC; abandono por tramo de edad con IC; OR crudo frente a ajustado de Alemania; distribución de `Balance` con la masa en cero; histograma de `EstimatedSalary`; abandono por `IsActiveMember`.

## 7. Decisiones técnicas

| ID | Decisión | Motivo |
|---|---|---|
| D-07 | Adelantar la división a la semana 2 | El EDA no debe ver la prueba; las decisiones de variables se tomarán con datos de exploración |
| D-08 | Sin función de carga para la prueba en esta semana | Protección estructural, no solo por disciplina |
| D-09 | Manifiesto con hashes versionado | Evidencia verificable de que la prueba no cambió |
| D-10 | Holm sobre H1–H5; equivalencia para H6 | Controla el error de familia; un p-valor no prueba ausencia de efecto |
| D-11 | `statsmodels` para modelos logísticos y `scipy` para contrastes | IC y razón de verosimilitud estándar y auditables; no reimplementar inferencia |
| D-12 | Agrupar 3 y 4 productos en H2 | Nivel 4 con muy pocas filas; evita celdas pequeñas |

## 8. Criterios de aceptación

Evidencia: [registro S04–S06](../docs/registro-avance.md), [resultados](../reports/hypotheses.json), [conclusiones](../reports/eda_hypotheses.md) y [CI técnico](https://github.com/darwinjaco/bank-churn-ml/actions/runs/37487169164). La revisión del responsable de diseño sigue pendiente.

- [x] Esta especificación tiene commit **antes** de cualquier cambio en `src/` o `tests/`.
- [x] La división reproduce el manifiesto: tamaños 6.000 / 2.000 / 2.000 (±1), sin solapamiento, tasa de abandono por conjunto a ≤ 1 pp de la global.
- [x] Las funciones estadísticas tienen tests con valores de referencia conocidos (sección 9).
- [x] Los contrastes detectan un efecto sembrado en datos sintéticos y no rechazan H₀ cuando no hay efecto (semilla fija).
- [x] `reports/hypotheses.json` contiene, por hipótesis: estadístico, p crudo, p Holm, efecto, IC y veredicto (`confirmada`, `detectable sin relevancia`, `no confirmada`).
- [x] `reports/eda_hypotheses.md` tiene una conclusión de una línea por hipótesis y sus implicaciones para la semana 3.
- [x] Ningún módulo de esta semana usa `Gender` ni carga la partición de prueba (test que lo comprueba).
- [x] CI en verde y cobertura ≥ 85 %.

## 9. Valores de referencia para tests

| Función | Entrada | Resultado esperado |
|---|---|---|
| IC de Wilson 95 % | 50 éxitos de 100 | [0,4038 ; 0,5962] |
| IC de Wilson 95 % | 0 éxitos de 20 | [0,0000 ; 0,1611] |
| OR con IC de Woolf | tabla [[20, 80], [10, 90]] | OR 2,25; IC [0,9943 ; 5,0915] |
| Holm | p = [0,01; 0,04; 0,03; 0,005] | [0,03; 0,06; 0,06; 0,02] |
| V de Cramér | [[50, 0], [0, 50]] | 1,0 |
| Freeman–Halton | [[8, 2], [1, 5], [0, 4]] | p = 0,008764 |
| Freeman–Halton | [[3, 1], [1, 3], [0, 0]] | p = 0,485714 (igual a Fisher 2×2) |

## 10. Definición de cierre

Spec con commit, código y tests en verde en CI, resultados generados sobre datos reales, conclusiones redactadas, registro actualizado (S04–S06) y hallazgos trasladados a la tabla Q de la spec 001.
