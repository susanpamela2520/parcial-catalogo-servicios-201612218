"""P01–P03: autenticación local y autorización en el servidor (pruebas de integración API + BD)."""
from sqlalchemy import select

from app.models import Sesion, Usuario
from conftest import PW_ADMIN, PW_CONSULTA, login


def test_p01_login_valido_por_usuario_y_correo(cliente, org):
    r = login(cliente, "admin", PW_ADMIN)
    assert r.status_code == 200
    assert r.json()["usuario"]["rol"] == "administrador"
    assert "password_hash" not in r.json()["usuario"]
    assert cliente.get("/api/auth/me").status_code == 200
    assert login(cliente, "CONSULTA@x.test", PW_CONSULTA).status_code == 200


def test_p01_login_invalido(cliente, org):
    for usuario, pw in (("admin", "incorrecta"), ("noexiste", PW_ADMIN), ("", "")):
        r = login(cliente, usuario, pw)
        assert r.status_code == 401
        assert r.json()["detail"] == "Usuario o contraseña incorrectos."
    assert cliente.get("/api/auth/me").status_code == 401


def test_p01_hash_con_sal_no_texto_plano(db, org):
    u = db.scalar(select(Usuario).where(Usuario.usuario == "admin"))
    assert u.password_hash.startswith("$argon2id$")
    assert PW_ADMIN not in u.password_hash
    otro = db.scalar(select(Usuario).where(Usuario.usuario == "consulta"))
    assert u.password_hash.split("$")[4] != otro.password_hash.split("$")[4]  # sales distintas


def test_p02_sin_sesion_rechazado(cliente, org):
    for metodo, ruta in (("get", "/api/servicios"), ("get", "/api/usuarios"), ("post", "/api/org/empresas"),
                         ("post", "/api/importaciones")):
        r = getattr(cliente, metodo)(ruta, **({"json": {}} if metodo == "post" else {}))
        assert r.status_code == 401, ruta


def test_p02_logout_invalida_la_sesion(cliente, org, db):
    login(cliente, "admin", PW_ADMIN)
    token = cliente.cookies.get("catalogo_sesion")
    assert cliente.post("/api/auth/logout").status_code == 200
    # reutilizar el token anterior manualmente debe fallar: la sesión quedó revocada en BD
    cliente.cookies.set("catalogo_sesion", token)
    assert cliente.get("/api/servicios").status_code == 401
    assert db.scalar(select(Sesion.revocada_en)) is not None


def test_p02_usuario_inactivo(admin, org):
    from fastapi.testclient import TestClient
    from app.main import app
    with TestClient(app) as c:
        assert login(c, "consulta", PW_CONSULTA).status_code == 200
        assert admin.post(f"/api/usuarios/{org['consulta'].id}/desactivar").status_code == 200
        assert c.get("/api/servicios").status_code == 401  # sesión existente queda sin efecto
        assert login(c, "consulta", PW_CONSULTA).status_code == 401  # no puede volver a entrar


def test_p03_consulta_lee_pero_no_modifica(consulta, org):
    assert consulta.get("/api/servicios").status_code == 200
    assert consulta.get("/api/org/empresas").status_code == 200
    usuarios = consulta.get("/api/usuarios").json()
    assert usuarios and all("password_hash" not in u for u in usuarios)
    intentos = [
        ("post", "/api/org/empresas", {"codigo": "X", "nombre": "X"}),
        ("put", f"/api/org/empresas/{org['empresa'].id}", {"nombre": "Hack"}),
        ("post", f"/api/org/empresas/{org['empresa'].id}/desactivar", None),
        ("post", "/api/usuarios", {"nombre": "x", "usuario": "x", "rol": "administrador", "password": "12345678",
                                   "puesto_id": org["p1"].id}),
        ("post", "/api/servicios", {"codigo": "X", "nombre": "X"}),
        ("post", "/api/catalogos/clases", {"nombre": "X"}),
        ("post", "/api/importaciones", None),
    ]
    for metodo, ruta, cuerpo in intentos:
        r = getattr(consulta, metodo)(ruta, **({"json": cuerpo} if cuerpo is not None else {}))
        assert r.status_code == 403, ruta
    assert consulta.get(f"/api/org/empresas/{org['empresa'].id}").json()["nombre"] == "Empresa Prueba"
