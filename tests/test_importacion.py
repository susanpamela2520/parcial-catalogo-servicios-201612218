"""P06–P08: importación del Excel.

- test_p06/p07/p08_*: usan el archivo ORIGINAL data/CatalogoServicios.xlsx (prueba de integración real).
- test_regla_*: usan un Excel SINTÉTICO generado en tiempo de prueba (tests/fixtures/excel_sintetico.py)
  para comprobar cada regla de forma controlada (pruebas unitarias/integración del importador).
"""
import hashlib

import pytest
from sqlalchemy import func, select

from app import config
from app.importador import importar
from app.models import ObservacionImportacion, ServicioN1, ServicioN2
from fixtures.excel_sintetico import generar


def _original():
    if not config.EXCEL_PATH.exists():
        pytest.fail(f"Falta el archivo original {config.EXCEL_PATH}. Colóquelo en data/CatalogoServicios.xlsx")
    return config.EXCEL_PATH


def _obs(db, imp_id, tipo=None, codigo=None):
    q = select(ObservacionImportacion).where(ObservacionImportacion.importacion_id == imp_id)
    if tipo:
        q = q.where(ObservacionImportacion.tipo == tipo)
    if codigo:
        q = q.where(ObservacionImportacion.codigo == codigo)
    return list(db.scalars(q))


# ------------------------------------------------------------------ archivo original

def test_p06_importar_archivo_original(db):
    ruta = _original()
    sha = hashlib.sha256(ruta.read_bytes()).hexdigest()
    r = importar(db, ruta)
    assert r["control"]["n1_encontrados"] == 12
    assert r["control"]["n2_encontrados"] == 46
    assert db.scalar(select(func.count()).select_from(ServicioN1)) == 12
    assert db.scalar(select(func.count()).select_from(ServicioN2)) == 46
    assert r["observaciones"] > 0 and _obs(db, r["importacion_id"])
    assert r["n2"]["creados"] == 46 and r["n1"]["creados"] == 12
    assert hashlib.sha256(ruta.read_bytes()).hexdigest() == sha  # el original no se modificó
    sin_origen = db.scalar(select(func.count()).select_from(ServicioN2).where(ServicioN2.origen_rango.is_(None)))
    assert sin_origen == 0  # trazabilidad hoja/rango


def test_p07_repetir_importacion_sin_duplicados(db):
    ruta = _original()
    importar(db, ruta)
    r2 = importar(db, ruta)
    assert r2["n1"]["creados"] == 0 and r2["n2"]["creados"] == 0
    assert r2["n2"]["sin_cambios"] == 46 and r2["n1"]["sin_cambios"] == 12
    assert db.scalar(select(func.count()).select_from(ServicioN2)) == 46
    assert r2["importacion_id"] == 2  # cada ejecución queda registrada


def test_p08_conflicto_se12_y_ausencias(db):
    r = importar(db, _original())
    se12 = db.scalar(select(ServicioN1).where(ServicioN1.codigo == "SE.12"))
    assert se12.nombre == "Suministrar Analitica"
    alternativos = {n["valor"] for n in se12.nombres_alternativos}
    assert {"Suministrar Analitica", "Mantener Tableros de Control"} <= alternativos
    assert _obs(db, r["importacion_id"], "CONFLICTO_NOMBRE_N1", "SE.12")
    for cod in ("SE.12.1", "SE.12.2", "SE.12.3"):
        s = db.scalar(select(ServicioN2).where(ServicioN2.codigo == cod))
        assert s is not None, cod
        assert isinstance(s.codigo, str) and s.n1.codigo == "SE.12"
        assert s.estado_revision == "REVISION"
    sin_datos = list(db.scalars(select(ServicioN2).where(ServicioN2.codigo.in_(["SE.12.1", "SE.12.2", "SE.12.3"]))))
    # nada inventado: lo que falta en el Excel queda NULL, con observación
    for s in sin_datos:
        if s.criticidad_original is None:
            assert s.criticidad_id is None
        if s.activo_original is None:
            assert s.activo is None
        if s.metrica is None:
            assert any("metrica" in (o.detalle or {}).get("campos", []) for o in _obs(db, r["importacion_id"], "ATRIBUTO_AUSENTE", s.codigo))


