# Sistema de gestión del catálogo de servicios de TI

Parcial — Software Avanzado, Facultad de Ingeniería, USAC. Aplicación web que importa el catálogo de `data/CatalogoServicios.xlsx`, lo mantiene, y agrega estructura organizacional, usuarios y responsables de servicios.

| | |
|---|---|
| **Integrante** | Susan Pamela Herrera Monzon — carné: `201612218` |
| **Rama de entrega** | `main` · etiqueta `parcial-v2.0` |
| **Tecnologías** | Python 3.12, FastAPI, SQLAlchemy 2, PostgreSQL 16, HTML/JS, Docker Compose |
| **Documentación técnica** | [`docs/RESOLUCION.md`](docs/RESOLUCION.md) · contexto para IA: [`AGENTS.md`](AGENTS.md) |

## 1. Requisitos
- Docker Engine **24+** y Docker Compose **v2.20+** (`docker compose version`).
- Puerto `8000` libre (cambiable con `APP_PORT` en `.env`).
- No se necesita Python, PostgreSQL ni ninguna clave de proveedores de IA en el equipo.

## 2. Configuración
```bash
git clone <URL-del-repositorio> parcial-catalogo-servicios
cd parcial-catalogo-servicios
cp .env.example .env          # en Windows: copy .env.example .env
# edite .env si desea otras contraseñas de demostración
```
`data/CatalogoServicios.xlsx` es el archivo original sin modificar; el contenedor lo monta en **solo lectura**.

## 3. Levantar el sistema
```bash
docker compose up --build -d
docker compose ps             # db y app deben quedar "healthy"
```
- URL: **http://localhost:8000**
- Al arrancar, `app` espera a que la base esté disponible (healthcheck + reintentos) y aplica las migraciones pendientes.
- Salud: `http://localhost:8000/health`

## 4. Importar el Excel y crear cuentas de evaluación
```bash
docker compose exec app python -m scripts.import_excel --observaciones   # importa 12 N1 / 46 N2 e imprime incidencias
docker compose exec app python -m scripts.seed_demo                      # organización demo, cuentas y 3 asignaciones
```
El orden importa: `seed_demo` crea las 3 asignaciones sobre servicios ya importados (si se ejecuta antes, se puede repetir; es idempotente). La importación también se puede ejecutar desde la interfaz (**Importación → Importar**) con el rol administrador. Repetirla no duplica registros.

| Rol | Usuario | Contraseña |
|---|---|---|
| administrador | valor de `DEMO_ADMIN_USUARIO` (por defecto `admin`) | valor de `DEMO_ADMIN_PASSWORD` en `.env` |
| consulta | valor de `DEMO_CONSULTA_USUARIO` (por defecto `consulta`) | valor de `DEMO_CONSULTA_PASSWORD` en `.env` |

Credenciales **solo de demostración**, configuradas localmente en `.env` (no versionado). Los usuarios `ana.redes` y `luis.apps` (rol consulta, misma contraseña que la cuenta de consulta) existen para mostrar responsables. La estructura organizacional demo es ficticia: **no proviene del Excel**.

## 5. Pruebas y verificación
```bash
docker compose exec app pytest -v                 # P01–P11 sobre la base aislada catalogo_test
docker compose exec app sh scripts/check.sh      # harness completo: Excel intacto, lint, migraciones, pruebas
sh scripts/p12_persistencia.sh                   # P12: reinicio de contenedores sin borrar volúmenes (desde el anfitrión)
```
`check.sh` termina con `RESULTADO: TODO EN VERDE` y código 0, o indica qué control falló. Las pruebas nunca tocan la base de evaluación `catalogo`. Detalle por escenario en `docs/RESOLUCION.md` §7–§8.

> Si el volumen de la BD se creó con una versión anterior del repositorio y no existe `catalogo_test`, créela una vez con
> `docker compose exec db psql -U catalogo -c "CREATE DATABASE catalogo_test;"`.

## 6. Operación
| Acción | Comando |
|---|---|
| Ver logs | `docker compose logs -f app` (o `db`) |
| Detener (conserva datos) | `docker compose stop` |
| Iniciar de nuevo | `docker compose start` |
| Apagar y quitar contenedores (conserva datos) | `docker compose down` |
| Reconstruir tras cambios | `docker compose up --build -d` |
| **Reinicio destructivo** (borra la BD de evaluación) | `docker compose down -v` y luego repetir §3 y §4 |

## 7. Estructura
```text
AGENTS.md                 contexto para asistentes de IA
compose.yaml, Dockerfile, .dockerignore, .env.example
migrations/               migraciones SQL numeradas
src/app/                  aplicación (API, servicios de negocio, importador, interfaz en static/)
src/scripts/              migrate, import_excel, seed_demo, p12
scripts/                  entrypoint.sh, check.sh (harness), p12_persistencia.sh
tests/                    pytest P01–P11 + reglas del importador (fixtures/excel_sintetico.py)
data/CatalogoServicios.xlsx   archivo original
docs/RESOLUCION.md        documento de resolución
docs/contexto/ docs/prompts/ docs/evidencias/
```

## 8. Acceso del catedrático
El usuario de GitHub **`maldanap-usac`** fue agregado como colaborador del repositorio. Estado de la invitación: `__________` (aceptada / pendiente).
