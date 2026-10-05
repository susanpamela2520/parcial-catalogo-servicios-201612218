"""Modelos ORM. El esquema lo crean las migraciones SQL de /migrations, no create_all()."""
from datetime import datetime
from decimal import Decimal

from sqlalchemy import ForeignKey, String, Text, Numeric, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


class Auditable:
    creado_en: Mapped[datetime] = mapped_column(server_default=func.now())
    actualizado_en: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())


class Empresa(Auditable, Base):
    __tablename__ = "empresa"
    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(30))
    nombre: Mapped[str] = mapped_column(String(200))
    activo: Mapped[bool] = mapped_column(default=True)


class Area(Auditable, Base):
    __tablename__ = "area"
    id: Mapped[int] = mapped_column(primary_key=True)
    empresa_id: Mapped[int] = mapped_column(ForeignKey("empresa.id"))
    codigo: Mapped[str] = mapped_column(String(30))
    nombre: Mapped[str] = mapped_column(String(200))
    activo: Mapped[bool] = mapped_column(default=True)


class Departamento(Auditable, Base):
    __tablename__ = "departamento"
    id: Mapped[int] = mapped_column(primary_key=True)
    area_id: Mapped[int] = mapped_column(ForeignKey("area.id"))
    codigo: Mapped[str] = mapped_column(String(30))
    nombre: Mapped[str] = mapped_column(String(200))
    activo: Mapped[bool] = mapped_column(default=True)


class Seccion(Auditable, Base):
    __tablename__ = "seccion"
    id: Mapped[int] = mapped_column(primary_key=True)
    departamento_id: Mapped[int] = mapped_column(ForeignKey("departamento.id"))
    codigo: Mapped[str] = mapped_column(String(30))
    nombre: Mapped[str] = mapped_column(String(200))
    activo: Mapped[bool] = mapped_column(default=True)


class Puesto(Auditable, Base):
    __tablename__ = "puesto"
    id: Mapped[int] = mapped_column(primary_key=True)
    seccion_id: Mapped[int] = mapped_column(ForeignKey("seccion.id"))
    codigo: Mapped[str] = mapped_column(String(30))
    nombre: Mapped[str] = mapped_column(String(200))
    activo: Mapped[bool] = mapped_column(default=True)


class Usuario(Auditable, Base):
    __tablename__ = "usuario"
    id: Mapped[int] = mapped_column(primary_key=True)
    puesto_id: Mapped[int] = mapped_column(ForeignKey("puesto.id"))
    nombre: Mapped[str] = mapped_column(String(200))
    usuario: Mapped[str] = mapped_column(String(80))
    correo: Mapped[str | None] = mapped_column(String(200))
    password_hash: Mapped[str] = mapped_column(String(255))
    rol: Mapped[str] = mapped_column(String(20))
    activo: Mapped[bool] = mapped_column(default=True)

    puesto: Mapped[Puesto] = relationship(lazy="joined")


class Sesion(Base):
    __tablename__ = "sesion"
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuario.id"))
    creada_en: Mapped[datetime] = mapped_column(server_default=func.now())
    expira_en: Mapped[datetime]
    revocada_en: Mapped[datetime | None]


class ClaseServicio(Base):
    __tablename__ = "clase_servicio"
    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(80))
    activo: Mapped[bool] = mapped_column(default=True)


class Criticidad(Base):
    __tablename__ = "criticidad"
    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(80))
    orden: Mapped[int]
    activo: Mapped[bool] = mapped_column(default=True)


class TipoServicio(Base):
    __tablename__ = "tipo_servicio"
    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(80))
    activo: Mapped[bool] = mapped_column(default=True)


class MapeoEtiqueta(Base):
    __tablename__ = "mapeo_etiqueta"
    id: Mapped[int] = mapped_column(primary_key=True)
    campo: Mapped[str] = mapped_column(String(40))
    valor_original: Mapped[str] = mapped_column(String(200))
    valor_canonico: Mapped[str] = mapped_column(String(200))
    motivo: Mapped[str] = mapped_column(String(300))