# ------------------------------------------------------------------ reglas con Excel sintético

@pytest.fixture
def sintetico(tmp_path):
    return generar(tmp_path / "sintetico.xlsx")


def test_regla_conteos_y_celdas_combinadas(db, sintetico):
    r = importar(db, sintetico)
    assert r["control"]["ok"] and r["filas_continuacion"] == 11
    # SE.01.4 ocupa 2 filas combinadas: un solo servicio con el valor de la celda principal
    s = db.scalar(select(ServicioN2).where(ServicioN2.codigo == "SE.02.1"))
    assert s.n1.codigo == "SE.02" and s.n1.nombre == "Servicio nivel 1 número 2"


def test_regla_fila_sin_codigo_no_se_asigna(db, sintetico):
    r = importar(db, sintetico)
    obs = _obs(db, r["importacion_id"], "FILA_SIN_CODIGO")
    assert len(obs) == 1 and r["filas_omitidas"] == 1
    # el texto de la celda es dato, no instrucción: la tabla sigue intacta
    assert db.scalar(select(func.count()).select_from(ServicioN2)) == 46
    assert not db.scalar(select(func.count()).select_from(ServicioN2).where(ServicioN2.metrica == "Texto huérfano"))


def test_regla_conflicto_atributo_en_continuacion(db, sintetico):
    r = importar(db, sintetico)
    s = db.scalar(select(ServicioN2).where(ServicioN2.codigo == "SE.05.4"))
    assert s.metrica == "Disponibilidad %"  # se conserva el de la fila principal
    assert {v["valor"] for v in s.origen_valores["metrica"]} == {"Disponibilidad %", "Tiempo de respuesta"}
    assert _obs(db, r["importacion_id"], "CONFLICTO_ATRIBUTO", "SE.05.4")


def test_regla_codigo_normalizado_conserva_original(db, sintetico):
    r = importar(db, sintetico)
    s = db.scalar(select(ServicioN2).where(ServicioN2.codigo == "SE.03.2"))
    assert s.codigo_original == " se.03.2 "
    assert _obs(db, r["importacion_id"], "CODIGO_NORMALIZADO", "SE.03.2")


def test_regla_etiqueta_mapeada(db, sintetico):
    importar(db, sintetico)
    s = db.scalar(select(ServicioN2).where(ServicioN2.codigo == "SE.04.1"))
    assert s.tipo.nombre == "Back End" and s.tipo_original == "back end"


def test_regla_reimportacion_respeta_ediciones(admin, db, sintetico):
    importar(db, sintetico)
    s = db.scalar(select(ServicioN2).where(ServicioN2.codigo == "SE.12.2"))
    admin.put(f"/api/servicios/{s.id}", json={"activo": "S"})
    r = importar(db, sintetico)
    db.expire_all()
    assert r["n2"]["sin_cambios"] == 46
    assert db.get(ServicioN2, s.id).activo == "S"


def test_importacion_por_api(admin, consulta, monkeypatch, sintetico):
    monkeypatch.setattr(config, "EXCEL_PATH", sintetico)
    assert consulta.post("/api/importaciones").status_code == 403
    r = admin.post("/api/importaciones")
    assert r.status_code == 200 and r.json()["control"]["ok"]
    imp = admin.get("/api/importaciones").json()[0]
    assert consulta.get(f"/api/importaciones/{imp['id']}/observaciones").status_code == 200


def test_regla_n1_derivado_del_codigo(db, sintetico):
    r = importar(db, sintetico)
    s = db.scalar(select(ServicioN2).where(ServicioN2.codigo == "SE.12.3"))
    assert s is not None and s.n1.codigo == "SE.12" and s.estado_revision == "REVISION"
    assert _obs(db, r["importacion_id"], "N1_DERIVADO_DEL_CODIGO", "SE.12.3")
    assert _obs(db, r["importacion_id"], "ENCABEZADO_LISTA_OPCIONES")
