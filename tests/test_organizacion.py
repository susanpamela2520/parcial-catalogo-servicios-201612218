"""P04–P05 y política de desactivación de la jerarquía organizacional (integración)."""


def crear(c, ent, **datos):
    return c.post(f"/api/org/{ent}", json=datos)


def test_p04_crear_jerarquia_y_asignar_usuario(admin):
    e = crear(admin, "empresas", codigo="ACME", nombre="Acme").json()
    a = crear(admin, "areas", codigo="OPS", nombre="Operaciones", empresa_id=e["id"]).json()
    d = crear(admin, "departamentos", codigo="SOP", nombre="Soporte", area_id=a["id"]).json()
    s = crear(admin, "secciones", codigo="MESA", nombre="Mesa de ayuda", departamento_id=d["id"]).json()
    p = crear(admin, "puestos", codigo="AG", nombre="Agente", seccion_id=s["id"]).json()
    r = admin.post("/api/usuarios", json={"nombre": "María", "usuario": "maria", "correo": "maria@acme.test",
                                          "rol": "consulta", "password": "Segura-123", "puesto_id": p["id"]})
    assert r.status_code == 201, r.text
    u = admin.get(f"/api/usuarios/{r.json()['id']}").json()
    ruta = u["organizacion"]
    assert ruta["empresa"]["codigo"] == "ACME"  # empresa derivada de la jerarquía
    assert (ruta["area"]["id"], ruta["departamento"]["id"], ruta["seccion"]["id"], ruta["puesto"]["id"]) == \
           (a["id"], d["id"], s["id"], p["id"])
    assert [x["codigo"] for x in admin.get(f"/api/org/puestos?padre_id={s['id']}").json()] == ["AG"]
    # un puesto puede tener varios usuarios
    r2 = admin.post("/api/usuarios", json={"nombre": "Pedro", "usuario": "pedro", "rol": "consulta",
                                           "password": "Segura-123", "puesto_id": p["id"]})
    assert r2.status_code == 201
    assert len(admin.get("/api/usuarios", params={"puesto_id": p["id"]}).json()) == 2


def test_p05_codigo_duplicado(admin, org):
    r = crear(admin, "empresas", codigo="emp", nombre="Otra")  # sin distinguir mayúsculas
    assert r.status_code == 409 and "Ya existe" in r.json()["detail"]
    r = crear(admin, "secciones", codigo="S1", nombre="Dup", departamento_id=org["departamento"].id)
    assert r.status_code == 409
    # mismo código en otro padre sí es válido (único dentro del padre)
    d2 = crear(admin, "departamentos", codigo="OTRO", nombre="Otro", area_id=org["area"].id).json()
    assert crear(admin, "secciones", codigo="S1", nombre="Ok", departamento_id=d2["id"]).status_code == 201
    r = admin.post("/api/usuarios", json={"nombre": "x", "usuario": "ADMIN", "rol": "consulta",
                                          "password": "Segura-123", "puesto_id": org["p1"].id})
    assert r.status_code == 409 and "ya está registrado" in r.json()["detail"]


def test_p05_referencia_inexistente_o_huerfano(admin, org):
    r = crear(admin, "areas", codigo="X", nombre="X", empresa_id=99999)
    assert r.status_code == 404 and "no existe" in r.json()["detail"]
    r = crear(admin, "areas", codigo="X", nombre="X")
    assert r.status_code == 422 and "Debe indicar" in r.json()["detail"]
    r = admin.post("/api/usuarios", json={"nombre": "x", "usuario": "x", "rol": "consulta",
                                          "password": "Segura-123", "puesto_id": 99999})
    assert r.status_code == 404


def test_no_asociar_a_padre_inactivo(admin, org):
    d2 = crear(admin, "departamentos", codigo="D2", nombre="D2", area_id=org["area"].id).json()
    assert admin.post(f"/api/org/departamentos/{d2['id']}/desactivar").status_code == 200
    r = crear(admin, "secciones", codigo="NEW", nombre="Nueva", departamento_id=d2["id"])
    assert r.status_code == 409 and "inactiva" in r.json()["detail"]


def test_desactivar_con_dependientes_requiere_cascada(admin, org):
    r = admin.post(f"/api/org/secciones/{org['s2'].id}/desactivar")
    assert r.status_code == 409
    assert {d["tipo"] for d in r.json()["dependientes"]} == {"puesto", "usuario"}
    r = admin.post(f"/api/org/secciones/{org['s2'].id}/desactivar?cascada=true")
    assert r.status_code == 200
    assert len(r.json()["desactivados"]) == 3  # sección + puesto + usuario
    # nada se borra: los registros siguen existiendo, inactivos
    assert admin.get(f"/api/org/puestos/{org['p2'].id}").json()["activo"] is False
    assert admin.get(f"/api/usuarios/{org['consulta'].id}").json()["activo"] is False
    # reactivar un hijo con padre inactivo se rechaza
    assert admin.post(f"/api/org/puestos/{org['p2'].id}/activar").status_code == 409


def test_admin_no_puede_desactivarse_a_si_mismo(admin, org):
    assert admin.post(f"/api/usuarios/{org['admin'].id}/desactivar").status_code == 409