class ServicioN1(Auditable, Base):
    __tablename__ = "servicio_n1"
    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(40))
    codigo_original: Mapped[str | None] = mapped_column(String(80))
    nombre: Mapped[str] = mapped_column(String(300))
    nombres_alternativos: Mapped[list] = mapped_column(JSONB, default=list)
    activo: Mapped[bool] = mapped_column(default=True)
    origen_hoja: Mapped[str | None] = mapped_column(String(100))
    origen_rango: Mapped[str | None] = mapped_column(String(100))
    origen_hash: Mapped[str | None] = mapped_column(String(64))


class ServicioN2(Auditable, Base):
    __tablename__ = "servicio_n2"
    id: Mapped[int] = mapped_column(primary_key=True)
    servicio_n1_id: Mapped[int] = mapped_column(ForeignKey("servicio_n1.id"))
    codigo: Mapped[str] = mapped_column(String(40))
    codigo_original: Mapped[str | None] = mapped_column(String(80))
    nombre: Mapped[str] = mapped_column(String(300))
    activo: Mapped[str | None] = mapped_column(String(1))
    activo_original: Mapped[str | None] = mapped_column(String(80))
    clase_id: Mapped[int | None] = mapped_column(ForeignKey("clase_servicio.id"))
    clase_original: Mapped[str | None] = mapped_column(String(200))
    criticidad_id: Mapped[int | None] = mapped_column(ForeignKey("criticidad.id"))
    criticidad_original: Mapped[str | None] = mapped_column(String(200))
    tipo_id: Mapped[int | None] = mapped_column(ForeignKey("tipo_servicio.id"))
    tipo_original: Mapped[str | None] = mapped_column(String(200))
    descripcion: Mapped[str | None] = mapped_column(Text)
    metrica: Mapped[str | None] = mapped_column(Text)
    minimo: Mapped[Decimal | None] = mapped_column(Numeric(18, 4))
    minimo_original: Mapped[str | None] = mapped_column(String(80))
    maximo: Mapped[Decimal | None] = mapped_column(Numeric(18, 4))
    maximo_original: Mapped[str | None] = mapped_column(String(80))
    dado_de_baja: Mapped[bool] = mapped_column(default=False)
    estado_revision: Mapped[str] = mapped_column(String(20), default="OK")
    seccion_id: Mapped[int | None] = mapped_column(ForeignKey("seccion.id"))
    responsable_id: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"))
    origen_hoja: Mapped[str | None] = mapped_column(String(100))
    origen_rango: Mapped[str | None] = mapped_column(String(100))
    origen_valores: Mapped[dict | None] = mapped_column(JSONB)
    origen_hash: Mapped[str | None] = mapped_column(String(64))

    n1: Mapped[ServicioN1] = relationship(lazy="joined")
    clase: Mapped[ClaseServicio | None] = relationship(lazy="joined")
    criticidad: Mapped[Criticidad | None] = relationship(lazy="joined")
    tipo: Mapped[TipoServicio | None] = relationship(lazy="joined")
    seccion: Mapped[Seccion | None] = relationship(lazy="joined")
    responsable: Mapped[Usuario | None] = relationship(lazy="joined")


class Importacion(Base):
    __tablename__ = "importacion"
    id: Mapped[int] = mapped_column(primary_key=True)
    ejecutada_en: Mapped[datetime] = mapped_column(server_default=func.now())
    archivo: Mapped[str] = mapped_column(String(300))
    sha256: Mapped[str] = mapped_column(String(64))
    hoja: Mapped[str] = mapped_column(String(100))
    resumen: Mapped[dict] = mapped_column(JSONB)


class ObservacionImportacion(Base):
    __tablename__ = "observacion_importacion"
    id: Mapped[int] = mapped_column(primary_key=True)
    importacion_id: Mapped[int] = mapped_column(ForeignKey("importacion.id"))
    tipo: Mapped[str] = mapped_column(String(60))
    hoja: Mapped[str] = mapped_column(String(100))
    rango: Mapped[str | None] = mapped_column(String(100))
    codigo: Mapped[str | None] = mapped_column(String(80))
    mensaje: Mapped[str] = mapped_column(Text)
    detalle: Mapped[dict | None] = mapped_column(JSONB)
