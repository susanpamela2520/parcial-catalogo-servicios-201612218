"""Configuración leída de variables de entorno (ver .env.example)."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://catalogo:catalogo@localhost:5432/catalogo")
EXCEL_PATH = Path(os.getenv("EXCEL_PATH", str(BASE_DIR / "data" / "CatalogoServicios.xlsx")))
EXCEL_HOJA = os.getenv("EXCEL_HOJA", "Servicios Externos")
SESSION_HOURS = int(os.getenv("SESSION_HOURS", "8"))
COOKIE_NAME = "catalogo_sesion"
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() == "true"

# Controles de importación definidos por el enunciado
ESPERADO_N1 = int(os.getenv("ESPERADO_N1", "12"))
ESPERADO_N2 = int(os.getenv("ESPERADO_N2", "46"))
