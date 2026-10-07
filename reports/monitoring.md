# Monitoreo simulado de cambios de distribución

Generado por `churn-monitor` (spec 006 §4). Referencia: entrenamiento; actual: validación remuestreada con semilla 2028. La partición de prueba no se usa. Umbrales y expectativas preregistrados antes de ejecutar.

## Escenarios

| Escenario | Definición |
|---|---|
| S0 | Validación sin remuestrear (control de falsas alarmas) |
| S1 | Envejecimiento: pesos ∝ exp(0,05·(Age - mediana)) |
| S2 | Proporción de Germany x 2 (composición exacta) |
| S3 | IsActiveMember = 0 en el 70 % (composición exacta) |
| S4 | Tasa de abandono del 35 % por etiqueta (composición exacta) |

## PSI por variable

Estable < 0,10 · moderado 0,10-0,25 · **alerta > 0,25**. ✱ = diferencia significativa en KS/chi² con corrección de Holm (solo apoyo).

| Variable | S0 | S1 | S2 | S3 | S4 |
|---|---|---|---|---|---|
| CreditScore | 0.004 | 0.004 | 0.006 | 0.009 | 0.012 |
| Age | 0.006 | **0.327** ✱ | 0.011 | 0.024 | 0.023 ✱ |
| Balance | 0.006 | 0.008 | 0.068 ✱ | 0.013 | 0.013 |
| Tenure | 0.005 | 0.003 | 0.024 ✱ | 0.004 | 0.007 |
| NumOfProducts | 0.001 | 0.013 ✱ | 0.007 | 0.001 | 0.010 ✱ |
| HasCrCard | 0.000 | 0.001 | 0.001 | 0.003 | 0.001 |
| IsActiveMember | 0.000 | 0.009 ✱ | 0.000 | 0.196 ✱ | 0.003 |
| Geography | 0.001 | 0.002 | **0.275** ✱ | 0.001 | 0.005 |
| Probabilidad predicha | 0.000 | 0.081 | 0.055 | 0.014 | 0.039 |
| **Alarma** | no | sí | sí | no | no |

## Señales sin etiquetas y métricas con etiquetas

| Métrica | S0 | S1 | S2 | S3 | S4 |
|---|---|---|---|---|---|
| Tasa de contacto | 31.1 % | 42.2 % | 38.2 % | 34.9 % | 38.6 % |
| Probabilidad media | 20.6 % | 26.8 % | 24.5 % | 22.9 % | 25.4 % |
| Beneficio esperado (€) | 60,163 | 89,597 | 77,454 | 70,941 | 84,134 |
| Tasa de abandono observada | 20.3 % | 25.4 % | 25.2 % | 23.0 % | 35.0 % |
| Calibración global (pp) | +0.3 | +1.4 | -0.7 | -0.1 | -9.6 |
| AP | 0.696 | 0.748 | 0.723 | 0.743 | 0.833 |
| Brier (x S0) | 0.1010 (1.00) | 0.1100 (1.09) | 0.1191 (1.18) | 0.1030 (1.02) | 0.1418 (1.40) |
| Beneficio realizado modelo (€) | 61,950 | 86,800 | 82,050 | 76,700 | 122,200 |
| Beneficio contactar a todos (€) | 22,100 | 52,400 | 51,200 | 38,000 | 110,000 |
| **Degradación** | no | no | sí | no | sí |

Contactar a nadie rinde 0 € en todos los escenarios. Degradación: calibración global fuera de ±3 pp o Brier > 1,15 x S0.

## Expectativas preregistradas

| Expectativa | Resultado | Detalle |
|---|---|---|
| E1 — S0 sin alarma y sin degradación | cumplida | alarma no, degradación no |
| E2 — S1-S3: alarma en la variable desplazada y calibración dentro de ±3 pp | **no cumplida** | S1: PSI Age 0.327, calibración dentro; S2: PSI Geography 0.275, calibración dentro; S3: PSI IsActiveMember 0.196, calibración dentro |
| E3 — S4: PSI de variables ≤ 0,25 y calibración fuera de ±3 pp | cumplida | PSI máximo Age 0.023; calibración -9.6 pp |
| E4 — La tasa de contacto se aleja más de 2 pp de S0 en S1-S4 | cumplida | S1: +11.1 pp; S2: +7.2 pp; S3: +3.8 pp; S4: +7.6 pp |

## Lectura

- Las alarmas de PSI miden cambios en las entradas, no en el error del modelo. Solo las métricas con etiquetas (calibración, Brier, beneficio realizado) muestran degradación.
- El Brier depende de la mezcla de clientes: si aumenta la proporción de grupos con más abandono puede subir sin que el modelo empeore (spec 006 §4.7).
- Datos remuestreados de validación (ya usada para seleccionar y calibrar): es una simulación de mecanismos, no una estimación del comportamiento en producción.
