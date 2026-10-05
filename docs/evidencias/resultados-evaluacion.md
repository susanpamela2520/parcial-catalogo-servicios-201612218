# Resultados con el Excel original y Docker

Completar al correr el sistema en Docker con `data/CatalogoServicios.xlsx` original (ver README §4). Pegar la salida real de cada comando.

| Fecha | Commit | Comando | Resultado |
|---|---|---|---|
| | | `docker compose exec app python -m scripts.import_excel --observaciones` | |
| | | `docker compose exec app python -m scripts.import_excel` (2.ª vez) | |
| | | `docker compose exec app sh scripts/check.sh` | |
| | | `sh scripts/p12_persistencia.sh` | |

## Salida de la importación
```text
docker compose exec app python -m scripts.import_excel --observaciones
[import] resumen:
{
  "filas_leidas": 97,
  "filas_servicio": 46,
  "filas_continuacion": 49,
  "filas_vacias": 0,
  "filas_omitidas": 2,
  "n1": {
    "creados": 12,
    "actualizados": 0,
    "sin_cambios": 0
  },
  "n2": {
    "creados": 46,
    "actualizados": 0,
    "sin_cambios": 0
  },
  "control": {
    "n1_encontrados": 12,
    "n2_encontrados": 46,
    "esperado_n1": 12,
    "esperado_n2": 46,
    "ok": true
  },
  "observaciones": 8,
  "observaciones_por_tipo": {
    "FILA_SIN_CODIGO": 2,
    "ENCABEZADO_LISTA_OPCIONES": 1,
    "CONFLICTO_NOMBRE_N1": 1,
    "ATRIBUTO_AUSENTE": 3,
    "N1_DERIVADO_DEL_CODIGO": 1
  },
  "importacion_id": 1
}
[import] servicios con observaciones: SE.12.1, SE.12.2, SE.12.3
  - [FILA_SIN_CODIGO] A42:L42 : Fila 42 tiene datos pero no tiene código N2 ni pertenece a un rango combinado de C; se omite.
  - [FILA_SIN_CODIGO] A67:L67 : Fila 67 tiene datos pero no tiene código N2 ni pertenece a un rango combinado de C; se omite.
  - [ENCABEZADO_LISTA_OPCIONES] E111:H111 : Fila 111: encabezado de las listas de opciones; no es un servicio.
  - [CONFLICTO_NOMBRE_N1] A99:B100 SE.12: El código N1 SE.12 aparece con 2 nombres distintos; nombre canónico: 'Suministrar Analitica'.
  - [ATRIBUTO_AUSENTE] A99:L99 SE.12.1: SE.12.1 no tiene valor en: activo, clase, criticidad, tipo, metrica. Queda como desconocido.
  - [ATRIBUTO_AUSENTE] A100:L100 SE.12.2: SE.12.2 no tiene valor en: activo, clase, criticidad, tipo, metrica. Queda como desconocido.
  - [N1_DERIVADO_DEL_CODIGO] A101:L101 SE.12.3: SE.12.3 no tiene COD.N1 en el Excel; se asocia a SE.12 por el prefijo de su código.
  - [ATRIBUTO_AUSENTE] A101:L101 SE.12.3: SE.12.3 no tiene valor en: activo, clase, criticidad, tipo, metrica. Queda como desconocido.
```

## Salida de check.sh
```text
1/5 Excel original intacto ==
[OK] SHA-256 coincide

== 2/5 Calidad de código (ruff) ==
All checks passed!
[OK] sin observaciones

== 3/5 Migraciones ==
[migrate] esquema al día
[OK] esquema al día

== 4/5 Pruebas automatizadas P01-P11 (base catalogo_test) ==
.................................                                [100%]
=========================== warnings summary ===========================
../usr/local/lib/python3.12/site-packages/fastapi/testclient.py:1
  /usr/local/lib/python3.12/site-packages/fastapi/testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
33 passed, 1 warning in 35.30s
[OK] pruebas en verde

== 5/5 Variables sensibles fuera del repositorio ==
[OK] .env no está incluido

RESULTADO: TODO EN VERDE

```

