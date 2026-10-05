"""Apoyo de scripts/p12_persistencia.sh. Crea, verifica y retira una empresa marcadora inactiva.

Solo toca su propio registro (código P12-*), nunca datos de evaluación.
"""
import sys

from sqlalchemy import delete, select

from app.db import SessionLocal
from app.models import Empresa


def main(accion: str, codigo: str) -> int:
    if not codigo.startswith("P12-"):
        print("código de control inválido")
        return 1
    db = SessionLocal()
    try:
        if accion == "crear":
            db.add(Empresa(codigo=codigo, nombre="Registro de control P12 (temporal)", activo=False))
            db.commit()
            return 0
        existe = db.scalar(select(Empresa.id).where(Empresa.codigo == codigo)) is not None
        print(f"[P12] registro {codigo}: {'encontrado' if existe else 'NO encontrado'}")
        db.execute(delete(Empresa).where(Empresa.codigo == codigo))
        db.commit()
        return 0 if existe else 1
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
