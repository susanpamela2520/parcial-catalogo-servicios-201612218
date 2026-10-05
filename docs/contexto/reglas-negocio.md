# Reglas de negocio

## Organización
| ID | Regla | Dónde se aplica |
|---|---|---|
| RN-01 | Jerarquía Empresa → Área → Departamento → Sección → Puesto → Usuario; un único padre (FK NOT NULL). | Esquema SQL |
| RN-02 | Código de empresa único global; códigos subordinados únicos dentro del padre (sin distinguir mayúsculas en la API). | `UNIQUE(padre, codigo)` + `services/organizacion.py` |
| RN-03 | No se crean ni mueven registros bajo padres inexistentes (404) o inactivos (409). | `_padre_activo` |
| RN-04 | La empresa del usuario se deriva por joins desde su puesto; no existe columna `empresa_id` en usuario. | `ruta_organizacional` |
| RN-05 | Bajas lógicas (`activo = false`); no hay DELETE en la API. | Rutas `/desactivar` |
| RN-06 | Desactivar con hijos activos → 409 con la lista de dependientes. Con `?cascada=true` se desactivan todos los descendientes y se devuelven. | `desactivar_registro` |
| RN-07 | Reactivar exige el padre activo. | `activar_registro` |
| RN-08 | Al desactivar un usuario (directo o en cascada) se revocan sus sesiones. Un administrador no puede desactivarse a sí mismo. | `desactivar_registro` |
| RN-09 | Una sección desactivada conserva sus asignaciones históricas (se informan en la respuesta), pero no admite asignaciones nuevas. | `validar_asignacion` |

## Catálogo
| ID | Regla | Dónde |
|---|---|---|
| RC-01 | Todo N2 pertenece a un N1 existente; código único por nivel. | FK + UNIQUE |
| RC-02 | Clase, criticidad y tipo se eligen de catálogos (FK); un valor fuera de catálogo se conserva en `*_original`. | `guardar_n2`, importador |
| RC-03 | `minimo <= maximo` cuando ambos existen; ausente = NULL, nunca 0. | API + `CHECK ck_umbral` |
| RC-04 | `ACTIVO` del Excel: `S`, `N` o NULL (desconocido). La baja desde la app es `dado_de_baja`, independiente. | Esquema |
| RC-05 | `estado_revision = REVISION` si falta ACTIVO, clase, criticidad o tipo, o si la importación dejó observaciones no informativas. | API + importador |
| RC-06 | Responsable opcional, debe pertenecer a la sección asignada; sin sección no hay responsable. | API + trigger `tg_valida_responsable` + `CHECK` |

## Seguridad
| ID | Regla |
|---|---|
| RS-01 | Contraseñas con Argon2id (sal aleatoria por hash). Nunca se devuelve `password_hash` en la API. |
| RS-02 | Sesión: token aleatorio de 256 bits en cookie HttpOnly, SameSite=Lax; en BD solo su SHA-256, con expiración y revocación. |
| RS-03 | Cada petición valida sesión vigente **y** usuario activo. |
| RS-04 | GET = cualquier usuario autenticado; POST/PUT = solo administrador (403). |
| RS-05 | Mensaje de login genérico; se hace verificación ficticia cuando el usuario no existe para igualar tiempos. |
