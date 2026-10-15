# Plan de cierre — Render, cabeceras y versión final

| Campo | Valor |
|---|---|
| Base | Rediseño publicado en `871ad5e`; compuerta previa `ca498f2` |
| Rama | `feat/dashboard-redesign`, PR #2 sobre `docs/pre-production-review` |
| Especificaciones | 007 v1.2 §10 y 006 v1.2 §13 |
| Autorización | Responsable: «okay adelante» tras el checklist de cierre |
| Estado | Cierre local comprobado; el responsable autoriza commit único e integración GitHub primero; Release condicionada al redeploy de main |

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

## 6. Cierre consolidado autorizado — 14 de octubre de 2026

El responsable solicita conservar los cambios en local y crear **un solo commit
al terminar**, seguido de la integración si no hay conflictos y las comprobaciones
son satisfactorias. Se conserva Hugging Face como alternativa manual.

- Alcance: documentación, recorrido animado y retirada de `notebooks/.gitkeep`,
  redundante porque el notebook existe. No se modifica `src/`, `tests/` ni
  dependencias; no hace falta introducir otra compuerta de implementación.
- Conservar datos, modelo, MLflow, configuración personal y planes históricos.
  Cachés y temporales propios se retiran al finalizar las comprobaciones y después
  de conservar la evidencia. No ejecutar una limpieza indiscriminada de ignorados.
- El stash `render-prep` contiene una propuesta antigua de Dockerfile derivado,
  reintentos de API y tests; se comparó y se conserva como trabajo aparcado.
  Su contenido no se aplica automáticamente al rediseño actual.
- Reproducibilidad: registrar los resultados previos del clon limpio `bacb47b`
  y repetir Compose desde ese clon para cerrar literalmente spec 005 §9.
- Revisar los PR completos y verificar la cadena de ancestros. Integración
  propuesta: `feat/dashboard-redesign` → `docs/pre-production-review` → `main`
  mediante `--ff-only`, con CI verde antes de avanzar cada base. Sin force push
  ni commits adicionales de fusión. Si falla la condición, detenerse y consultar.
- Render: el responsable confirma que hará el redeploy manual de `bacb47b`;
  se exige la comprobación HTTPS y funcional real antes de atribuir un cierre.
  Después de integrar se configura `main` como rama del servicio y se comprueba
  el commit final desplegado. Un push no sustituye el redeploy.
- La etiqueta `v1.0.0` ya fue publicada prematuramente en `bacb47b`. El responsable
  autoriza **`v1.0.1`** para la entrega final. Conservar esa etiqueta anterior y
  `model-v1.0`; no cambiar el paquete ni las dependencias por un cierre documental.
  Preparar notas y publicar la nueva Release solo tras cumplir su evidencia.
- El único commit agrupa la limpieza, el GIF, los estados y el registro. El CI
  del propio commit y las acciones posteriores se enlazan en la Release y en el
  informe final, sin crear otro commit exclusivamente para escribir su hash.

### Pausa por despliegue no confirmado

La inspección independiente sigue mostrando la interfaz anterior aunque el
responsable indicó Live. Se necesita confirmar hash del deploy, rama y ruta de
Dockerfile en el panel. El responsable elige dejarlo pendiente: los cambios y
resultados quedan locales, sin commit nuevo, integración ni Release. No se
descartan los entornos/datos necesarios para retomar la comprobación.

### Reanudación autorizada — GitHub primero

El responsable solicita terminar y, ante la evidencia de que Render aún sirve
la interfaz anterior, elige **«Integrar GitHub primero»**. Esta decisión sustituye
la pausa de commit/fusiones: se permite crear el único commit de limpieza/documentación,
publicarlo y avanzar las bases con CI satisfactorio. No cambia la condición de
la Release: esperar el redeploy de `main` y comprobar la URL real.

La evidencia posterior al commit (su hash, ejecuciones de CI, PR integrados y
deploy) se publica en los PR y, al satisfacer el despliegue, en las notas de
`v1.0.1`. El registro versionado es el snapshot previo a esas acciones; no se
crea un segundo commit para actualizar resultados que solo existen después.
