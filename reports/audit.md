# Explicabilidad y auditoría — Semana 6

Generado con `uv run python -m churn.model_card` desde [audit.json](audit.json) (spec 002 v1.6 §11). Validación, artefacto congelado de la semana 5 y t* = 1/6. Análisis de **desarrollo**: no cambia el modelo.

## SHAP

Explica la probabilidad sin calibrar del Random Forest base; aditividad comprobada (error máximo 9.3e-15). Importancia predictiva, no causal.

| Variable | Media de abs(SHAP) |
|---|---|
| Age | 0.1030 |
| NumOfProducts | 0.0713 |
| IsActiveMember | 0.0540 |
| Geography=Germany | 0.0274 |
| Balance | 0.0148 |
| has_balance | 0.0134 |
| CreditScore | 0.0080 |
| Geography=France | 0.0072 |
| Tenure | 0.0050 |
| HasCrCard | 0.0036 |
| Geography=Spain | 0.0036 |

| Grupo (R4) | Media de abs(SHAP) del grupo |
|---|---|
| Geography | 0.0344 |
| saldo (Balance + has_balance) | 0.0262 |
| saldo y geografía (R4) | 0.0540 |

Explicaciones locales (cinco mayores contribuciones; valores de las variables tal como las recibe el modelo):

- **mayor probabilidad** (caso sin identificador, p calibrada 0.975): NumOfProducts = 4 (+0.347); Age = 55 (+0.237); IsActiveMember = 0 (+0.063); Geography=Germany = 1 (+0.038); Balance = 118773 (+0.036).
- **cerca del umbral** (caso sin identificador, p calibrada 0.167): NumOfProducts = 2 (-0.095); Geography=Germany = 1 (+0.051); Balance = 114319 (+0.034); Age = 40 (-0.033); IsActiveMember = 0 (+0.032).
- **menor probabilidad** (caso sin identificador, p calibrada 0.042): Age = 30 (-0.060); NumOfProducts = 2 (-0.057); IsActiveMember = 1 (-0.027); has_balance = 0 (-0.022); Geography=Germany = 0 (-0.009).

Figura: [shap_importance.png](figures/shap_importance.png).

## Errores en t*

| Grupo | n | Edad | Productos | Activo | Alemania | Saldo cero |
|---|---|---|---|---|---|---|
| VP | 310 | 47.4 | 1.43 | 31.9% | 49.4% | 25.8% |
| FP | 311 | 44.9 | 1.25 | 41.8% | 37.6% | 20.6% |
| FN | 97 | 37.3 | 1.39 | 58.8% | 21.6% | 34.0% |
| VN | 1282 | 35.5 | 1.61 | 57.7% | 16.4% | 45.5% |

- Banda ±0.05 alrededor de t*: 319 clientes, abandono 20.4%; 122 contactados. Pequeños cambios de supuestos moverían a estos clientes de lado.

- Mayor proporción de abandonos no contactados: tramo_edad = 18-29 (65.4% de 26 abandonos).

## Segmentos

| Segmento | Nivel | n | Abandono | Predicho | Brecha | Contacto | Sensibilidad | Precisión |
|---|---|---|---|---|---|---|---|---|
| Geography | France | 1013 | 14.6% | 16.3% | +0.017 | 22.6% | 67.6% | 43.7% |
| Geography | Germany | 501 | 34.7% | 32.5% | -0.023 | 53.9% | 87.9% | 56.7% |
| Geography | Spain | 486 | 17.5% | 17.4% | -0.001 | 25.1% | 67.1% | 46.7% |
| tramo_edad | 18-29 | 339 | 7.7% | 8.7% | +0.010 | 6.2% | 34.6% | 42.9% |
| tramo_edad | 30-39 | 845 | 11.2% | 10.3% | -0.009 | 11.8% | 45.3% | 43.0% |
| tramo_edad | 40-49 | 535 | 29.2% | 31.0% | +0.018 | 56.8% | 87.2% | 44.7% |
| tramo_edad | 50-59 | 171 | 57.9% | 56.2% | -0.017 | 84.8% | 96.0% | 65.5% |
| tramo_edad | 60+ | 110 | 28.2% | 30.9% | +0.027 | 46.4% | 87.1% | 52.9% |
| productos | 1 | 1034 | 28.3% | 26.8% | -0.015 | 46.2% | 79.9% | 49.0% |
| productos | 2 | 910 | 7.6% | 9.7% | +0.021 | 9.6% | 44.9% | 35.6% |
| productos | 3-4 | 56 | 80.4% | 84.1% | +0.038 | 100.0% | 100.0% | 80.4% |
| IsActiveMember | 0 | 974 | 25.8% | 26.8% | +0.011 | 40.2% | 84.1% | 53.8% |
| IsActiveMember | 1 | 1026 | 15.2% | 14.7% | -0.005 | 22.3% | 63.5% | 43.2% |
| has_balance | 0 | 760 | 14.9% | 15.4% | +0.006 | 18.9% | 70.8% | 55.6% |
| has_balance | 1 | 1240 | 23.7% | 23.8% | +0.001 | 38.5% | 78.2% | 48.2% |
| Gender | Female | 889 | 24.0% | 22.1% | -0.018 | 31.2% | 77.5% | 59.6% |
| Gender | Male | 1111 | 17.5% | 19.4% | +0.019 | 31.0% | 74.7% | 42.2% |

## E-01: auditoría por género

n: Female 889, Male 1111. Tasa observada de abandono: Female 24.0%, Male 17.5%. IC 95 % por bootstrap estratificado (2.000 réplicas, semilla 42). Alerta = IC sin 0 y abs(Δ) ≥ 0,05.

| Métrica | Female | Male | Δ (F - M) | IC 95 % | Alerta |
|---|---|---|---|---|---|
| Tasa de contacto | 31.2% | 31.0% | +0.002 | [-0.039; +0.044] | no |
| Sensibilidad | 77.5% | 74.7% | +0.027 | [-0.057; +0.109] | no |
| Precisión | 59.6% | 42.2% | +0.174 | [+0.103; +0.252] | **sí** |
| Brecha de calibración | -1.8% | 1.9% | -0.038 | [-0.067; -0.009] | no |

- La tasa de contacto y la sensibilidad no muestran diferencias detectables.
- La alerta de precisión es coherente con tasas base distintas: con igual tasa de contacto, el grupo con más abandono obtiene mayor precisión; contactar a un hombre tiene, en promedio, menor probabilidad de evitar un abandono.
- Al excluir `Gender`, el modelo subestima levemente a las mujeres y sobrestima a los hombres (Δ de calibración con IC sin 0, por debajo del umbral de alerta).
- Según §11.4 solo se reporta; cualquier mitigación requiere enmienda.

## Trazabilidad

Commit: `6e398a3de1521aea6f3cef5734673cb47116f722`; artefacto: `f2796d55bd2bd4683b6745516061486654b43bba`; MLflow: `0913aa3e07bb4a0e916834a2959c2bf0`.
