# Especificación 008 — Cobertura completa de sentencias

| Campo | Valor |
|---|---|
| Estado | Diseño previo a tests; compuerta SDD pendiente |
| Base | `6487997`, CI y Security scans satisfactorios |
| Objetivo | 100 % de sentencias de `src/churn` mediante pruebas significativas |
| Autorización | Responsable: probar el 100 % y autorizar dos commits (compuerta y tests), publicados en main |

## 1. Alcance

Medición inicial: 322 tests, 2.376 sentencias, 43 sin cubrir, 98,19 %.
Se amplían tests; no se cambia el código productivo, dependencias, modelo,
hiperparámetros, supuestos, reportes ni dataset. El mínimo histórico de CI (85 %)
se conserva; la aceptación de esta sección exige explícitamente 100 %.
No se presenta cobertura de sentencias como cobertura de ramas ni ausencia de bugs.

## 2. Invariantes

- No usar exclusiones de cobertura, `pragma: no cover`, omisiones nuevas ni
  eliminar código para reducir el denominador.
- No cargar la partición real de prueba, repetir evaluación final real ni
  reentrenar sobre datos del proyecto. `Gender` no entra en ningún modelo.
- Nuevos tests usan fixtures sintéticas, `tmp_path`, transporte simulado y
  bases MLflow temporales. No contactan red/proveedores ni descargan el modelo real.
- Los reportes existentes pueden leerse para comprobar renderizadores; cualquier
  variante se crea en memoria o se copia al temporal, nunca se sobrescribe el original.
- Las CLI se ejecutan con raíz/entradas/salidas temporales y argv aislado. El
  wrapper `__main__` se comprueba con `runpy`, sin sustituir el cuerpo bajo prueba:
  salidas/códigos correctos o rechazo de prerrequisitos ausentes/incoherentes.
  El lanzador de evaluación final debe rechazar metadata sintética ya completada
  antes de cargar modelo o partición. Nunca ejecutar `churn-final` contra el workspace.

## 3. Casos de aceptación

| Área | Caso y comportamiento a comprobar |
|---|---|
| Artefacto | Descargador HTTP simulado conserva bytes y cierra recursos; CLI comprueba hash y comunica éxito o rechazo |
| Calibración | OOF incompleta produce error, no calibrador con NaN |
| Selección | E-03 conserva salario cuando empeora más del margen; modelo complejo compara con LogReg; OOF de la familia correcta, sin mezclar repeticiones |
| SHAP | Explicación no aditiva rechazada |
| Hipótesis | Fisher con OR infinito y Woolf con celdas cero se serializan como indefinidos, sin inventar valores |
| Reportes | Perfiles vacíos omitidos y prueba todavía reservada explícita en ficha |
| Narrativa | Reset de cuota permite nuevos intentos; cliente OpenAI real configurado sin red y sin credenciales reales |
| ASGI | Desconexión temprana no llama la app y libera plaza; mensajes tras replay se delegan intactos |
| Tracking | URI predeterminada crea directorio y corrida dentro del temporal; comando Git devuelve identidad correcta |
| CSV | Cabeceras vacías o con codificación inválida muestran error controlado |
| Validación | AUC de clase única indefinida; duplicados informativos, productos extremos y salario bajo cubiertos también sin datos locales |
| Figuras | Archivo que supera el límite falla; recursos de figura se cierran |
| Lanzadores | CLI de reportes y validación producen archivos/códigos esperados; CLI de análisis no prosigue sin prerrequisitos |

## 4. Verificación

1. Pruebas focalizadas; comprobar sus aserciones de comportamiento, no solo ejecutar líneas.
2. Cinco comandos obligatorios de AGENTS §4 y hooks explícitos para archivos nuevos.
3. Suite con `uv run pytest --cov=churn --cov-report=term-missing --cov-fail-under=100`:
   cero sentencias sin cubrir, sin excluir módulos ni cambiar el denominador.
4. Repetición desde copia Git limpia sin dataset, modelo o tracking locales:
   solo los tres skips preexistentes esperados; 100 % de sentencias también allí.
5. CI y Security scans del commit publicado satisfactorios; distinguir del umbral
   del workflow que se mantiene en 85 %. Registrar medición local estricta y CI.

Si un test revela un defecto productivo que impida el objetivo, documentar el
hallazgo y pedir una enmienda antes de cambiar `src/`. No debilitar aserciones.

Plan: [plan-cobertura-completa.md](../docs/plan-cobertura-completa.md).
