"""P05 (servicios), P09–P11: mantenimiento, búsqueda y asignación de servicios (integración)."""
import pytest


@pytest.fixture
def base(admin):
    cat = {k: {o["nombre"]: o["id"] for o in admin.get(f"/api/catalogos/{k}").json()}
           for k in ("clases", "criticidades", "tipos")}
    n1a = admin.post("/api/servicios-n1", json={"codigo": "SE.01", "nombre": "Infraestructura"}).json()
    n1b = admin.post("/api/servicios-n1", json={"codigo": "SE.02", "nombre": "Aplicaciones"}).json()

    def srv(codigo, nombre, n1, **extra):
        r = admin.post("/api/servicios", json={"codigo": codigo, "nombre": nombre, "servicio_n1_id": n1["id"], **extra})
        assert r.status_code == 201, r.text
        return r.json()

    s = [
        srv("SE.01.1", "Correo electrónico", n1a, activo="S", clase_id=cat["clases"]["RECURRENTE"],
            criticidad_id=cat["criticidades"]["High"], tipo_id=cat["tipos"]["End User Service"], minimo=95, maximo=100),
        srv("SE.01.2", "Respaldo de servidores", n1a, activo="N", clase_id=cat["clases"]["A DEMANDA"],
            criticidad_id=cat["criticidades"]["Normal"], tipo_id=cat["tipos"]["Back End"]),
        srv("SE.02.1", "Portal de correo web", n1b, activo="S", clase_id=cat["clases"]["RECURRENTE"],
            criticidad_id=cat["criticidades"]["Low"], tipo_id=cat["tipos"]["Front End"]),
        srv("SE.02.2", "Sin datos", n1b),
    ]
    return {"cat": cat, "n1a": n1a, "n1b": n1b, "srv": s}


def test_p05_servicio_duplicado_o_referencia_inexistente(admin, base):
    r = admin.post("/api/servicios", json={"codigo": "se.01.1", "nombre": "Dup", "servicio_n1_id": base["n1a"]["id"]})
    assert r.status_code == 409 and "Ya existe" in r.json()["detail"]
    r = admin.post("/api/servicios", json={"codigo": "SE.09.1", "nombre": "X", "servicio_n1_id": 99999})
    assert r.status_code == 404 and "no existe" in r.json()["detail"]
    r = admin.post("/api/servicios", json={"codigo": "SE.09.1", "nombre": "X", "servicio_n1_id": base["n1a"]["id"],
                                           "clase_id": 99999})
    assert r.status_code == 404
    r = admin.post("/api/servicios-n1", json={"codigo": "SE.01", "nombre": "Dup"})
    assert r.status_code == 409
    r = admin.post("/api/servicios", json={"nombre": "Sin código", "servicio_n1_id": base["n1a"]["id"]})
    assert r.status_code == 422 and "obligatorios" in r.json()["detail"]


def test_p09_minimo_mayor_que_maximo(admin, base):
    r = admin.post("/api/servicios", json={"codigo": "SE.01.9", "nombre": "X", "servicio_n1_id": base["n1a"]["id"],
                                           "minimo": 10, "maximo": 5})
    assert r.status_code == 422 and "mínimo" in r.json()["detail"]
    sid = base["srv"][0]["id"]
    r = admin.put(f"/api/servicios/{sid}", json={"minimo": 101})
    assert r.status_code == 422
    assert admin.get(f"/api/servicios/{sid}").json()["minimo"] == 95  # no se guardó


def test_ausente_no_se_convierte_en_cero(admin, base):
    s = admin.get(f"/api/servicios/{base['srv'][3]['id']}").json()
    assert s["minimo"] is None and s["maximo"] is None
    assert s["activo"] is None and s["activo_texto"] == "DESCONOCIDO"
    assert s["estado_revision"] == "REVISION"


def test_p10_buscar_y_filtrar(consulta, base):
    def codigos(**p):
        return [s["codigo"] for s in consulta.get("/api/servicios", params=p).json()["items"]]

    assert codigos(q="correo") == ["SE.01.1", "SE.02.1"]
    assert codigos(q="SE.02") == ["SE.02.1", "SE.02.2"]
    assert codigos(n1_id=base["n1a"]["id"]) == ["SE.01.1", "SE.01.2"]
    assert codigos(activo="N") == ["SE.01.2"]
    assert codigos(activo="DESCONOCIDO") == ["SE.02.2"]
    assert codigos(clase_id=base["cat"]["clases"]["RECURRENTE"]) == ["SE.01.1", "SE.02.1"]
    assert codigos(criticidad_id=base["cat"]["criticidades"]["High"]) == ["SE.01.1"]
    assert codigos(tipo_id=base["cat"]["tipos"]["Front End"]) == ["SE.02.1"]
    assert codigos(q="correo", activo="S", n1_id=base["n1b"]["id"]) == ["SE.02.1"]
    pag = consulta.get("/api/servicios", params={"tamano": 3, "pagina": 2}).json()
    assert pag["total"] == 4 and pag["paginas"] == 2 and [s["codigo"] for s in pag["items"]] == ["SE.02.2"]


def test_baja_logica_de_servicio(admin, base):
    sid = base["srv"][1]["id"]
    assert admin.post(f"/api/servicios/{sid}/desactivar").json()["dado_de_baja"] is True
    assert "SE.01.2" not in [s["codigo"] for s in admin.get("/api/servicios").json()["items"]]
    assert "SE.01.2" in [s["codigo"] for s in admin.get("/api/servicios?incluir_baja=true").json()["items"]]


def test_ficha_incluye_nivel_1(consulta, base):
    s = consulta.get(f"/api/servicios/{base['srv'][0]['id']}").json()
    assert s["n1"] == {"id": base["n1a"]["id"], "codigo": "SE.01", "nombre": "Infraestructura"}
    for campo in ("codigo", "nombre", "activo", "clase", "criticidad", "tipo", "descripcion", "metrica",
                  "minimo", "maximo", "seccion", "responsable", "origen_rango"):
        assert campo in s


def test_asignacion_valida(admin, base, org):
    sid = base["srv"][0]["id"]
    r = admin.put(f"/api/servicios/{sid}/asignacion",
                  json={"seccion_id": org["s1"].id, "responsable_id": org["admin"].id})
    assert r.status_code == 200
    assert r.json()["seccion"]["codigo"] == "S1" and r.json()["responsable"]["usuario"] == "admin"


def test_p11_responsable_de_otra_seccion(admin, base, org):
    sid = base["srv"][0]["id"]
    r = admin.put(f"/api/servicios/{sid}/asignacion",
                  json={"seccion_id": org["s1"].id, "responsable_id": org["consulta"].id})  # consulta está en S2
    assert r.status_code == 422 and "no pertenece" in r.json()["detail"]
    assert admin.get(f"/api/servicios/{sid}").json()["responsable"] is None
    r = admin.put(f"/api/servicios/{sid}/asignacion", json={"responsable_id": org["admin"].id})
    assert r.status_code == 422  # responsable sin sección


def test_p11_trigger_bd_defensa_en_profundidad(db, base, org):
    """Aunque se salte la API, la BD rechaza un responsable de otra sección."""
    import pytest as _pt
    from sqlalchemy import text
    from sqlalchemy.exc import IntegrityError
    with _pt.raises(IntegrityError):
        db.execute(text("UPDATE servicio_n2 SET seccion_id=:s, responsable_id=:u WHERE id=:id"),
                   {"s": org["s1"].id, "u": org["consulta"].id, "id": base["srv"][0]["id"]})
    db.rollback()
