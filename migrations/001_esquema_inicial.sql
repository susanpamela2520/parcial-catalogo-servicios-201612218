-- 001: esquema inicial del catálogo de servicios de TI
-- Jerarquía organizacional: empresa -> area -> departamento -> seccion -> puesto -> usuario

CREATE TABLE empresa (
    id          SERIAL PRIMARY KEY,
    codigo      VARCHAR(30)  NOT NULL UNIQUE,
    nombre      VARCHAR(200) NOT NULL,
    activo      BOOLEAN      NOT NULL DEFAULT TRUE,
    creado_en   TIMESTAMPTZ  NOT NULL DEFAULT now(),
    actualizado_en TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE area (
    id          SERIAL PRIMARY KEY,
    empresa_id  INTEGER      NOT NULL REFERENCES empresa(id) ON DELETE RESTRICT,
    codigo      VARCHAR(30)  NOT NULL,
    nombre      VARCHAR(200) NOT NULL,
    activo      BOOLEAN      NOT NULL DEFAULT TRUE,
    creado_en   TIMESTAMPTZ  NOT NULL DEFAULT now(),
    actualizado_en TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_area_codigo UNIQUE (empresa_id, codigo)
);

CREATE TABLE departamento (
    id          SERIAL PRIMARY KEY,
    area_id     INTEGER      NOT NULL REFERENCES area(id) ON DELETE RESTRICT,
    codigo      VARCHAR(30)  NOT NULL,
    nombre      VARCHAR(200) NOT NULL,
    activo      BOOLEAN      NOT NULL DEFAULT TRUE,
    creado_en   TIMESTAMPTZ  NOT NULL DEFAULT now(),
    actualizado_en TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_departamento_codigo UNIQUE (area_id, codigo)
);

CREATE TABLE seccion (
    id              SERIAL PRIMARY KEY,
    departamento_id INTEGER      NOT NULL REFERENCES departamento(id) ON DELETE RESTRICT,
    codigo          VARCHAR(30)  NOT NULL,
    nombre          VARCHAR(200) NOT NULL,
    activo          BOOLEAN      NOT NULL DEFAULT TRUE,
    creado_en       TIMESTAMPTZ  NOT NULL DEFAULT now(),
    actualizado_en  TIMESTAMPTZ  NOT NULL DEFAULT now(),
    CONSTRAINT uq_seccion_codigo UNIQUE (departamento_id, codigo)
);

CREATE TABLE puesto (
    id          SERIAL PRIMARY KEY,
    seccion_id  INTEGER      NOT NULL REFERENCES seccion(id) ON DELETE RESTRICT,
    codigo      VARCHAR(30)  NOT NULL,
    nombre      VARCHAR(200) NOT NULL,
    activo      BOOLEAN      NOT NULL DEFAULT TRUE,
    creado_en   TIMESTAMPTZ  NOT NULL DEFAULT now(),
    actualizado_en TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_puesto_codigo UNIQUE (seccion_id, codigo)
);

CREATE TABLE usuario (
    id              SERIAL PRIMARY KEY,
    puesto_id       INTEGER      NOT NULL REFERENCES puesto(id) ON DELETE RESTRICT,
    nombre          VARCHAR(200) NOT NULL,
    usuario         VARCHAR(80)  NOT NULL,
    correo          VARCHAR(200),
    password_hash   VARCHAR(255) NOT NULL,
    rol             VARCHAR(20)  NOT NULL CHECK (rol IN ('administrador', 'consulta')),
    activo          BOOLEAN      NOT NULL DEFAULT TRUE,
    creado_en       TIMESTAMPTZ  NOT NULL DEFAULT now(),
    actualizado_en  TIMESTAMPTZ  NOT NULL DEFAULT now()
);
-- usuario y correo únicos sin distinguir mayúsculas
CREATE UNIQUE INDEX uq_usuario_usuario ON usuario (lower(usuario));
CREATE UNIQUE INDEX uq_usuario_correo  ON usuario (lower(correo)) WHERE correo IS NOT NULL;

-- Sesiones del lado del servidor: solo se guarda el SHA-256 del token
CREATE TABLE sesion (
    token_hash   CHAR(64)    PRIMARY KEY,
    usuario_id   INTEGER     NOT NULL REFERENCES usuario(id) ON DELETE CASCADE,
    creada_en    TIMESTAMPTZ NOT NULL DEFAULT now(),
    expira_en    TIMESTAMPTZ NOT NULL,
    revocada_en  TIMESTAMPTZ
);
CREATE INDEX ix_sesion_usuario ON sesion (usuario_id);

-- Catálogos controlados
CREATE TABLE clase_servicio (
    id      SERIAL PRIMARY KEY,
    nombre  VARCHAR(80) NOT NULL UNIQUE,
    activo  BOOLEAN     NOT NULL DEFAULT TRUE
);

CREATE TABLE criticidad (
    id      SERIAL PRIMARY KEY,
    nombre  VARCHAR(80) NOT NULL UNIQUE,
    orden   INTEGER     NOT NULL,
    activo  BOOLEAN     NOT NULL DEFAULT TRUE
);

CREATE TABLE tipo_servicio (
    id      SERIAL PRIMARY KEY,
    nombre  VARCHAR(80) NOT NULL UNIQUE,
    activo  BOOLEAN     NOT NULL DEFAULT TRUE
);

-- Mapeo verificable de etiquetas corregidas (valor original -> valor de catálogo)
CREATE TABLE mapeo_etiqueta (
    id              SERIAL PRIMARY KEY,
    campo           VARCHAR(40)  NOT NULL,
    valor_original  VARCHAR(200) NOT NULL,
    valor_canonico  VARCHAR(200) NOT NULL,
    motivo          VARCHAR(300) NOT NULL,
    CONSTRAINT uq_mapeo UNIQUE (campo, valor_original)
);

-- Servicios de nivel 1
CREATE TABLE servicio_n1 (
    id               SERIAL PRIMARY KEY,
    codigo           VARCHAR(40)  NOT NULL UNIQUE,
    codigo_original  VARCHAR(80),
    nombre           VARCHAR(300) NOT NULL,
    nombres_alternativos JSONB    NOT NULL DEFAULT '[]'::jsonb,
    activo           BOOLEAN      NOT NULL DEFAULT TRUE,
    origen_hoja      VARCHAR(100),
    origen_rango     VARCHAR(100),
    origen_hash      CHAR(64),
    creado_en        TIMESTAMPTZ  NOT NULL DEFAULT now(),
    actualizado_en   TIMESTAMPTZ  NOT NULL DEFAULT now()
);

-- Servicios de nivel 2
CREATE TABLE servicio_n2 (
    id                   SERIAL PRIMARY KEY,
    servicio_n1_id       INTEGER      NOT NULL REFERENCES servicio_n1(id) ON DELETE RESTRICT,
    codigo               VARCHAR(40)  NOT NULL UNIQUE,
    codigo_original      VARCHAR(80),
    nombre               VARCHAR(300) NOT NULL,
    -- ACTIVO del Excel: 'S', 'N' o NULL = desconocido (no se inventa)
    activo               CHAR(1)      CHECK (activo IN ('S', 'N')),
    activo_original      VARCHAR(80),
    clase_id             INTEGER      REFERENCES clase_servicio(id),
    clase_original       VARCHAR(200),
    criticidad_id        INTEGER      REFERENCES criticidad(id),
    criticidad_original  VARCHAR(200),
    tipo_id              INTEGER      REFERENCES tipo_servicio(id),
    tipo_original        VARCHAR(200),
    descripcion          TEXT,
    metrica              TEXT,
    minimo               NUMERIC(18, 4),
    minimo_original      VARCHAR(80),
    maximo               NUMERIC(18, 4),
    maximo_original      VARCHAR(80),
    -- Baja lógica desde la aplicación (independiente del ACTIVO del Excel)
    dado_de_baja         BOOLEAN      NOT NULL DEFAULT FALSE,
    estado_revision      VARCHAR(20)  NOT NULL DEFAULT 'OK' CHECK (estado_revision IN ('OK', 'REVISION')),
    seccion_id           INTEGER      REFERENCES seccion(id),
    responsable_id       INTEGER      REFERENCES usuario(id),
    origen_hoja          VARCHAR(100),
    origen_rango         VARCHAR(100),
    origen_valores       JSONB,
    origen_hash          CHAR(64),
    creado_en            TIMESTAMPTZ  NOT NULL DEFAULT now(),
    actualizado_en       TIMESTAMPTZ  NOT NULL DEFAULT now(),
    CONSTRAINT ck_umbral CHECK (minimo IS NULL OR maximo IS NULL OR minimo <= maximo),
    CONSTRAINT ck_responsable_requiere_seccion CHECK (responsable_id IS NULL OR seccion_id IS NOT NULL)
);
CREATE INDEX ix_servicio_n2_n1 ON servicio_n2 (servicio_n1_id);

-- Defensa en profundidad: el responsable debe pertenecer a la sección asignada
CREATE FUNCTION fn_valida_responsable() RETURNS trigger AS $$
BEGIN
    IF NEW.responsable_id IS NOT NULL AND NOT EXISTS (
        SELECT 1 FROM usuario u JOIN puesto p ON p.id = u.puesto_id
        WHERE u.id = NEW.responsable_id AND p.seccion_id = NEW.seccion_id
    ) THEN
        RAISE EXCEPTION 'El responsable no pertenece a la sección asignada'
            USING ERRCODE = 'check_violation';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tg_valida_responsable
    BEFORE INSERT OR UPDATE OF responsable_id, seccion_id ON servicio_n2
    FOR EACH ROW EXECUTE FUNCTION fn_valida_responsable();

-- Bitácora de importaciones
CREATE TABLE importacion (
    id            SERIAL PRIMARY KEY,
    ejecutada_en  TIMESTAMPTZ NOT NULL DEFAULT now(),
    archivo       VARCHAR(300) NOT NULL,
    sha256        CHAR(64)    NOT NULL,
    hoja          VARCHAR(100) NOT NULL,
    resumen       JSONB       NOT NULL
);

CREATE TABLE observacion_importacion (
    id             SERIAL PRIMARY KEY,
    importacion_id INTEGER      NOT NULL REFERENCES importacion(id) ON DELETE CASCADE,
    tipo           VARCHAR(60)  NOT NULL,
    hoja           VARCHAR(100) NOT NULL,
    rango          VARCHAR(100),
    codigo         VARCHAR(80),
    mensaje        TEXT         NOT NULL,
    detalle        JSONB
);
CREATE INDEX ix_obs_importacion ON observacion_importacion (importacion_id);
