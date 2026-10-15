# Escaneos CI y comprobación pública

Especificación: [007 §9](../specs/007-security-hardening.md#9-enmienda-v11--escaneos-y-verificación-pública).
Plan: [escaneos de seguridad](plan-escaneos-seguridad.md). Compuerta: `40127be`.

## Escaneos automatizados

`.github/workflows/security.yml` ejecuta dos jobs independientes en pull requests,
push a `main` o manualmente:

- **Dependencias:** exporta el lock completo con hashes a un archivo temporal;
  `pip-audit==2.10.1` funciona en un entorno de herramienta separado. No instala
  el proyecto, no resuelve sus dependencias ni aplica `--fix`. El resultado
  corresponde al Python 3.11 y plataforma del job, no a todas las combinaciones
  posibles del lockfile.
- **Secretos:** Gitleaks v8.30.1, binario oficial con SHA-256 comprobado e
  historial completo. Se exige redacción total; el artifact final conserva
  únicamente regla, ruta, línea y commit. No se sube el informe crudo.

Los jobs fallan si detectan hallazgos o si el análisis no puede completarse.
No hay `continue-on-error`, exclusiones de hallazgos ni actualizaciones automáticas.
Una excepción necesita evidencia y decisión versionada. Los artifacts duran
7 días y las Actions están fijadas por SHA.

## Comprobación pública manual

Cuando el responsable disponga de la URL raíz de Render:

```powershell
uv run python scripts/verify_public_security.py --url https://TU-DEMO.onrender.com
```

El script hace peticiones sin credenciales, no lee cuerpos de respuesta ni
envía datos de clientes, archivos o inferencia. Comprueba:

1. Conexión HTTPS con validación normal del certificado y redirección desde HTTP.
2. Cabeceras del **dashboard público**, distintas de las de la API interna:
   `nosniff`, política de referencia, HSTS y un control limitado de framing.
   No certifica toda la CSP.
3. Health HTTP 200 y cookie XSRF observada en raíz, host-config o health: informa solo nombre y atributos,
   nunca valor. `SameSite=None` requiere `Secure`; `HttpOnly` no se exige al
   token que el frontend necesita leer.
4. Handshake WebSocket: origen propio aceptado y origen ajeno rechazado. No
   envía mensajes de aplicación; un 403 general sin aceptación del origen propio
   no demuestra que el control CORS esté bien configurado.

Códigos: **0** = controles comprobados satisfactorios; **1** = fallo comprobado;
**2** = evidencia incompleta, ausencia de URL o problema de red/TLS. Sin URL
se devuelve `not_verified`, sin hacer peticiones.

Render documenta TLS y redirección automáticos, pero eso no es evidencia de
esta demo hasta comprobar su URL. Sus arranques en frío pueden requerir esperar
y repetir la comprobación. Subida con XSRF e iframe requieren además un navegador.

## Evidencia

Consultar S16–S18 de [registro-avance.md](registro-avance.md). En la URL real
https://bank-churn-ml-ufa7.onrender.com/ se comprobó el 14 de octubre de 2026:

- TLS y redirección HTTPS satisfactorios; WebSocket propio 101 y ajeno 403.
- Cabeceras `X-Content-Type-Options`, `Referrer-Policy` y HSTS ausentes; framing
  no verificado. El comprobador HTTP devuelve **código 1**, no una auditoría verde.
- El comprobador HTTP no observó cookie; un navegador Edge real sí observó
  `_streamlit_xsrf` con SameSite Lax, Secure falso y HttpOnly falso, sin publicar
  valores. Subida válida HTTP 204; sin token XSRF, HTTP 403.
- Referencia, CSV sintético, Modelo y Monitoreo funcionales en navegador.
  No se probó iframe ni se declara validada toda la CSP.

Los tests con respuestas sintéticas no se presentan como verificación pública,
y un resultado de auditoría local no sustituye la ejecución remota del workflow.
La remediación de cabeceras requiere una decisión versionada antes de implementarla.

La enmienda 007 v1.2 versionó la solución nativa mediante `st.App` y middleware.
Cabeceras, cookie de health, origen propio/ajeno y subida con/sin token comprobados
en el launcher local; el cierre posterior en Render se documenta debajo.

S23 repite la auditoría: cabeceras aún ausentes (código 1) y algunos intentos
incompletos por timeout de lectura (código 2). El navegador sigue mostrando la
interfaz anterior, con pestañas y botón «Evaluar». El estado Live informado no
basta para identificar el código servido. El responsable pospone la revisión
del panel; no se certifica la actualización HTTPS ni el cierre de la Release.

### Cierre verificado de v1.0.1

El 15 de octubre se comprobó el deploy Live de `9384e51` en el servicio existente.
El script público terminó con **código 0 / passed**: TLS, redirección, cabeceras,
framing, health, cookie y orígenes correctos. Edge completó doce controles de
interfaz sin errores de consola. Una prueba HTTPS adicional comprobó plantilla,
subida válida 204 y subida sin token 403.

Los fallos y pausas de S18–S24 son evidencia histórica. Quedan superados por el
informe final de la [Release v1.0.1](https://github.com/darwinjaco/bank-churn-ml/releases/tag/v1.0.1),
que contiene `verification-v1.0.1.json`. La CSP se evalúa solo respecto al framing;
no se certifican iframe externo, WCAG completa ni capacidad de producción.
