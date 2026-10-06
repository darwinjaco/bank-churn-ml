# EDA e hipótesis preregistradas — Semana 2

## Protocolo y muestra

- Especificación 003 v1.0 preregistrada en `678004d`; enmienda v1.1 en `9e043df`, antes de observar los contrastes reales. H1–H6, direcciones y umbrales permanecieron sin cambios.
- Fuente numérica de H1–H6: [hypotheses.json](hypotheses.json); revisión estratificada calculada con el código de [Exploratorio](#exploratorio). División reproducible: [split_manifest.json](split_manifest.json), semilla 42 y scikit-learn 1.9.1.
- Muestra analítica: **8.000 clientes**, entrenamiento (6.000) y validación (2.000); 1.630 abandonos, tasa del 20,375 %. La partición de prueba no se carga para EDA ni contrastes.
- α = 0,05, bilateral; Holm exclusivamente sobre H1–H5. H6 se evalúa por equivalencia del IC de AUC dentro de [0,45; 0,55], con 2.000 réplicas bootstrap y semilla 42.
- H1/H2/H5 utilizaron Pearson sin Yates. La frecuencia esperada mínima de H2 es 52,36; el fallback exacto de Freeman–Halton no fue necesario en los contrastes reales, pero pasa sus tests de referencia.
- Los intervalos son del 95 %. Los resultados expresan asociaciones en este dataset y no efectos causales de campañas o cambios de comportamiento.

## Tabla confirmatoria

DR significa diferencia de riesgo; **pp** son puntos porcentuales. En H2 los IC corresponden a las tasas por nivel, no a V de Cramér. El pico de H4 es una estimación puntual; su IC no fue preregistrado.

En esta tabla, los p-valores menores a 10⁻¹⁰ se muestran como «< 10⁻¹⁰»; los valores completos se conservan en `hypotheses.json`.

| Hipótesis | Efecto | IC 95 % | p Holm | Prueba usada | Veredicto |
|---|---|---|---|---|---|
| H1: inactivos abandonan más | DR +12,27 pp; OR 2,1610 | DR [10,51; 14,03] pp; OR [1,9314; 2,4178] | < 10⁻¹⁰ | Pearson 2×2 sin Yates | Confirmada |
| H2: tasa(2) < tasa(1) < tasa(3–4) | V = 0,3875; tasas 7,38 % < 27,98 % < 85,60 % | Nivel 2 [6,58; 8,27] %; nivel 1 [26,62; 29,38] %; nivel 3–4 [80,79; 89,37] % | < 10⁻¹⁰ | Pearson 3×2 sin Yates | Confirmada |
| H3: asociación de Alemania ajustada por saldo | OR ajustado 2,1787; OR crudo 2,5688 | Ajustado [1,9133; 2,4809]; crudo [2,2881; 2,8840] | < 10⁻¹⁰ | Wald del coeficiente `is_germany` en Logit | Confirmada |
| H4: edad con U invertida | β cuadrático = −0,003429; pico 56,58 años | β [−0,003855; −0,003002] | < 10⁻¹⁰ | Razón de verosimilitud, modelos Logit anidados | Confirmada |
| H5: saldo cero asociado a menos abandono | DR −10,62 pp | DR [−12,31; −8,88] pp | < 10⁻¹⁰ | Pearson 2×2 sin Yates | Confirmada |
| H6: AUC de salario sin señal útil según el margen fijado | AUC = 0,5146 | [0,4997; 0,5306], dentro de [0,45; 0,55] | No aplica | Equivalencia por IC bootstrap percentil | Confirmada |

### Una conclusión por hipótesis

- **H1:** la tasa de los inactivos es 12,27 pp mayor y su IC supera los 5 pp preregistrados.
- **H2:** las tasas de 2, 1 y 3–4 productos siguen el orden fijado y sus IC no se solapan; el grupo 3–4 contiene solo 257 clientes.
- **H3:** Alemania mantiene una asociación con mayores odds de abandono tras ajustar por saldo; el log-OR se atenúa un 17,46 % y el IC del OR ajustado queda por encima de 1,5.
- **H4:** el coeficiente cuadrático y todo su IC son negativos, con máximo estimado a los 56,58 años dentro del rango preregistrado.
- **H5:** quienes tienen saldo cero presentan 13,59 % de abandono frente al 24,21 % con saldo positivo; el IC de la DR queda por debajo de −5 pp; asociación parcialmente confundida con `Geography`, ver Exploratorio.
- **H6:** el IC de AUC del salario bruto queda dentro del margen de equivalencia; esto no demuestra independencia ni inutilidad en interacciones o transformaciones.

## Exploratorio

Estos análisis secundarios son descriptivos, no pertenecen a la familia Holm y no reciben un veredicto confirmatorio:

- **Saldo positivo:** Mann–Whitney entre abandonos y permanencias, U = 2.433.321,5, p crudo = 0,3941 y AUC = 0,5080. El contraste usa 1.237 abandonos y 3.872 permanencias; no aporta evidencia descriptiva clara de ordenamiento por saldo dentro de este grupo.
- **Distribución salarial:** KS frente a uniforme en [11,58; 199.992,48], D = 0,00829 y p crudo = 0,6388. Los límites se estimaron de la muestra; ese p no valida una hipótesis confirmatoria de uniformidad ni prueba origen sintético.
- **Masa en cero:** 2.891 de 8.000 clientes (36,14 %) tienen saldo cero. Es una propiedad descriptiva de la muestra de exploración, distinta del 36,17 % del reporte global de semana 1.
- **Soporte de H3:** Alemania no tiene clientes con `Balance = 0` (0/2.005). La comparación ajustada de Alemania tiene soporte común solo en clientes con saldo > 0: Alemania 33,1 % (663/2.005) frente a 18,5 % (574/3.104) en Francia + España. No hay observaciones alemanas para contrastar la asociación con saldo cero.
- **H5 estratificada sin Alemania:** en Francia + España, saldo cero 13,6 % (393/2.891) frente a saldo positivo 18,5 % (574/3.104), DR = −4,8984 pp, aproximadamente −4,9 pp. Parte de la asociación cruda de H5 refleja la composición geográfica; el veredicto preregistrado se mantiene, pero la DR observada dentro de este estrato es menor y queda cerca del umbral práctico de 5 pp. Esta comparación descriptiva no estima un efecto causal atribuible al saldo.

### Código reproducible de la revisión por geografía y saldo

Las cifras de los dos puntos anteriores se calcularon ejecutando este código con `load_exploration()`, sin consultar prueba ni modificar el JSON confirmatorio:

```python
from churn.split import load_exploration

df = load_exploration()
germany = df["Geography"].eq("Germany")
rest = df["Geography"].isin(["France", "Spain"])
zero = df["Balance"].eq(0)
masks = {
    "germany_zero": germany & zero,
    "germany_positive": germany & ~zero,
    "rest_zero": rest & zero,
    "rest_positive": rest & ~zero,
}
summary = {}
for name, mask in masks.items():
    y = df.loc[mask, "Exited"]
    summary[name] = {
        "n": len(y),
        "k": int(y.sum()),
        "rate": float(y.mean()) if len(y) else None,
    }
summary["germany_total"] = int(germany.sum())
summary["dr_rest_pp"] = 100 * (summary["rest_zero"]["rate"] - summary["rest_positive"]["rate"])
print(summary)
```

| Segmento derivado del código | Clientes | Abandonos | Tasa |
|---|---|---|---|
| Alemania, saldo cero | 0 | 0 | No definida |
| Alemania, saldo positivo | 2.005 | 663 | 33,0673 % |
| Francia + España, saldo cero | 2.891 | 393 | 13,5939 % |
| Francia + España, saldo positivo | 3.104 | 574 | 18,4923 % |

La falta de clientes alemanes con saldo cero motiva documentar un posible artefacto de generación y la señal compartida entre `has_balance` y `Geography`. En la interpretación de modelos se reportará SHAP de ambas variables en conjunto y no se interpretarán sus coeficientes por separado en la semana 3.

## Implicaciones para la semana 3

La selección de variables se decidirá mediante validación cruzada de entrenamiento, según la especificación 002, después de la revisión de esta semana.

| Elemento ya previsto | Evidencia y consecuencia para su evaluación |
|---|---|
| `has_balance` | H5 y la masa en cero justifican evaluar el indicador de saldo positivo ya propuesto, además del saldo continuo |
| `age_band` | H4 justifica evaluar la representación no lineal ya prevista; los tramos y límites permanecen fijados en `config.py` |
| `balance_to_salary` | Los contrastes actuales no justifican por sí solos esta razón; conserva su condición de candidata pendiente de CV, sin incorporación automática |
| E-02: ablación de `NumOfProducts` | H2 refuerza la prioridad de la auditoría prevista: comparar el modelo con/sin la variable y reportar resultados separados para el grupo 3–4, con su tamaño e incertidumbre |
| E-03: ablación de `EstimatedSalary` | H6 respalda ejecutar la comparación prevista sin salario ni sus derivadas, incluida `balance_to_salary`; no autoriza excluirlo por AUC univariada únicamente |

No se añaden variables ni se cambia la regla de selección del modelo. El valor económico del cliente y los costos de campaña siguen siendo supuestos de la futura especificación 004.

## Artefactos y reproducibilidad

```powershell
uv sync --locked --all-groups
uv run churn-split
uv run churn-hypotheses
uv run --group eda python -m churn.plots
uv run pytest --cov=churn --cov-report=term-missing --cov-fail-under=85
```

- [Notebook](../notebooks/01_eda.ipynb): descriptivos, reporte e imágenes, sin funciones propias ni salidas versionadas.
- [Figuras](figures/): seis PNG menores de 200 KB; la figura de productos mantiene el grupo 3–4 de H2.
- [CI técnico verificado](https://github.com/darwinjaco/bank-churn-ml/actions/runs/37487169164): 69 aprobados, 2 omitidos por ausencia del CSV y cobertura del 98,05 %.
- Comprobación local con CSV: 71 aprobados y cobertura del 98,48 %, incluida correspondencia del manifiesto real.

**Límites:** observaciones transversales, ausencia de datos de tratamiento, posible origen sintético sin confirmación de procedencia y exploración global agregada ya realizada en semana 1. Confirmar H1–H6 bajo el protocolo no garantiza utilidad predictiva, equidad ni beneficio económico.
