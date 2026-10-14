# Plan de despliegue gratuito — Render

| Campo | Valor |
|---|---|
| Base publicada | `193a13d`, configuración de Render; CI y Security scans remotos en verde; diseño previo en `40f913f` |
| Autorización | Responsable: «si es gratis vamos» y «adelante modifica lo necesario»; formulario manual preparado en Render |
| Estado | Demo pública funcional verificada (S18); cabeceras/framing y evidencia del build pendientes |
| URL real | https://bank-churn-ml-ufa7.onrender.com/ |
| Especificación | Enmienda v1.1 de la spec 006, §12 |

## 1. Recursos y límites

Usar **Hobby + un Web Service `free`**: 512 MB y 0,1 CPU. El presupuesto de
750 horas mensuales es compartido por todos los servicios gratuitos del workspace.
Una sola instancia evita duplicarlo. Render suspende servicios sin tráfico tras
15 minutos; el arranque posterior puede ser lento.

No crear servicios de pago, discos, bases de datos ni claves de proveedor LLM.
La demo empieza con plantilla (`LLM_MAX_CALLS_PER_HOUR=0`): Render Free pierde
el SQLite local al reiniciar o suspender, por lo que no se puede prometer una cuota
persistente de LLM en esa plataforma. Los controles restantes de la spec 007
siguen activos. No recuperar automáticamente el stash `render-prep`.

## 2. Blueprint

La especificación y el plan previos están versionados en `40f913f`.
La configuración se guarda como `render.yaml` en la raíz. Render usa BuildKit;
el Dockerfile actual ya se ha
verificado con su variante `release` sin contexto local del modelo.

```yaml
services:
  - type: web
    name: bank-churn-ml
    runtime: docker
    region: virginia
    plan: free
    numInstances: 1
    dockerfilePath: ./Dockerfile
    dockerContext: .
    autoDeployTrigger: 'off'
    healthCheckPath: /_stcore/health
    envVars:
      - key: ROLE
        value: all
      - key: PORT
        value: '10000'
      - key: API_URL
        value: http://127.0.0.1:8000
      - key: LLM_MAX_CALLS_PER_HOUR
        value: '0'
      - key: STREAMLIT_BROWSER_SERVER_ADDRESS
        fromService:
          name: bank-churn-ml
          type: web
          envVarKey: RENDER_EXTERNAL_HOSTNAME
```

`plan: free` debe figurar explícitamente: omitirlo selecciona un plan de pago.
No fijar `branch`: el Blueprint utilizará su propia rama, evitando desplegar
`main` antes de que contenga las correcciones. El despliegue automático permanece
desactivado; seleccionar manualmente un commit con CI satisfactorio.

## 3. Orden de trabajo y compuerta

1. Cuenta conectada y formulario preparado según las capturas del responsable;
   verificar Hobby y mantener el compute Free seleccionado.
2. Diseño y plan previos versionados en `40f913f`, con CI y Security scans
   satisfactorios. La preparación usa esa compuerta y el Dockerfile existente.
3. Añadir `render.yaml`, validar contra el esquema oficial, publicar los cambios
   con autorización del responsable y comprobar el CI del commit. Mantener
   `plan: free` y cero recursos adicionales facturables.
4. Crear el servicio desde el panel de Render y esperar un build correcto.
   No sustituir el modelo ni el hash si el build falla.
5. Registrar la URL asignada, probar health, interfaz Cliente (0,947 y contactar),
   CSV sintético, modelo y monitoreo, incluidos errores y XSRF bajo HTTPS.
6. Actualizar README y criterios solo con la evidencia pública obtenida.

### 3.1 Formulario manual preparado por el responsable

Crear el servicio desde el formulario es equivalente a aplicar estos valores;
Render no importa `render.yaml` automáticamente en ese flujo. No crear un
segundo servicio mediante Blueprint después de crear el primero manualmente.

| Campo | Valor |
|---|---|
| Name / Language | `bank-churn-ml` / Docker |
| Branch | `docs/pre-production-review`, hasta fusionar las correcciones |
| Region / Compute | Virginia / Free ($0, 512 MB, 0,1 CPU) |
| Root Directory | Vacío |
| Docker Build Context Directory / Dockerfile Path | `.` / `Dockerfile` |
| Health Check Path | `/_stcore/health` |
| Docker Command / Pre-Deploy Command | Vacíos: usar el CMD de la imagen |
| Registry Credential / Auto-Deploy | No credential / Off |
| `ROLE` | `all` |
| `PORT` | `10000` |
| `API_URL` | `http://127.0.0.1:8000` |
| `LLM_MAX_CALLS_PER_HOUR` | `0` |

Tras asignarse la URL, añadir `STREAMLIT_BROWSER_SERVER_ADDRESS` con su hostname
exacto (por ejemplo, `nombre-asignado.onrender.com`, sin protocolo ni `/`). En el
Blueprint se resuelve mediante la autorreferencia documentada por Render; en el
formulario manual no dejarlo vacío ni pegar `${RENDER_EXTERNAL_HOSTNAME}`.
Guardar y redesplegar si es necesario, y después verificar HTTPS y XSRF.

El botón **Deploy web service** inicia la creación y el build. No constituye por
sí solo el cierre: esperar estado Live y registrar las comprobaciones públicas.

### 3.2 Resultado público — 14 de octubre de 2026

URL facilitada por el responsable: https://bank-churn-ml-ufa7.onrender.com/.
Health `ok`, referencia 0,947/contactar/plantilla, lote sintético de 20 clientes,
Modelo y Monitoreo comprobados en navegador. Subida válida HTTP 204 y subida
sin token XSRF rechazada HTTP 403. Origen WebSocket propio 101, ajeno 403.

La auditoría HTTP devuelve código 1: faltan `X-Content-Type-Options`,
`Referrer-Policy` y HSTS; framing no verificado. La cookie que el script HTTP
no observó sí aparece en navegador como `_streamlit_xsrf`, SameSite Lax,
sin Secure ni HttpOnly (no se imprimieron valores). No hay iframe probado.

Antes de modificar proxy, cabeceras o arranque se requiere aprobar y versionar
la solución, conforme a spec 007 §9.2. El hostname efectivo, commit del build,
SHA-256 registrado en el build y estado del panel requieren evidencia de Render;
no se deducen del HTML público. Detalle en S18 del registro.

## 4. Evidencia local y límites de la prueba

La imagen con modelo descargado del Release pasó la prueba con
`--memory=512m --memory-swap=512m --cpus=0.1`: health del dashboard, referencia,
plantilla y lote sintético de 1.000 clientes correctos, `OOMKilled=false`.
Memoria de trabajo observada: 409,8 MiB. Cgroup incluida caché llegó a 512 MiB.
No es una prueba completa de interfaz bajo carga ni garantía de rendimiento en
Render; esa comprobación requiere la cuenta y el servicio desplegado.

## 5. Fuentes oficiales consultadas

- [Plan gratuito y sus límites](https://render.com/docs/free).
- [Tarifas: distinguir workspace Hobby de compute Free](https://render.com/pricing).
- [Docker y BuildKit](https://render.com/docs/docker).
- [Campos de Blueprint](https://render.com/docs/blueprint-spec).
- [Esquema oficial de validación](https://render.com/schema/render.yaml.json).
