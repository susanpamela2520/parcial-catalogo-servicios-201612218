"""Reglas del catálogo de servicios (N1, N2, catálogos controlados y asignaciones)."""
from decimal import Decimal, InvalidOperation

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from ..models import (ClaseServicio, Criticidad, Puesto, Seccion, ServicioN1, ServicioN2,
                      TipoServicio, Usuario)
from .errores import NegocioError
from .organizacion import a_dict

CATALOGOS = {
    "clases": (ClaseServicio, "clase de servicio"),
    "criticidades": (Criticidad, "criticidad"),
    "tipos": (TipoServicio, "tipo de servicio"),
}


# ------------------------------------------------------------ catálogos controlados

def catalogo_spec(nombre: str):
    if nombre not in CATALOGOS:
        raise NegocioError(f"Catálogo desconocido: {nombre}", 404)
    return CATALOGOS[nombre]


def listar_catalogo(db: Session, nombre: str, solo_activos: bool = False) -> list[dict]:
    modelo, _ = catalogo_spec(nombre)
    orden = modelo.orden if modelo is Criticidad else modelo.nombre
    q = select(modelo).order_by(orden)
    if solo_activos:
        q = q.where(modelo.activo.is_(True))
    return [a_dict(o) for o in db.scalars(q)]


def guardar_catalogo(db: Session, nombre: str, data: dict, id_: int | None = None) -> dict:
    modelo, etiqueta = catalogo_spec(nombre)
    valor = (data.get("nombre") or "").strip()
    if not valor:
        raise NegocioError("El nombre es obligatorio.")
    q = select(modelo.id).where(func.lower(modelo.nombre) == valor.lower())
    if id_:
        q = q.where(modelo.id != id_)
    if db.scalar(q):
        raise NegocioError(f"Ya existe la {etiqueta} '{valor}'.", 409)
    if id_:
        obj = db.get(modelo, id_)
        if obj is None:
            raise NegocioError(f"No existe la {etiqueta} indicada.", 404)
        obj.nombre = valor
    else:
        obj = modelo(nombre=valor, activo=True)
        if modelo is Criticidad:
            obj.orden = int(data.get("orden") or (db.scalar(select(func.max(Criticidad.orden))) or 0) + 1)
        db.add(obj)
    if "activo" in data:
        obj.activo = bool(data["activo"])
    db.commit()
    return a_dict(obj)


# ------------------------------------------------------------ servicios nivel 1

def n1_dict(o: ServicioN1, total_n2: int | None = None) -> dict:
    d = a_dict(o)
    if total_n2 is not None:
        d["total_n2"] = total_n2
    return d


def listar_n1(db: Session) -> list[dict]:
    conteo = dict(db.execute(select(ServicioN2.servicio_n1_id, func.count()).group_by(ServicioN2.servicio_n1_id)).all())
    return [n1_dict(o, conteo.get(o.id, 0)) for o in db.scalars(select(ServicioN1).order_by(ServicioN1.codigo))]


def guardar_n1(db: Session, data: dict, id_: int | None = None) -> dict:
    obj = db.get(ServicioN1, id_) if id_ else ServicioN1(activo=True, nombres_alternativos=[])
    if obj is None:
        raise NegocioError(f"No existe el servicio de nivel 1 con id {id_}.", 404)
    codigo = (data.get("codigo") or obj.codigo or "").strip()
    nombre = (data.get("nombre") or obj.nombre or "").strip()
    if not codigo or not nombre:
        raise NegocioError("Código y nombre del servicio de nivel 1 son obligatorios.")
    q = select(ServicioN1.id).where(func.upper(ServicioN1.codigo) == codigo.upper())
    if id_:
        q = q.where(ServicioN1.id != id_)
    if db.scalar(q):
        raise NegocioError(f"Ya existe un servicio de nivel 1 con el código '{codigo}'.", 409)
    obj.codigo, obj.nombre = codigo, nombre
    if "activo" in data:
        obj.activo = bool(data["activo"])
    if not id_:
        db.add(obj)
    db.commit()
    return n1_dict(obj)


# ------------------------------------------------------------ servicios nivel 2

def _ref(o, campos=("id", "nombre")):
    return {c: getattr(o, c) for c in campos} if o is not None else None


