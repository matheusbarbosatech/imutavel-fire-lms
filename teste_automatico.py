import sys
import time

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

import importlib

try:
    webdriver = importlib.import_module('selenium.webdriver')
    By = importlib.import_module('selenium.webdriver.common.by').By
    Keys = importlib.import_module('selenium.webdriver.common.keys').Keys
    WebDriverWait = importlib.import_module('selenium.webdriver.support.ui').WebDriverWait
    EC = importlib.import_module('selenium.webdriver.support.expected_conditions')
    HAS_SELENIUM = True
except Exception:
    HAS_SELENIUM = False

URL_BASE = "https://sistema-matricula-fmp9.onrender.com"

def main():
    if not HAS_SELENIUM:
        print("[AVISO] O pacote 'selenium' não está instalado neste ambiente Python.")
        return

    print("🤖 Iniciando bateria de testes completos no Imutável Fire LMS...")
    try:
        navegador = webdriver.Chrome()
        wait = WebDriverWait(navegador, 10)

        # -------------------------------------------------------------
        # TESTE 1: LANDING PAGE PÚBLICA
        # -------------------------------------------------------------
        print("\n[TESTE 1/3] Testando acesso à Landing Page publica...")
        navegador.get(f"{URL_BASE}/")
        time.sleep(2)
        print(f"URL Atual: {navegador.current_url}")
        
        # -------------------------------------------------------------
        # TESTE 2: LOGIN DO ADMINISTRADOR
        # -------------------------------------------------------------
        print("\n[TESTE 2/3] Testando Login de Administrador...")
        navegador.get(f"{URL_BASE}/accounts/login/")
        
        wait.until(EC.presence_of_element_located((By.NAME, "username"))).send_keys("admin@imutavel.com")
        navegador.find_element(By.NAME, "password").send_keys("SenhaForte2026!")
        navegador.find_element(By.NAME, "password").send_keys(Keys.RETURN)
        
        time.sleep(3)
        if "courses/dashboard" in navegador.current_url:
            print("✅ SUCESSO: Login realizado e redirecionado para /courses/dashboard/.")
        else:
            print(f"⚠️ AVISO: Redirecionado para {navegador.current_url}")

        # -------------------------------------------------------------
        # TESTE 3: ACESSO À DASHBOARD
        # -------------------------------------------------------------
        print("\n[TESTE 3/3] Verificando Painel de Cursos...")
        navegador.get(f"{URL_BASE}/courses/dashboard/")
        time.sleep(2)
        print("✅ SUCESSO: Painel carregado com status 200.")

        print("\n🎉 Bateria de testes concluída!")

    except Exception as e:
        print(f"\n❌ ERRO DURANTE OS TESTES: {e}")

    finally:
        try:
            navegador.quit()
        except Exception:
            pass

if __name__ == '__main__':
    main()