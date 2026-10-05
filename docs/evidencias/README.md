# Evidencias

| Archivo | Qué demuestra |
|---|---|
| `harness-ciclo-01-fallo.log` | Primera ejecución de `scripts/check.sh`: falla (módulo no encontrado por `PYTHONPATH`; falta el Excel). |
| `harness-ciclo-01-correccion.log` | Ejecución tras la corrección: `RESULTADO: TODO EN VERDE`, código 0. |
| `pytest-sesion-ia.log` | `pytest -v` completo (32 pruebas) en la sesión de IA. |
| `resultados-evaluacion.md` | Plantilla para anotar la corrida con el Excel **original** y Docker (P06–P08 y P12). |

## Ciclo completo de harness engineering (ciclo 01)
1. **Tarea:** crear la rutina de verificación `scripts/check.sh` (prompt P5).
2. **Cambio propuesto por la IA:** script con 5 controles que invoca `python -m scripts.migrate` y `pytest`.
3. **Ejecución de controles:** `sh scripts/check.sh` → `harness-ciclo-01-fallo.log`.
4. **Fallo detectado:** `No module named scripts.migrate` en el control 3 (y en cadena el 4). El fallo **no** fue introducido deliberadamente: apareció al ejecutar el script fuera del contenedor, donde no existe `PYTHONPATH=/app/src`.
5. **Corrección:** `export PYTHONPATH="${PYTHONPATH:-src}"` en `check.sh` y regla agregada a `AGENTS.md` (contexto v3).
6. **Nueva ejecución satisfactoria:** `harness-ciclo-01-correccion.log` → 5/5 controles OK, 32 pruebas en verde, código de salida 0.

> Nota de transparencia: el Excel original no estuvo disponible en la sesión de IA. La corrida verde usó el Excel sintético en una copia temporal del repositorio. La verificación con el archivo original se registra en `resultados-evaluacion.md`.
