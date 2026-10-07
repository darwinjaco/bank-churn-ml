---
title: Bank Churn Retention
emoji: 🏦
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
pinned: false
license: mit
short_description: Churn probability turned into retention decisions in euros
---

# Abandono bancario → decisiones de retención

Demo del proyecto [darwinjaco/bank-churn-ml](https://github.com/darwinjaco/bank-churn-ml): un Random Forest calibrado estima la probabilidad de abandono de un cliente y la regla de beneficio esperado decide si conviene contactarlo (umbral 1/6).

- Pestañas: cliente individual con razones SHAP, lote desde CSV y métricas de la evaluación final.
- El modelo (`model-v1.0`) se descarga del GitHub Release y se verifica por SHA-256 durante el build.
- Datos públicos de Kaggle, probablemente sintéticos; supuestos económicos ilustrativos. **No es asesoría financiera.**
- El Space gratuito se suspende tras un periodo sin uso: el primer acceso puede tardar un minuto.

Código, especificaciones y ficha del modelo en el repositorio de GitHub.
