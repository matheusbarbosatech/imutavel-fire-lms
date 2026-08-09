import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.db import connection

def force_clean():
    print("🧹 [Render Hack] Iniciando limpeza forçada no banco de dados...")
    with connection.cursor() as cursor:
        try:
            # Tenta limpar caso o banco do Render seja PostgreSQL
            cursor.execute("TRUNCATE courses_enrollment CASCADE;")
            print("✅ Limpeza concluída via PostgreSQL (Cascade).")
        except Exception:
            try:
                # Tenta limpar caso o banco do Render seja SQLite
                cursor.execute("DELETE FROM courses_enrollment;")
                print("✅ Limpeza concluída via SQLite.")
            except Exception as e:
                print(f"⚠️ Aviso ignorado: {e}")

if __name__ == "__main__":
    force_clean()
    print("🚀 Pronto para rodar as migrações em paz!")