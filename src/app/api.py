"""Rutas JSON /api/*. Toda autorización se decide aquí (servidor), no en la interfaz.

- Lectura (GET): cualquier usuario autenticado y activo.
- Escritura (POST/PUT): solo rol administrador.
"""
from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from . import config
from .db import get_db
from .deps import requiere_admin, usuario_actual
from .importador import importar
from .models import Importacion, MapeoEtiqueta, ObservacionImportacion, Usuario
from .security import autenticar, crear_sesion, revocar_sesion
from .services import catalogo as cat
from .services import organizacion as org
from .services.errores import NegocioError

router = APIRouter(prefix="/api")
Lector = Depends(usuario_actual)
Admin = Depends(requiere_admin)


# ------------------------------------------------------------------ autenticación
@router.post("/auth/login")
def login(response: Response, datos: dict = Body(...), db: Session = Depends(get_db)):
    ident = str(datos.get("usuario") or datos.get("correo") or "")
    u = autenticar(db, ident, str(datos.get("password") or ""))
    if u is None:
        # Mensaje genérico: no revela si el usuario existe o está inactivo
        raise HTTPException(401, "Usuario o contraseña incorrectos.")
    token = crear_sesion(db, u)
    response.set_cookie(config.COOKIE_NAME, token, httponly=True, samesite="lax", secure=config.COOKIE_SECURE,
                        max_age=config.SESSION_HOURS * 3600, path="/")
    return {"usuario": org.usuario_dict(db, u)}


@router.post("/auth/logout")
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    revocar_sesion(db, request.cookies.get(config.COOKIE_NAME))
    response.delete_cookie(config.COOKIE_NAME, path="/")
    return {"ok": True}


@router.get("/auth/me")
def me(u: Usuario = Lector, db: Session = Depends(get_db)):
    return org.usuario_dict(db, u)


# ------------------------------------------------------------------ organización
@router.get("/org/{entidad}")
def org_listar(entidad: str, padre_id: int | None = None, activo: bool | None = None,
               _: Usuario = Lector, db: Session = Depends(get_db)):
    return org.listar(db, entidad, padre_id, activo)


@router.get("/org/{entidad}/{id_}")
def org_obtener(entidad: str, id_: int, _: Usuario = Lector, db: Session = Depends(get_db)):
    return org.a_dict(org.obtener(db, entidad, id_))


@router.post("/org/{entidad}", status_code=201)
def org_crear(entidad: str, datos: dict = Body(...), _: Usuario = Admin, db: Session = Depends(get_db)):
    return org.crear(db, entidad, datos)


@router.put("/org/{entidad}/{id_}")
def org_actualizar(entidad: str, id_: int, datos: dict = Body(...), _: Usuario = Admin, db: Session = Depends(get_db)):
    return org.actualizar(db, entidad, id_, datos)


@router.post("/org/{entidad}/{id_}/desactivar")
def org_desactivar(entidad: str, id_: int, cascada: bool = False, u: Usuario = Admin, db: Session = Depends(get_db)):
    return org.desactivar_registro(db, org.obtener(db, entidad, id_), cascada, u.id)


@router.post("/org/{entidad}/{id_}/activar")
def org_activar(entidad: str, id_: int, _: Usuario = Admin, db: Session = Depends(get_db)):
    obj = org.obtener(db, entidad, id_)
    return org.activar_registro(db, obj, org.padre_de(obj))


# ------------------------------------------------------------------ usuarios
def _usuario(db: Session, id_: int) -> Usuario:
    u = db.get(Usuario, id_)
    if u is None:
        raise NegocioError(f"No existe el usuario con id {id_}.", 404)
    return u


@router.get("/usuarios")
def usuarios_listar(puesto_id: int | None = None, seccion_id: int | None = None, activo: bool | None = None,
                    _: Usuario = Lector, db: Session = Depends(get_db)):
    from .models import Puesto
    q = select(Usuario).join(Puesto, Puesto.id == Usuario.puesto_id).order_by(Usuario.usuario)
    if puesto_id:
        q = q.where(Usuario.puesto_id == puesto_id)
    if seccion_id:
        q = q.where(Puesto.seccion_id == seccion_id)
    if activo is not None:
        q = q.where(Usuario.activo == activo)
    return [org.usuario_dict(db, u) for u in db.scalars(q).unique()]


@router.get("/usuarios/{id_}")
def usuarios_obtener(id_: int, _: Usuario = Lector, db: Session = Depends(get_db)):
    return org.usuario_dict(db, _usuario(db, id_))


@router.post("/usuarios", status_code=201)
def usuarios_crear(datos: dict = Body(...), _: Usuario = Admin, db: Session = Depends(get_db)):
    return org.crear_usuario(db, datos)


@router.put("/usuarios/{id_}")
def usuarios_actualizar(id_: int, datos: dict = Body(...), _: Usuario = Admin, db: Session = Depends(get_db)):
    return org.actualizar_usuario(db, _usuario(db, id_), datos)


