import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.db import connection

print("🔥 INICIANDO LIMPEZA DE EMERGÊNCIA NO BANCO DE DADOS (RENDER)...")

with connection.cursor() as cursor:
    try:
        # PostgreSQL (Render) - Limpa tudo em cascata para não dar erro de chave estrangeira
        cursor.execute("""
            TRUNCATE courses_enrollment CASCADE;
            TRUNCATE courses_module CASCADE;
            TRUNCATE courses_lesson CASCADE;
            TRUNCATE certificates_certificate CASCADE;
        """)
        print("✅ TABELAS ÓRFÃS DESTRUÍDAS COM SUCESSO (POSTGRESQL)!")
    except Exception as e:
        print(f"⚠️ Erro no truncate (Pode ser SQLite): {e}")

print("🚀 Limpeza concluída, liberando caminho para a migração!")