# Correcciones de seguridad de la demo

Especificación: [007](../specs/007-security-hardening.md). Compuerta de código:
`6343526`. El modelo, su hash y los resultados permanecen congelados.

| Hallazgo | Corrección |
|---|---|
| SEC-01 | Descarga sin columnas extra ni identificadores; normalización y protección CSV |
| SEC-02 | Auditoría y evaluación final cargan únicamente artefactos locales con SHA-256 válido |
| SEC-03 | Ventana global de 60 intentos/minuto y 2 inferencias simultáneas; presupuesto LLM SQLite |
| SEC-04 | JSON de 512 KiB y CSV de 1 MiB; lectura de como máximo 1.001 filas |
| SEC-05 | Tres casos SHAP publicados sin identificador; generador sin `customer_id` |
| SEC-06 | XSRF y CORS activos; configuración de iframe HTTPS sin desactivar XSRF |
| SEC-07 | Puertos Compose publicados en `127.0.0.1` |
| SEC-08 | Helper Git restringido a protocolo, host y Space; token fuera de la URL |
| SEC-09 | Texto LLM con `st.text`, sin Markdown ni HTML |
| SEC-10 | Actions/hooks por SHA e imágenes por digest multi-arquitectura verificado |
| SEC-11 | Exclusión `.env*` y `.runtime`, con excepción de la plantilla vacía |
| SEC-12 | Errores 422 sin `input`/`ctx`; validación CLI sin valores rechazados |
| SEC-13 | CI con `contents: read` y checkout sin credenciales persistidas |

## Límites operativos

- La API funciona con un worker y presupuesto global, no una cuota por visitante.
- El LLM comparte la cuota entre procesos con acceso al mismo SQLite. Reiniciar
  el proceso conserva el presupuesto; perder el archivo/volumen no lo conserva.
  Compose usa el volumen `llm-state`. No garantiza una cuota común entre hosts.
- La defensa CSV principal es eliminar texto extra y exportar datos normalizados;
  no se promete que una técnica de escape sea universal tras guardar y reabrir
  el archivo en todos los programas de hojas de cálculo.
- No se reescribe Git: el historial conserva los identificadores anteriores del
  dataset público. No se han detectado secretos reales que requieran rotación.
- El helper entrega el token al proceso Git por su canal de credenciales; el
  entorno del runner sigue siendo un límite de confianza, no un almacén invulnerable.
- TLS, cabeceras del proxy, iframe público y análisis de CVE siguen requiriendo
  verificación externa. Las pruebas locales no certifican esos controles.

## Fuentes

La spec 007 enlaza OWASP, scikit-learn, Streamlit, Python y GitHub Actions.
El protocolo del helper sigue [Git credentials](https://git-scm.com/docs/gitcredentials).
El límite del widget sigue [Streamlit file uploader](https://docs.streamlit.io/develop/api-reference/widgets/st.file_uploader).

## Verificación

Consultar S14 de [registro-avance.md](registro-avance.md) para los comandos,
resultados locales y evidencia de CI. Las pruebas de evaluación final son
sintéticas; nunca se vuelve a ejecutar la evaluación real reservada.
