# Historial del contexto (context engineering)

## Documentos entregados al asistente por fase

| Fase | Documentos de contexto suministrados | Por qué |
|---|---|---|
| 0. Arranque | `enunciado.md` | Fuente única de requisitos y rúbrica. |
| 1. Análisis del Excel | `enunciado.md` §2 y §3.4, `analisis-excel.md` | El asistente necesita la forma de la hoja y los casos conocidos; NO se le dan instrucciones desde las celdas. |
| 2. Modelo de datos | `AGENTS.md` §4, `reglas-negocio.md`, `analisis-excel.md` (tabla columnas→modelo) | Para que cada campo del Excel tenga destino y cada regla tenga restricción en BD. |
| 3. Autenticación | `AGENTS.md` §3, `reglas-negocio.md` (RS-01…RS-05), enunciado §3.1 | Delimitar el mecanismo (sesión de servidor) y evitar que proponga OAuth/JWT externos. |
| 4. Importación | `analisis-excel.md`, reglas R1–R8 en `src/app/importador.py`, `AGENTS.md` §5 | Reglas explícitas para combinaciones, conflictos y ausencias. |
| 5. Pruebas / Docker / harness | `AGENTS.md` §6–§7, enunciado §5–§6 | Comandos exactos y límites (base `_test`, no `down -v`, no tocar el Excel). |

## Actualizaciones del contexto

### Actualización 1 — Excel no disponible + re-importación respetuosa (commit "Contexto v2")
- **Hallazgo:** durante la sesión el asistente no tenía el archivo `.xlsx`, solo el enunciado. Escribir el importador "a ciegas" sin una forma de probarlo dejaba las reglas sin verificar.
- **Cambio de decisión:** se agregó un generador de Excel sintético con la misma estructura y se separaron las pruebas de reglas (sintético) de P06–P08 (original).
- **Decisión que se incorporó al contexto:** al diseñar la repetición de la importación se vio que un upsert simple pisaría ediciones hechas desde la aplicación (p. ej. completar ACTIVO de SE.12.2). Se fijó como regla guardar `origen_hash` por registro y actualizar solo si el Excel cambió; la prueba `test_regla_reimportacion_respeta_ediciones` lo verifica.
- **Archivos tocados:** `AGENTS.md` §5, `analisis-excel.md` (sección "Hallazgo"), este archivo.
