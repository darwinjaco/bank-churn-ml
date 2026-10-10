# Plan — Correcciones de seguridad

Base: `a2598ee`. Especificación: [007 v1.0](../specs/007-security-hardening.md).
El responsable aprobó el perfil de límites y aparcar únicamente la preparación
de Render. No ejecutar el modelo sobre la partición de prueba real.

| Paso | Entregable | Verificación |
|---|---|---|
| T0 | Spec 007, enmiendas relacionadas y registro S14; commit previo | CI base en verde y comprobaciones de AGENTS §4 |
| T1 | CSV acotado y exportación minimizada; texto LLM literal; errores redactados | Casos adversarios sintéticos y regresiones del contrato |
| T2 | Carga verificada en CLI; reportes sin identificadores | Rechazo antes de deserializar; métricas congeladas intactas |
| T3 | Límites de cuerpo, frecuencia y concurrencia; cuota LLM SQLite | Límites exactos, ventanas y concurrencia, fallo cerrado |
| T4 | XSRF/CORS, puertos locales, exclusiones, permisos, autenticación Git y referencias inmutables | Configuración, tests pertinentes y validación Docker disponible |
| T5 | Documentación y registro final | Suite completa, cobertura ≥ 85 %, lista de pendientes externos |

Versionar T0 antes de editar `src/`, tests o dependencias. La preparación
`render-prep` permanece guardada; al recuperarla habrá que resolver sus conflictos
con las correcciones de seguridad y aprobar la enmienda correspondiente.
