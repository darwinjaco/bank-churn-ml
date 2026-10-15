# Plan — Cobertura completa de sentencias

Especificación: [008](../specs/008-complete-statement-coverage.md).
El responsable autoriza dos commits como excepción a los cierres documentales
anteriores de commit único. Trabajo sobre `main`, sin mover etiquetas de Release.

## T0 — Compuerta

- Leer implementación/tests y medir cobertura: base 6487997, 322 aprobados,
  43/2.376 sentencias ausentes, cobertura 98,19 %.
- Especificación 008, este plan y registro S26; cinco comandos de AGENTS,
  hooks nuevos y CI previo verde. Commit y push del diseño; esperar CI.
- Mensaje: `docs: specify complete statement coverage (SDD gate)`.

## T1 — Tests después de la compuerta

- Extender archivos existentes según spec 008 §3; lanzadores parametrizados en
  `tests/test_cli_entrypoints.py` si conviene centralizar su aislamiento.
- Aislar raíz, argv, rutas, variables de entorno y tracking. Mantener mensajes y
  códigos de error comprobables, referencias sintéticas y relaciones numéricas.
- Probar rutas alternativas de selección con resultados CV sintéticos fijados,
  verificando exclusiones, familia y decisión; no nuevas búsquedas reales.
- Pruebas dirigidas, Ruff/formato, después suite completa al 100 %. Sin cambios
  de implementación, dependencias o configuración de exclusiones de cobertura.

## T2 — Reproducibilidad y publicación

- Cinco comandos exactos de AGENTS y hooks nuevos, más suite estricta al 100 %.
- Preparar copia temporal limpia del Git publicado con el diff de tests previsto,
  sin CSV/modelo/MLflow locales. Ejecutar suite estricta; tres skips esperados.
- Actualizar el registro con resultados realmente observados y límites. Mantener
  cifras históricas de la memoria v1.0.1 como evidencia de aquella entrega.
- Commit de tests y evidencia solo con CI previo verde; push y comprobar workflows.
- Mensaje: `test: cover remaining statements with isolated regression cases`.
- La confirmación posterior del CI se registra en el comentario del commit y
  respuesta final, sin crear un tercer commit solo para incluir su propio hash.
