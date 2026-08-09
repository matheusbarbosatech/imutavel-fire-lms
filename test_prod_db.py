import os
import sys

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

os.environ['DEBUG'] = 'False'  # Simula ambiente de produção

import django
from pathlib import Path
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection
try:
    with connection.cursor() as cursor:
        vendor = connection.vendor
        if vendor == 'postgresql':
            cursor.execute("SELECT version();")
            ver = cursor.fetchone()[0]
        else:
            cursor.execute("SELECT sqlite_version();")
            ver = f"SQLite {cursor.fetchone()[0]}"
        print("[OK] CONEXAO BANCO DE DADOS ATIVA!")
        print(f"Engine: {vendor} ({ver})")
except Exception as e:
        print(f"[ERRO] Falha na conexao: {e}")