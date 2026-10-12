# Plan — Escaneos CI y comprobación de seguridad pública

Base: `3419a65`, CI remoto en verde. Especificación: enmienda v1.1 aprobada de
[spec 007 §9](../specs/007-security-hardening.md#9-enmienda-v11--escaneos-y-verificación-pública).

| Paso | Entregable | Evidencia |
|---|---|---|
| T0 | Enmienda y este plan, versionados antes de código o tests | CI previo y comprobaciones AGENTS §4 |
| T1 | Workflow separado con escaneo de dependencias y secretos | Herramientas aisladas/pinadas, requisitos exportados del lock e historial completo |
| T2 | Informes minimizados y comportamiento sin falsos verdes | Tests sintéticos y escaneos reales; ninguna actualización de dependencias |
| T3 | Comprobación manual de HTTPS, cabeceras, cookies y rechazo de origen | Pruebas sintéticas del evaluador; evidencia real únicamente con URL pública |
| T4 | Registro de avance y documentación de uso | Resultados locales separados de CI remoto y verificación pública |

Si aparece un hallazgo, registrar su alcance y detener la remediación de
dependencias/modelo hasta aprobar su enmienda. No silenciar fallos del escáner.
La preparación de Render continúa en su propio plan y el stash se conserva.
