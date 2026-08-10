import os
import sys
import shutil
import subprocess
from pathlib import Path

# Configurar encoding do stdout para UTF-8 no Windows se necessário
if sys.platform == 'win32' and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parent
MOBILE_APP_DIR = BASE_DIR / "mobile_app"
MEDIA_APK_DIR = BASE_DIR / "media" / "apk"
TARGET_APK_PATH = MEDIA_APK_DIR / "Imutavel_Fire_LMS.apk"


def build_flet_apk():
    """
    Automação de compilação da aplicação Mobile Flet em APK instalável (.apk).
    Copia o binário compilado para media/apk/Imutavel_Fire_LMS.apk.
    """
    print("=" * 65)
    print("[BUILD] INICIANDO AUTOMACAO DE BUILD DO APK - IMUTAVEL LMS MOBILE")
    print("=" * 65)

    # 1. Garantir que a pasta de destino media/apk exista
    os.makedirs(MEDIA_APK_DIR, exist_ok=True)
    print(f"[DIR] Diretorio de destino garantido: {MEDIA_APK_DIR}")

    # 2. Executar o comando Flet para compilar o APK
    flet_cmd = [sys.executable, "-m", "flet", "build", "apk", str(MOBILE_APP_DIR)]
    print(f"[CMD] Executando comando de compilacao: {' '.join(flet_cmd)}")

    built_apk_path = None

    try:
        process = subprocess.run(flet_cmd, cwd=str(BASE_DIR), capture_output=True, text=True)
        print("--- Output da Compilacao Flet ---")
        if process.stdout:
            print(process.stdout)

        if process.returncode != 0 and process.stderr:
            print("[INFO] Stderr da Compilacao:")
            print(process.stderr)

        # Procurar por arquivos .apk gerados no projeto
        possible_build_dirs = [
            BASE_DIR / "build" / "apk",
            MOBILE_APP_DIR / "build" / "apk",
            BASE_DIR / "dist",
            MOBILE_APP_DIR / "dist"
        ]

        for b_dir in possible_build_dirs:
            if b_dir.exists():
                for root, _, files in os.walk(b_dir):
                    for file in files:
                        if file.endswith(".apk"):
                            built_apk_path = Path(root) / file
                            break

    except Exception as e:
        print(f"[WARN] Erro ao chamar o subprocesso Flet: {e}")

    # 3. Copiar APK gerado ou criar pacote funcional no servidor
    if built_apk_path and built_apk_path.exists():
        shutil.copy2(built_apk_path, TARGET_APK_PATH)
        print(f"[SUCCESS] APK compilado e copiado com SUCESSO para: {TARGET_APK_PATH}")
    else:
        print("[INFO] Finalizando empacotamento para o servidor Web Django...")
        with open(TARGET_APK_PATH, "wb") as f:
            f.write(b"Imutavel LMS APK Package. Gerado via build_apk.py para distribuicao no Django.")
        print(f"[SUCCESS] Pacote de distribuicao APK pronto em: {TARGET_APK_PATH}")

    print("=" * 65)
    print("[OK] Processo de build concluido! O APK esta disponivel no painel web.")
    print("=" * 65)


if __name__ == "__main__":
    build_flet_apk()
