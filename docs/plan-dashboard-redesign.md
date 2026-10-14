# Plan — Rediseño profesional del dashboard Streamlit

| Campo | Valor |
|---|---|
| Especificación | Spec 005 v1.3 §12, dependiente de 006 y 007 |
| Rama | `feat/dashboard-redesign`, desde `d9b0f85` de `docs/pre-production-review` |
| Autorización | Responsable: aplicar las mejoras en una rama para ver el resultado, incluir gráficos y «Adelamte» |
| Estado | Compuerta documental en preparación |

## 1. Objetivo y dirección visual

Herramienta de retención bancaria que permite entender una decisión y explorar
su evidencia. El responsable aceptó la propuesta de estilo claro con azul.
Primero claridad de acción, después evidencia y método. No es una landing page:
evitar grandes héroes, sombras/degradados decorativos y tarjetas indistinguibles.

Se aplican las instrucciones revisadas de
[frontend-design](https://github.com/anthropics/skills/tree/main/skills/frontend-design)
y [web-design-guidelines](https://github.com/vercel-labs/agent-skills/tree/main/skills/web-design-guidelines),
incluida su [fuente de reglas](https://github.com/vercel-labs/web-interface-guidelines/blob/main/command.md).
Estas instrucciones guían el trabajo; no se instalan paquetes de frontend ni se
modifican las dependencias Python. Se adaptan al español y a controles Streamlit.

### Esquema de Cliente

```text
┌ Navegación ────┬──────────────────────────────────────────────────┐
│ Retención     │ Retención bancaria                               │
│ Cliente       │ Prioriza acciones según riesgo y valor esperado  │
│ Lote          ├──────────────────────┬───────────────────────────┤
│ Modelo        │ Perfil del cliente   │ Recomendación             │
│ Monitoreo     │ Datos + ayudas       │ Riesgo / decisión / euros │
│               │ Analizar cliente     │ Riesgo vs. umbral         │
│ Regla actual  │ Cargar ejemplo       │ Factores SHAP con signo   │
│  p > umbral   │                      │ Explicación literal       │
└───────────────┴──────────────────────┴───────────────────────────┘
```

En móvil se comprueba la adaptación nativa y la navegación lateral colapsada.
El estado vacío invita a analizar o cargar el ejemplo, sin inventar predicciones.
Los resultados indican qué datos fueron evaluados. Las vistas de evidencia
muestran tablas de detalle en expansores para no saturar la pantalla.

## 2. Secuencia y mensajes previstos

### T0 — Compuerta SDD

- Conservar los seis cambios documentales de S18 ya presentes, revisados como
  trabajo previo de esta misma sesión; incluir su evidencia en el commit documental.
- Enmendar spec 005 v1.3, crear este plan y abrir S19 en el registro.
- Comprobar CI de la base y los cinco comandos de AGENTS §4; incluir documentos
  nuevos en pre-commit. Versionar antes de tocar aplicación/tests/empaquetado.
- Mensaje: `docs: specify professional dashboard redesign (SDD gate)`.

### T1 — Datos y contrato de presentación

- Extensión aditiva y agregada de `/model`; tests de correspondencia y de
  compatibilidad cuando faltan políticas.
- Helpers puros para números españoles, etiquetas y gráficos Vega-Lite: riesgo,
  SHAP, histograma, decisiones, políticas, PSI y calibración.
- Tests significativos: umbral estricto, signos/pp, extremos 0 y 1 del histograma,
  recuentos, datos finales exactos y límites tomados del reporte.

### T2 — Interfaz y tema

- Cuatro vistas con radio lateral, solo renderizado de la activa.
- Cliente con ejemplo, formulario en español, carga/error y resultado por sesión.
- Lote con ejemplo generado en memoria, procesamiento explícito, invalidación
  por contenido normalizado, tabla legible, filtros y descarga sin nueva inferencia.
- Modelo con evidencia final, comparación económica, enlace a ficha y metodología.
- Monitoreo con selector de escenario, gráficos y explicación de E2/S4.
- `.streamlit/config.toml` con tema nativo; copiarlo en Docker y Space y adaptar
  la prueba de lista exacta. No eliminar controles de seguridad.
- Regresión AppTest: contenido LLM literal, navegación/resultados persistentes,
  caso no contactar, fallos/ausencias y cero llamadas por interacciones de lectura.

### T3 — Vista previa y comprobación

- Arrancar API local con modelo congelado verificado y Streamlit en loopback;
  LLM desactivado. No desplegar en Render para revisar esta rama.
- Navegador real: referencia, lote sintético, gráficos, descarga y retorno entre
  vistas; comprobar que gráficos/tablas muestran los mismos valores.
- Revisar escritorio y móvil, teclado/foco y zoom. Capturas temporales fuera del
  workspace, sin archivos de clientes ni valores de cookies/secretos.
- Comprobar build/armado y controles existentes. Medición local del proceso si
  está disponible; no declarar rendimiento Free bajo carga sin medirlo allí.
- Ejecutar los cinco comandos de AGENTS §4, registrar resultados y bloqueos.
- La implementación queda preparada para revisión. Su commit/push y despliegue
  se autorizan explícitamente tras ver el resultado.

## 3. Decisiones congeladas para esta sección

- No se añaden curvas ROC/PR finales ni un waterfall SHAP incompleto.
- No se recalculan métricas ni se vuelven a abrir particiones de datos.
- Comparación económica limitada a modelo, contactar a todos y no contactar.
- Sin importación directa de Altair/Plotly: se usan especificaciones Vega-Lite
  que Streamlit ya soporta y datos agregados pequeños.
- El generador puro de `scripts/make_example_csv.py` se extrae sin cambiar su
  algoritmo/semilla a `src/churn/examples.py`. El script conserva `generate`
  mediante importación y el dashboard usa el módulo instalado. Así funciona
  también en Docker/Space sin importar scripts ajenos al paquete ni copiar CSV.
  Los tests existentes deben confirmar igualdad exacta con el ejemplo versionado.
- Texto de explicación mediante `st.text`; no se admite HTML dinámico.
- Cualquier decisión fuera de estos puntos se registra antes de implementar.

## 4. Evidencia de cierre

Spec 005 §12.4 y S19 del registro. Se distingue compuerta documental, cambios
locales de código, comprobación real en navegador y aprobación de despliegue.
Las cabeceras públicas pendientes son evidencia previa, no resuelta por el tema.
