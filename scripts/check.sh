#!/bin/sh
# Harness de verificación: lo ejecutan el asistente de IA y el catedrático.
#   docker compose exec app sh scripts/check.sh
# Sale con 0 solo si TODOS los controles pasan. Nunca toca la base de evaluación salvo
# para aplicar migraciones (operación no destructiva); las pruebas usan catalogo_test.
set -u
cd "$(dirname "$0")/.."
# Corrección del ciclo 01: fuera del contenedor PYTHONPATH no existe y los módulos no se encontraban
export PYTHONPATH="${PYTHONPATH:-src}"
fallos=0
paso() { printf '\n== %s ==\n' "$1"; }
ok()   { echo "[OK] $1"; }
mal()  { echo "[FALLO] $1"; fallos=$((fallos + 1)); }

paso "1/5 Excel original intacto"
if [ ! -f data/CatalogoServicios.xlsx ]; then
  mal "falta data/CatalogoServicios.xlsx"
elif [ -f data/CatalogoServicios.sha256 ]; then
  (cd data && sha256sum -c CatalogoServicios.sha256 >/dev/null 2>&1) && ok "SHA-256 coincide" || mal "el Excel fue modificado (SHA-256 distinto)"
else
  echo "[AVISO] no existe data/CatalogoServicios.sha256; se omite la comparación"
fi

paso "2/5 Calidad de código (ruff)"
ruff check src tests && ok "sin observaciones" || mal "ruff encontró problemas"

paso "3/5 Migraciones"
python -m scripts.migrate && ok "esquema al día" || mal "migraciones"

paso "4/5 Pruebas automatizadas P01-P11 (base catalogo_test)"
python -m pytest -q && ok "pruebas en verde" || mal "hay pruebas fallidas"

paso "5/5 Variables sensibles fuera del repositorio"
if [ -f .env ]; then mal ".env está dentro de la imagen/repositorio"; else ok ".env no está incluido"; fi

echo
if [ "$fallos" -eq 0 ]; then echo "RESULTADO: TODO EN VERDE"; exit 0; fi
echo "RESULTADO: $fallos control(es) fallido(s)"; exit 1