## Salida de P12
```text
$ sh scripts/p12_persistencia.sh
[P12] creando registro de control P12-1791171012
[P12] reiniciando contenedores (docker compose stop + start; el volumen se conserva)
[+] Stopping 0/0
[+] Stopping 0/1alogo-servicios-app
[+] Stopping 0/1alogo-servicios-app
[+] Stopping 0/1alogo-servicios-app
[+] Stopping 0/1alogo-servicios-app
[+] Stopping 0/1alogo-servicios-app
[+] Stopping 0/1alogo-servicios-app
[+] Stopping 0/1alogo-servicios-app
[+] Stopping 1/1alogo-servicios-app
 ✔ Container catalogo-servicios-app[+] Stopping 1/2
 ✔ Container catalogo-servicios-app[+] Stopping 1/2 
 ✔ Container catalogo-servicios-app[+] Stopping 2/2 
 ✔ Container catalogo-servicios-app-1  Stopped0.8s  
 ✔ Container catalogo-servicios-db-1   Stopped0.4s 
[+] Running 0/0
[+] Running 0/1talogo-servicios-db-
[+] Running 0/1talogo-servicios-db-
[+] Running 0/1talogo-servicios-db-
[+] Running 0/1talogo-servicios-db-
[+] Running 0/1talogo-servicios-db-
[+] Running 0/1talogo-servicios-db-
[+] Running 0/1talogo-servicios-db-
[+] Running 0/1talogo-servicios-db-
[+] Running 0/1talogo-servicios-db-
[+] Running 0/1talogo-servicios-db-
[+] Running 0/1talogo-servicios-db-
[+] Running 0/1talogo-servicios-db-
[+] Running 0/1talogo-servicios-db-
[+] Running 0/1talogo-servicios-db-
[+] Running 0/1talogo-servicios-db-
[+] Running 0/1talogo-servicios-db-
[+] Running 0/1talogo-servicios-db-
[+] Running 0/1talogo-servicios-db-
[+] Running 0/1talogo-servicios-db-
[+] Running 0/1talogo-servicios-db-
[+] Running 0/1talogo-servicios-db-
[+] Running 0/1talogo-servicios-db-
[+] Running 0/1talogo-servicios-db-
[+] Running 0/1talogo-servicios-db-
[+] Running 0/1talogo-servicios-db-
[+] Running 0/1talogo-servicios-db-
[+] Running 0/1talogo-servicios-db-
[+] Running 0/1talogo-servicios-db-
[+] Running 0/1talogo-servicios-db-
[+] Running 0/1talogo-servicios-db-
[+] Running 0/1talogo-servicios-db-
[+] Running 0/1talogo-servicios-db-
[+] Running 0/1talogo-servicios-db-
[+] Running 0/1talogo-servicios-db-
[+] Running 0/1talogo-servicios-db-
[+] Running 0/1talogo-servicios-db-
[+] Running 0/1talogo-servicios-db-
[+] Running 0/1talogo-servicios-db-
[+] Running 0/1talogo-servicios-db-
[+] Running 0/1talogo-servicios-db-
[+] Running 0/1talogo-servicios-db-
[+] Running 0/1talogo-servicios-db-
[+] Running 0/1talogo-servicios-db-
[+] Running 0/1talogo-servicios-db-
[+] Running 0/1talogo-servicios-db-
[+] Running 0/1talogo-servicios-db-
[+] Running 0/1talogo-servicios-db-
[+] Running 0/1talogo-servicios-db-
[+] Running 0/1talogo-servicios-db-
[+] Running 0/1talogo-servicios-db-
[+] Running 0/1talogo-servicios-db-
[+] Running 0/1talogo-servicios-db-
[+] Running 0/1talogo-servicios-db-
[+] Running 0/1talogo-servicios-db-
[+] Running 0/1talogo-servicios-db-
[+] Running 0/1talogo-servicios-db-
[+] Running 1/1talogo-servicios-db-
 ✔ Container catalogo-servicios-db-[+] Running 1/2 
 ✔ Container catalogo-servicios-db-[+] Running 1/2  
 ✔ Container catalogo-servicios-db-[+] Running 1/2  
 ✔ Container catalogo-servicios-db-[+] Running 2/2  
 ✔ Container catalogo-servicios-db-1   Healthy5.7s  
 ✔ Container catalogo-servicios-app-1  Started0.4s 
[P12] registro P12-1791171012: encontrado
[P12] OK: el registro persiste tras el reinicio

```
