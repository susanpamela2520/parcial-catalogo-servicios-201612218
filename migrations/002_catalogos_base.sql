-- 002: valores de los catálogos tal como aparecen en el enunciado y en E112:H122.
-- Se conservan las etiquetas originales (incluida "Demostration").
INSERT INTO clase_servicio (nombre) VALUES ('A DEMANDA'), ('RECURRENTE')
ON CONFLICT (nombre) DO NOTHING;

INSERT INTO criticidad (nombre, orden) VALUES
    ('Very Low', 1), ('Low', 2), ('Normal', 3), ('High', 4), ('Very High', 5)
ON CONFLICT (nombre) DO NOTHING;

INSERT INTO tipo_servicio (nombre) VALUES
    ('Back End'), ('Demostration'), ('End User Service'), ('Front End'),
    ('IT Management'), ('IT Operational'), ('Other'), ('Project'),
    ('Reporting'), ('Training'), ('Underpinning Contract')
ON CONFLICT (nombre) DO NOTHING;
