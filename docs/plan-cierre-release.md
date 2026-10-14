# Plan de cierre — Render, cabeceras y versión final

| Campo | Valor |
|---|---|
| Base | Rediseño publicado en `871ad5e`; compuerta previa `ca498f2` |
| Rama | `feat/dashboard-redesign`, PR #2 sobre `docs/pre-production-review` |
| Especificaciones | 007 v1.2 §10 y 006 v1.2 §13 |
| Autorización | Responsable: «okay adelante» tras el checklist de cierre |
| Estado | Enmiendas documentales en preparación, previas a implementación |

## 1. Compuerta

1. CI remoto del rediseño satisfactorio y comprobaciones locales de AGENTS §4.
2. Versionar estas enmiendas, plan y evidencia del rediseño:
   `docs: specify public dashboard headers and release closure (SDD gate)`.
3. Publicar y comprobar CI antes de implementar la solución.

## 2. Implementación acotada

- `DashboardHeaders`: middleware ASGI sin buffer, con las cinco cabeceras de
  spec 007 §10; no cambia WebSocket, lifespan ni Set-Cookie.
- `dashboard/serve.py`, API pública `st.App`, launcher Docker actualizado y
  prueba del contenido del Space; controles existentes conservados.
- Audit HTTP observa cookie de health y verifica su código, sin cuerpos/valores.
- HF alternativo solo manual; comprobar YAML/disparadores y mantener su
  autenticación por helper, sin copiar valores de secretos.
- Tests focalizados reales: transporte/middleware y auditoría; regresión de
  navegación y minimización existente; imágenes con navegador y XSRF.
- Mensaje: `fix: secure public dashboard headers and make HF deployment manual`.

## 3. Reproducibilidad

- Clon limpio temporal del commit publicado, sin CSV/modelo/venv locales.
- Los cinco comandos de AGENTS §4; considerar las omisiones reales por falta
  de datos, sin ejecutar evaluación final ni eliminar pruebas.
- Build Release en ese clon; modelo descargado y hash comprobado durante build.
- Contenedor con `ROLE=all`, API interna, `PORT=10000`, LLM 0, memoria 512 MiB
  sin swap extra y CPU 0,1. Esperar el arranque en frío; no relajar los límites
  para atribuir un resultado verde a Free.
- Health, referencia/contactar, policies congeladas, lote sintético y auditoría
  de cabeceras de dashboard. Navegador con cookies/subida/origen; OOMKilled,
  recursos y log registrado. Retirar solo contenedores temporales propios.

## 4. Publicación y Render

- Revisar commits/diffs/checks antes de publicar/fusionar. PR #1 contiene la
  base de seguridad/Render y PR #2 el rediseño y este cierre; ambos deben pasar.
- El redeploy usa el mismo servicio Free. No crear otra instancia ni recursos de
  pago. Cambiar la rama del servicio a la versión aprobada cuando corresponda.
- No hay API key/id de Render en el entorno; necesitará panel del responsable.
  Registrar commit y log de build/hash, URL y estado del servicio.
- Volver a ejecutar el comprobador contra la URL real y la comprobación funcional
  en navegador, sin asumir que el push por sí solo desplegó (Auto-Deploy Off).

## 5. Documentación, recorrido y Release

- Recorrido GIF de las vistas reales con datos sintéticos, 20–30 s, sin mensajes
  de errores, sesiones ni valores de cookies. Validar tamaño con hooks.
- Actualizar README, contexto de traspaso, criterios de specs y registro/DoD
  con los resultados realmente obtenidos, diferenciando local de público.
- Crear etiqueta/Release `v1.0.0` únicamente al cumplir la evidencia de cierre y
  CI del commit final. Si falta Render, preparar notas y registrar la tarea pendiente.