def n2_dict(o: ServicioN2) -> dict:
    d = a_dict(o)
    for k in ("minimo", "maximo"):
        d[k] = float(d[k]) if d[k] is not None else None
    d["n1"] = _ref(o.n1, ("id", "codigo", "nombre"))
    d["clase"] = _ref(o.clase)
    d["criticidad"] = _ref(o.criticidad)
    d["tipo"] = _ref(o.tipo)
    d["seccion"] = _ref(o.seccion, ("id", "codigo", "nombre"))
    d["responsable"] = _ref(o.responsable, ("id", "nombre", "usuario"))
    d["activo_texto"] = {"S": "S", "N": "N"}.get(o.activo, "DESCONOCIDO")
    return d


def buscar_n2(db: Session, q: str | None = None, n1_id: int | None = None, activo: str | None = None,
              clase_id: int | None = None, criticidad_id: int | None = None, tipo_id: int | None = None,
              revision: str | None = None, incluir_baja: bool = False, pagina: int = 1, tamano: int = 20) -> dict:
    consulta = select(ServicioN2)
    if q:
        patron = f"%{q.strip()}%"
        consulta = consulta.where(or_(ServicioN2.codigo.ilike(patron), ServicioN2.nombre.ilike(patron)))
    if n1_id:
        consulta = consulta.where(ServicioN2.servicio_n1_id == n1_id)
    if activo:
        a = activo.upper()
        if a in ("S", "N"):
            consulta = consulta.where(ServicioN2.activo == a)
        elif a == "DESCONOCIDO":
            consulta = consulta.where(ServicioN2.activo.is_(None))
        else:
            raise NegocioError("El filtro de estado debe ser S, N o DESCONOCIDO.")
    if clase_id:
        consulta = consulta.where(ServicioN2.clase_id == clase_id)
    if criticidad_id:
        consulta = consulta.where(ServicioN2.criticidad_id == criticidad_id)
    if tipo_id:
        consulta = consulta.where(ServicioN2.tipo_id == tipo_id)
    if revision:
        consulta = consulta.where(ServicioN2.estado_revision == revision.upper())
    if not incluir_baja:
        consulta = consulta.where(ServicioN2.dado_de_baja.is_(False))
    tamano = max(1, min(int(tamano), 100))
    pagina = max(1, int(pagina))
    total = db.scalar(select(func.count()).select_from(consulta.subquery()))
    filas = db.scalars(consulta.order_by(ServicioN2.codigo).offset((pagina - 1) * tamano).limit(tamano)).unique()
    return {"total": total, "pagina": pagina, "tamano": tamano,
            "paginas": max(1, -(-total // tamano)), "items": [n2_dict(o) for o in filas]}


def obtener_n2(db: Session, id_: int) -> ServicioN2:
    o = db.get(ServicioN2, id_)
    if o is None:
        raise NegocioError(f"No existe el servicio con id {id_}.", 404)
    return o


def _decimal(valor, campo: str):
    if valor in (None, ""):
        return None  # ausente se mantiene ausente, nunca 0
    try:
        return Decimal(str(valor))
    except InvalidOperation:
        raise NegocioError(f"El campo '{campo}' debe ser numérico.")


def _ref_catalogo(db: Session, modelo, valor, etiqueta: str):
    if valor in (None, ""):
        return None
    obj = db.get(modelo, int(valor))
    if obj is None:
        raise NegocioError(f"La {etiqueta} indicada (id {valor}) no existe.", 404)
    if not obj.activo:
        raise NegocioError(f"La {etiqueta} '{obj.nombre}' está inactiva.", 409)
    return obj.id


def validar_asignacion(db: Session, seccion_id, responsable_id) -> tuple[int | None, int | None]:
    if seccion_id in (None, ""):
        if responsable_id not in (None, ""):
            raise NegocioError("Para asignar un responsable primero debe asignar una sección.")
        return None, None
    seccion = db.get(Seccion, int(seccion_id))
    if seccion is None:
        raise NegocioError(f"La sección indicada (id {seccion_id}) no existe.", 404)
    if not seccion.activo:
        raise NegocioError(f"La sección '{seccion.codigo}' está inactiva.", 409)
    if responsable_id in (None, ""):
        return seccion.id, None
    u = db.get(Usuario, int(responsable_id))
    if u is None:
        raise NegocioError(f"El usuario indicado (id {responsable_id}) no existe.", 404)
    if not u.activo:
        raise NegocioError(f"El usuario '{u.usuario}' está inactivo.", 409)
    puesto = db.get(Puesto, u.puesto_id)
    if puesto.seccion_id != seccion.id:
        raise NegocioError(
            f"El usuario '{u.usuario}' no pertenece a la sección '{seccion.codigo}'. "
            "El responsable debe ser de la sección responsable del servicio.", 422)
    return seccion.id, u.id


def guardar_n2(db: Session, data: dict, id_: int | None = None) -> dict:
    o = obtener_n2(db, id_) if id_ else ServicioN2(dado_de_baja=False)

    def v(campo):  # valor nuevo si viene en el payload, si no el actual
        return data[campo] if campo in data else getattr(o, campo, None)

    codigo = (v("codigo") or "").strip()
    nombre = (v("nombre") or "").strip()
    if not codigo or not nombre:
        raise NegocioError("Código y nombre del servicio son obligatorios.")
    n1_id = v("servicio_n1_id")
    if n1_id in (None, ""):
        raise NegocioError("Debe indicar el servicio de nivel 1 al que pertenece.")
    n1 = db.get(ServicioN1, int(n1_id))
    if n1 is None:
        raise NegocioError(f"El servicio de nivel 1 indicado (id {n1_id}) no existe.", 404)
    if not n1.activo and (not id_ or int(n1_id) != o.servicio_n1_id):
        raise NegocioError(f"El servicio de nivel 1 '{n1.codigo}' está inactivo.", 409)
    q = select(ServicioN2.id).where(func.upper(ServicioN2.codigo) == codigo.upper())
    if id_:
        q = q.where(ServicioN2.id != id_)
    if db.scalar(q):
        raise NegocioError(f"Ya existe un servicio de nivel 2 con el código '{codigo}'.", 409)

    activo = v("activo")
    activo = activo.strip().upper() if isinstance(activo, str) and activo.strip() else None
    if activo not in (None, "S", "N"):
        raise NegocioError("ACTIVO debe ser 'S', 'N' o vacío (desconocido).")

    minimo, maximo = _decimal(v("minimo"), "minimo"), _decimal(v("maximo"), "maximo")
    if minimo is not None and maximo is not None and minimo > maximo:
        raise NegocioError("El valor mínimo no puede ser mayor que el máximo.")

    clase_id = _ref_catalogo(db, ClaseServicio, v("clase_id"), "clase de servicio") if "clase_id" in data else o.clase_id
    crit_id = _ref_catalogo(db, Criticidad, v("criticidad_id"), "criticidad") if "criticidad_id" in data else o.criticidad_id
    tipo_id = _ref_catalogo(db, TipoServicio, v("tipo_id"), "tipo de servicio") if "tipo_id" in data else o.tipo_id

    if "seccion_id" in data or "responsable_id" in data:
        o.seccion_id, o.responsable_id = validar_asignacion(db, v("seccion_id"), v("responsable_id"))

    o.codigo, o.nombre, o.servicio_n1_id = codigo, nombre, n1.id
    o.activo, o.clase_id, o.criticidad_id, o.tipo_id = activo, clase_id, crit_id, tipo_id
    o.descripcion = (v("descripcion") or None)
    o.metrica = (v("metrica") or None)
    o.minimo, o.maximo = minimo, maximo
    if data.get("estado_revision") in ("OK", "REVISION"):
        o.estado_revision = data["estado_revision"]
    elif None in (activo, clase_id, crit_id, tipo_id):
        o.estado_revision = "REVISION"
    else:
        o.estado_revision = "OK"
    if not id_:
        db.add(o)
    db.commit()
    db.refresh(o)
    return n2_dict(o)


def asignar(db: Session, id_: int, data: dict) -> dict:
    o = obtener_n2(db, id_)
    o.seccion_id, o.responsable_id = validar_asignacion(db, data.get("seccion_id"), data.get("responsable_id"))
    db.commit()
    db.refresh(o)
    return n2_dict(o)


def cambiar_baja(db: Session, id_: int, baja: bool) -> dict:
    o = obtener_n2(db, id_)
    o.dado_de_baja = baja
    db.commit()
    db.refresh(o)
    return n2_dict(o)
