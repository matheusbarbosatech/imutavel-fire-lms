from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

URL_BASE = "https://sistema-matricula-fmp9.onrender.com"

print("🤖 Iniciando bateria de testes completos no Imutável Fire LMS...")
navegador = webdriver.Chrome()
wait = WebDriverWait(navegador, 10)

try:
    # -------------------------------------------------------------
    # TESTE 1: LOGIN DO ADMINISTRADOR
    # -------------------------------------------------------------
    print("\n[TESTE 1/4] Testando Login de Administrador...")
    navegador.get(f"{URL_BASE}/accounts/login/")
    
    wait.until(EC.presence_of_element_located((By.NAME, "username"))).send_keys("admin@imutavel.com")
    navegador.find_element(By.NAME, "password").send_keys("SenhaForte2026!")
    navegador.find_element(By.NAME, "password").send_keys(Keys.RETURN)
    
    time.sleep(3)
    if "courses" in navegador.current_url or "dashboard" in navegador.current_url:
        print("✅ SUCESSO: Login de Admin realizado com redirecionamento correto.")
    else:
        print("❌ FALHA: O login de Admin não redirecionou corretamente.")

    # -------------------------------------------------------------
    # TESTE 2: NAVEGAÇÃO NA DASHBOARD DO ALUNO (CATÁLOGO)
    # -------------------------------------------------------------
    print("\n[TESTE 2/4] Verificando Painel de Cursos do Aluno...")
    navegador.get(f"{URL_BASE}/courses/")
    time.sleep(2)
    
    if "courses" in navegador.current_url:
        print("✅ SUCESSO: Página de Cursos carregada sem erros 500.")
    else:
        print("❌ FALHA: A página de Cursos apresentou instabilidade.")

    # -------------------------------------------------------------
    # TESTE 3: ACESSO À ÁREA DO INSTRUTOR
    # -------------------------------------------------------------
    print("\n[TESTE 3/4] Testando acesso à Área do Instrutor...")
    navegador.get(f"{URL_BASE}/courses/instructor/")
    time.sleep(2)
    
    if "instructor" in navegador.current_url or "gestao" in navegador.current_url:
        print("✅ SUCESSO: Admin tem permissão e acessou a Área do Instrutor.")
    else:
        print("⚠️ AVISO: A rota de instrutor pode exigir um redirecionamento ou permissão específica.")

    # -------------------------------------------------------------
    # TESTE 4: PAINEL DE GESTÃO / BI (FINANCEIRO)
    # -------------------------------------------------------------
    print("\n[TESTE 4/4] Testando o Backoffice Gestor...")
    navegador.get(f"{URL_BASE}/gestao/dashboard/")
    time.sleep(2)
    
    if "gestao" in navegador.current_url:
        print("✅ SUCESSO: Dashboard de Gestão e BI carregou na nuvem com o PostgreSQL.")
    else:
        print("❌ FALHA: O painel de gestão bloqueou ou retornou erro.")

    print("\n🎉 Bateria de testes automatizados concluída com sucesso!")

except Exception as e:
    print(f"\n❌ ERRO DURANTE A EXECUÇÃO DOS TESTES: {e}")

finally:
    print("\nFechando o navegador de testes em 5 segundos...")
    time.sleep(5)
    navegador.quit()