"""Importa data/CatalogoServicios.xlsx y muestra el resumen.

Uso: python -m scripts.import_excel [--archivo RUTA] [--hoja NOMBRE] [--observaciones]
Código de salida: 0 si los controles 12/46 coinciden, 2 si no coinciden, 1 si hubo error.
"""
import argparse
import json
import sys

from sqlalchemy import select

from app.db import SessionLocal
from app.importador import importar
from app.models import ObservacionImportacion


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--archivo")
    p.add_argument("--hoja")
    p.add_argument("--observaciones", action="store_true", help="imprimir el detalle de observaciones")
    args = p.parse_args()
    db = SessionLocal()
    try:
        r = importar(db, args.archivo, args.hoja)
    except Exception as exc:  # noqa: BLE001
        print(f"[import] ERROR: {exc}")
        return 1
    print("[import] resumen:")
    print(json.dumps({k: v for k, v in r.items() if k != "servicios_observados"}, indent=2, ensure_ascii=False))
    print(f"[import] servicios con observaciones: {', '.join(r['servicios_observados']) or 'ninguno'}")
    if args.observaciones:
        for o in db.scalars(select(ObservacionImportacion).where(ObservacionImportacion.importacion_id == r["importacion_id"])):
            print(f"  - [{o.tipo}] {o.rango or ''} {o.codigo or ''}: {o.mensaje}")
    db.close()
    return 0 if r["control"]["ok"] else 2


if __name__ == "__main__":
    sys.exit(main())
