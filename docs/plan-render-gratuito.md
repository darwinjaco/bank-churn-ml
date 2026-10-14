# Plan de despliegue gratuito — Render

| Campo | Valor |
|---|---|
| Base publicada | `3419a65`, CI remoto en verde |
| Autorización | Responsable: «si es gratis vamos»; está creando su cuenta Render |
| Estado | Diseño y Blueprint propuestos; pendientes de versionar la enmienda antes de aplicar configuración |
| Especificación | Borrador de enmienda v1.1 de la spec 006, §12 |

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

## 2. Blueprint propuesto

Después de versionar especificación y plan, guardar esta configuración como
`render.yaml` en la raíz. Render usa BuildKit; el Dockerfile actual ya se ha
verificado con su variante `release` sin contexto local del modelo.

```yaml
services:
  - type: web
    name: bank-churn-ml
    runtime: docker
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

1. Confirmar que la cuenta Hobby está conectada a GitHub y completar su acceso.
2. Versionar la enmienda v1.1 de la spec 006 y este plan, con CI previo verde y
   las comprobaciones requeridas. No modificar `src/`, tests o dependencias
   para recuperar la antigua preparación de Render sin esa compuerta.
3. Añadir `render.yaml`, validar contra el esquema oficial y comprobar la rama
   publicada antes de crear el Blueprint. Mantener `plan: free` y cero recursos
   adicionales facturables.
4. Crear el servicio desde el panel de Render y esperar un build correcto.
   No sustituir el modelo ni el hash si el build falla.
5. Registrar la URL asignada, probar health, interfaz Cliente (0,947 y contactar),
   CSV sintético, modelo y monitoreo, incluidos errores y XSRF bajo HTTPS.
6. Actualizar README y criterios solo con la evidencia pública obtenida.

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
