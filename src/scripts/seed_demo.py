"""Crea (o actualiza) la estructura organizacional de demostración, las cuentas de evaluación
y tres asignaciones de servicios. Es idempotente: puede ejecutarse varias veces.

Uso: python -m scripts.seed_demo
Las contraseñas se leen de variables de entorno (DEMO_ADMIN_PASSWORD, DEMO_CONSULTA_PASSWORD);
no hay contraseñas en el código. Los datos organizacionales son FICTICIOS, no provienen del Excel.
"""
import os
import sys

from sqlalchemy import select

from app.db import SessionLocal
from app.models import Area, Departamento, Empresa, Puesto, Seccion, ServicioN2, Usuario
from app.security import hash_password
from app.services.catalogo import validar_asignacion

ORG = {
    "empresa": ("DEMO", "Organización Demo S.A."),
    "area": ("TI", "Tecnología de la Información"),
    "departamentos": {
        "INFRA": ("Infraestructura", {
            "REDES": ("Redes y Comunicaciones", [("ING-RED", "Ingeniero de Redes")]),
            "SOPORTE": ("Soporte a Usuarios", [("TEC-SOP", "Técnico de Soporte")]),
        }),
        "DESA": ("Desarrollo", {
            "APPS": ("Aplicaciones", [("DEV", "Desarrollador"), ("JEFE-APP", "Jefe de Aplicaciones")]),
        }),
    },
}


def get_or_create(db, modelo, filtros: dict, valores: dict):
    obj = db.scalar(select(modelo).filter_by(**filtros))
    if obj is None:
        obj = modelo(**filtros, **valores)
        db.add(obj)
        db.flush()
    return obj


def requerido(var: str) -> str:
    v = os.getenv(var)
    if not v or len(v) < 8:
        sys.exit(f"[seed] Defina {var} (mínimo 8 caracteres) en su archivo .env")
    return v


def usuario(db, nombre, login, correo, rol, puesto, password):
    u = db.scalar(select(Usuario).where(Usuario.usuario == login))
    if u is None:
        u = Usuario(usuario=login, nombre=nombre, correo=correo, rol=rol, puesto_id=puesto.id,
                    password_hash=hash_password(password), activo=True)
        db.add(u)
    else:  # deja la cuenta en estado conocido para la evaluación
        u.nombre, u.correo, u.rol, u.puesto_id, u.activo = nombre, correo, rol, puesto.id, True
        u.password_hash = hash_password(password)
    db.flush()
    return u


def main() -> int:
    admin_user = os.getenv("DEMO_ADMIN_USUARIO", "admin")
    consulta_user = os.getenv("DEMO_CONSULTA_USUARIO", "consulta")
    admin_pw = requerido("DEMO_ADMIN_PASSWORD")
    consulta_pw = requerido("DEMO_CONSULTA_PASSWORD")

    db = SessionLocal()
    try:
        e = get_or_create(db, Empresa, {"codigo": ORG["empresa"][0]}, {"nombre": ORG["empresa"][1], "activo": True})
        a = get_or_create(db, Area, {"empresa_id": e.id, "codigo": ORG["area"][0]}, {"nombre": ORG["area"][1], "activo": True})
        puestos, secciones = {}, {}
        for dcod, (dnom, secs) in ORG["departamentos"].items():
            d = get_or_create(db, Departamento, {"area_id": a.id, "codigo": dcod}, {"nombre": dnom, "activo": True})
            for scod, (snom, pts) in secs.items():
                s = get_or_create(db, Seccion, {"departamento_id": d.id, "codigo": scod}, {"nombre": snom, "activo": True})
                secciones[scod] = s
                for pcod, pnom in pts:
                    puestos[pcod] = get_or_create(db, Puesto, {"seccion_id": s.id, "codigo": pcod}, {"nombre": pnom, "activo": True})

        usuario(db, "Administrador de Evaluación", admin_user, "admin@demo.local", "administrador", puestos["JEFE-APP"], admin_pw)
        usuario(db, "Usuario de Consulta", consulta_user, "consulta@demo.local", "consulta", puestos["TEC-SOP"], consulta_pw)
        resp_red = usuario(db, "Ana Redes (demo)", "ana.redes", "ana.redes@demo.local", "consulta", puestos["ING-RED"], consulta_pw)
        resp_dev = usuario(db, "Luis Apps (demo)", "luis.apps", "luis.apps@demo.local", "consulta", puestos["DEV"], consulta_pw)
        db.commit()
        print(f"[seed] estructura organizacional demo y cuentas '{admin_user}' (administrador) y '{consulta_user}' (consulta) listas")

        servicios = list(db.scalars(select(ServicioN2).order_by(ServicioN2.codigo).limit(3)))
        if len(servicios) < 3:
            print("[seed] aún no hay servicios importados: ejecute 'python -m scripts.import_excel' y luego repita este comando "
                  "para crear las 3 asignaciones de demostración")
            return 0
        plan = [(servicios[0], secciones["REDES"], resp_red),
                (servicios[1], secciones["APPS"], resp_dev),
                (servicios[2], secciones["SOPORTE"], None)]
        for srv, sec, resp in plan:
            srv.seccion_id, srv.responsable_id = validar_asignacion(db, sec.id, resp.id if resp else None)
            print(f"[seed] {srv.codigo} -> sección {sec.codigo}" + (f", responsable {resp.usuario}" if resp else ""))
        db.commit()
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
