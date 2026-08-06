import os
os.environ['DEBUG'] = 'False'  # Simula ambiente de produção

import django
from pathlib import Path
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection
try:
    with connection.cursor() as cursor:
        cursor.execute("SELECT version();")
        print("✅ CONEXÃO PRODUÇÃO OK!")
        print(f"Servidor: {cursor.fetchone()[0]}")
except Exception as e:
    print(f"❌ ERRO: {e}")