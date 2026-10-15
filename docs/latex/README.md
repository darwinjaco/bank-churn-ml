# Memoria técnica en LaTeX

Documento principal: [`memoria-tecnica.tex`](memoria-tecnica.tex).
Versión descrita: **v1.0.1**, código **9384e51**, con evidencia publicada el
15 de octubre de 2026. La memoria es posterior a esa entrega y no modifica
modelo, métricas, dependencias ni particiones.

## Contenido

Portada, resumen, índices, gobierno SDD, datos/contrato, H1–H6, pipelines,
baselines, selección RF/XGBoost/LogReg, experimentos E-01–E-04, calibración,
derivación económica, prueba única, SHAP/equidad, monitoreo, arquitectura,
API/dashboard, seguridad, Docker/Render, reproducibilidad, operación,
conclusiones, ejemplos y fuentes.

Las cifras proceden de `reports/` y la Release; las figuras se incluyen desde
`../../reports/figures/`. No se necesitan el CSV, el modelo ni MLflow para compilar.

Validación del 15 de octubre de 2026: **34 páginas**, 14 tablas, cuatro figuras
y un diagrama; 55 marcadores y 79 enlaces internos comprobados. Compilación final
sin advertencias LaTeX, referencias indefinidas ni desbordamientos. El PDF tiene
300.268 bytes; su tamaño puede variar con otras versiones del compilador.

## Compilar con Tectonic

Requisito externo: [Tectonic](https://tectonic-typesetting.github.io/).
La validación de esta memoria utiliza **0.17.0**; no es una dependencia Python
del proyecto. La primera compilación descarga los recursos TeX necesarios.

Abre una terminal **en `docs/latex/`** y ejecuta:

```powershell
New-Item -ItemType Directory -Force build
tectonic --keep-logs --outdir build memoria-tecnica.tex
```

Tectonic repite las pasadas necesarias para resolver índices y referencias.
Si el ejecutable es portátil, utiliza su ruta con el operador `&` de PowerShell.

**PDF resultante:** `docs/latex/build/memoria-tecnica.pdf`.
El directorio `build/` está excluido de Git: conserva el PDF local y los logs,
sin añadirlos al repositorio. El archivo fuente y las instrucciones sí forman
parte de la documentación propuesta para versionar.

## Alternativa con una distribución TeX

Desde el mismo directorio, con `latexmk` y pdfLaTeX instalados:

```powershell
latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=build memoria-tecnica.tex
```

Se utilizan paquetes habituales de TeX Live/MiKTeX: Babel español, Latin Modern,
AMS, geometry, microtype, booktabs, longtable, tabularx, graphicx, enumitem,
listings, TikZ, fancyhdr, xurl, hyperref y bookmark. No requiere shell escape,
PythonTeX, minted ni scripts que ejecuten experimentos. Esta alternativa se
documenta para portabilidad; la comprobación ejecutada usa Tectonic.

## Fuentes y alcance de las afirmaciones

- `reports/final_test.json`: única evaluación final; no volver a ejecutarla.
- Resto de reportes: métricas de desarrollo, auditoría o simulación, identificadas.
- [Release v1.0.1](https://github.com/darwinjaco/bank-churn-ml/releases/tag/v1.0.1):
  cierre de CI, integración y comprobación pública, con informe JSON descargable.
- `docs/registro-avance.md`, S25: compilación y revisión de esta memoria.

El PDF no certifica capacidad de producción, efectos causales ni equidad por
el mero hecho de excluir `Gender`. Conserva las limitaciones del proyecto y
no presenta los supuestos económicos como resultados de una campaña real.
