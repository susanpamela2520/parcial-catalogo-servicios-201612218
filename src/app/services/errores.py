class NegocioError(Exception):
    """Error de validación de negocio con código HTTP y mensaje comprensible."""

    def __init__(self, mensaje: str, status: int = 422, detalle: dict | None = None):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.status = status
        self.detalle = detalle or {}
