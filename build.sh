#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input

# 1. Roda a limpeza na marra ANTES de tentar migrar
python fix_render.py

# 2. Faz a migração sem os dados antigos para atrapalhar
python manage.py migrate

# 3. Cadastra os 4 Cursos Oficiais automaticamente
python popular_lms.py