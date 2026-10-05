"""Hash de contraseñas (Argon2id, con sal aleatoria) y sesiones del lado del servidor."""
import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from . import config
from .models import Sesion, Usuario

_ph = PasswordHasher()  # Argon2id; la sal se genera en cada hash y va dentro del resultado

# Hash fijo para igualar el tiempo de respuesta cuando el usuario no existe
_HASH_FICTICIO = _ph.hash("contrasena-ficticia-para-tiempo-constante")


def hash_password(password: str) -> str:
    return _ph.hash(password)


def verificar_password(password_hash: str, password: str) -> bool:
    try:
        return _ph.verify(password_hash, password)
    except (VerificationError, InvalidHashError):
        return False


def _sha256(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def autenticar(db: Session, identificador: str, password: str) -> Usuario | None:
    ident = identificador.strip().lower()
    u = db.scalar(select(Usuario).where(
        (func.lower(Usuario.usuario) == ident) | (func.lower(Usuario.correo) == ident)
    ))
    if u is None:
        verificar_password(_HASH_FICTICIO, password)
        return None
    if not verificar_password(u.password_hash, password) or not u.activo:
        return None
    return u


def crear_sesion(db: Session, usuario: Usuario) -> str:
    token = secrets.token_urlsafe(32)
    db.add(Sesion(
        token_hash=_sha256(token),
        usuario_id=usuario.id,
        expira_en=datetime.now(timezone.utc) + timedelta(hours=config.SESSION_HOURS),
    ))
    db.commit()
    return token


def usuario_de_token(db: Session, token: str | None) -> Usuario | None:
    if not token:
        return None
    s = db.get(Sesion, _sha256(token))
    if s is None or s.revocada_en is not None or s.expira_en <= datetime.now(timezone.utc):
        return None
    u = db.get(Usuario, s.usuario_id)
    if u is None or not u.activo:  # un usuario desactivado pierde el acceso de inmediato
        return None
    return u


def revocar_sesion(db: Session, token: str | None) -> None:
    if token:
        db.execute(update(Sesion).where(Sesion.token_hash == _sha256(token), Sesion.revocada_en.is_(None))
                   .values(revocada_en=func.now()))
        db.commit()


def revocar_sesiones_usuario(db: Session, usuario_id: int) -> None:
    db.execute(update(Sesion).where(Sesion.usuario_id == usuario_id, Sesion.revocada_en.is_(None))
               .values(revocada_en=func.now()))
