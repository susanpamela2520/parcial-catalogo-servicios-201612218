"""Dependencias de FastAPI: sesión de BD y autorización en el servidor."""
from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from . import config
from .db import get_db
from .models import Usuario
from .security import usuario_de_token


def usuario_actual(request: Request, db: Session = Depends(get_db)) -> Usuario:
    u = usuario_de_token(db, request.cookies.get(config.COOKIE_NAME))
    if u is None:
        raise HTTPException(status_code=401, detail="Sesión no válida o expirada. Inicie sesión.")
    return u


def requiere_admin(u: Usuario = Depends(usuario_actual)) -> Usuario:
    if u.rol != "administrador":
        raise HTTPException(status_code=403, detail="Operación permitida solo para administradores.")
    return u