@router.post("/usuarios/{id_}/desactivar")
def usuarios_desactivar(id_: int, u: Usuario = Admin, db: Session = Depends(get_db)):
    return org.desactivar_registro(db, _usuario(db, id_), False, u.id)


@router.post("/usuarios/{id_}/activar")
def usuarios_activar(id_: int, _: Usuario = Admin, db: Session = Depends(get_db)):
    obj = _usuario(db, id_)
    return org.usuario_dict(db, _activar(db, obj))


def _activar(db, obj):
    org.activar_registro(db, obj, org.padre_de(obj))
    return obj


# ------------------------------------------------------------------ catálogos controlados
@router.get("/catalogos/{nombre}")
def catalogos_listar(nombre: str, solo_activos: bool = False, _: Usuario = Lector, db: Session = Depends(get_db)):
    return cat.listar_catalogo(db, nombre, solo_activos)


@router.post("/catalogos/{nombre}", status_code=201)
def catalogos_crear(nombre: str, datos: dict = Body(...), _: Usuario = Admin, db: Session = Depends(get_db)):
    return cat.guardar_catalogo(db, nombre, datos)


@router.put("/catalogos/{nombre}/{id_}")
def catalogos_actualizar(nombre: str, id_: int, datos: dict = Body(...), _: Usuario = Admin, db: Session = Depends(get_db)):
    return cat.guardar_catalogo(db, nombre, datos, id_)


@router.get("/mapeos")
def mapeos(_: Usuario = Lector, db: Session = Depends(get_db)):
    return [org.a_dict(m) for m in db.scalars(select(MapeoEtiqueta).order_by(MapeoEtiqueta.campo))]


# ------------------------------------------------------------------ servicios
@router.get("/servicios-n1")
def n1_listar(_: Usuario = Lector, db: Session = Depends(get_db)):
    return cat.listar_n1(db)


@router.post("/servicios-n1", status_code=201)
def n1_crear(datos: dict = Body(...), _: Usuario = Admin, db: Session = Depends(get_db)):
    return cat.guardar_n1(db, datos)


@router.put("/servicios-n1/{id_}")
def n1_actualizar(id_: int, datos: dict = Body(...), _: Usuario = Admin, db: Session = Depends(get_db)):
    return cat.guardar_n1(db, datos, id_)


@router.get("/servicios")
def n2_buscar(q: str | None = None, n1_id: int | None = None, activo: str | None = None,
              clase_id: int | None = None, criticidad_id: int | None = None, tipo_id: int | None = None,
              revision: str | None = None, incluir_baja: bool = False,
              pagina: int = Query(1, ge=1), tamano: int = Query(20, ge=1, le=100),
              _: Usuario = Lector, db: Session = Depends(get_db)):
    return cat.buscar_n2(db, q, n1_id, activo, clase_id, criticidad_id, tipo_id, revision, incluir_baja, pagina, tamano)


@router.get("/servicios/{id_}")
def n2_obtener(id_: int, _: Usuario = Lector, db: Session = Depends(get_db)):
    return cat.n2_dict(cat.obtener_n2(db, id_))


@router.post("/servicios", status_code=201)
def n2_crear(datos: dict = Body(...), _: Usuario = Admin, db: Session = Depends(get_db)):
    return cat.guardar_n2(db, datos)


@router.put("/servicios/{id_}")
def n2_actualizar(id_: int, datos: dict = Body(...), _: Usuario = Admin, db: Session = Depends(get_db)):
    return cat.guardar_n2(db, datos, id_)


@router.put("/servicios/{id_}/asignacion")
def n2_asignar(id_: int, datos: dict = Body(...), _: Usuario = Admin, db: Session = Depends(get_db)):
    return cat.asignar(db, id_, datos)


@router.post("/servicios/{id_}/desactivar")
def n2_desactivar(id_: int, _: Usuario = Admin, db: Session = Depends(get_db)):
    return cat.cambiar_baja(db, id_, True)


@router.post("/servicios/{id_}/activar")
def n2_reactivar(id_: int, _: Usuario = Admin, db: Session = Depends(get_db)):
    return cat.cambiar_baja(db, id_, False)


# ------------------------------------------------------------------ importación
@router.post("/importaciones")
def importar_excel(_: Usuario = Admin, db: Session = Depends(get_db)):
    try:
        return importar(db)
    except FileNotFoundError as e:
        raise NegocioError(str(e), 404)


@router.get("/importaciones")
def importaciones(_: Usuario = Lector, db: Session = Depends(get_db)):
    return [org.a_dict(i) for i in db.scalars(select(Importacion).order_by(Importacion.id.desc()).limit(20))]


@router.get("/importaciones/{id_}/observaciones")
def observaciones(id_: int, _: Usuario = Lector, db: Session = Depends(get_db)):
    q = select(ObservacionImportacion).where(ObservacionImportacion.importacion_id == id_).order_by(ObservacionImportacion.id)
    return [org.a_dict(o) for o in db.scalars(q)]
