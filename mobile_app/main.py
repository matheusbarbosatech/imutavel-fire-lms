import flet as ft
import sqlite3
import httpx
import os
import sys
import json
import asyncio
import re
import html
from pathlib import Path


def html_to_clean_markdown(html_text):
    """Converte conteúdo HTML do Django LMS em Markdown limpo e legível para a interface Flet."""
    if not html_text:
        return ""
    
    text = html.unescape(html_text)
    text = re.sub(r'<h[1-6][^>]*>(.*?)</h[1-6]>', r'\n\n### \1\n', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<(strong|b)[^>]*>(.*?)</\1>', r'**\2**', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<(em|i)[^>]*>(.*?)</\1>', r'*\2*', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<li[^>]*>(.*?)</li>', r'\n- \1', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<tr[^>]*>(.*?)</tr>', r'\n- \1', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<p[^>]*>(.*?)</p>', r'\n\n\1\n', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<br\s*/?>', r'\n', text, flags=re.IGNORECASE)
    
    clean = re.sub(r'<[^>]+>', '', text)
    
    lines = [line.strip() for line in clean.splitlines()]
    result = []
    prev_empty = False
    for line in lines:
        if line:
            result.append(line)
            prev_empty = False
        elif not prev_empty:
            result.append("")
            prev_empty = True
            
    return "\n".join(result).strip()


# Compatibilidade e fallback robusto de cores e ícones para todas as versões do Flet
class ColorPalette:
    def __getattr__(self, name):
        if hasattr(ft, "Colors") and hasattr(ft.Colors, name):
            return getattr(ft.Colors, name)
        if hasattr(ft, "colors") and hasattr(ft.colors, name):
            return getattr(ft.colors, name)
        tailwinds = {
            "SLATE_300": "#cbd5e1",
            "SLATE_400": "#94a3b8",
            "SLATE_500": "#64748b",
            "SLATE_700": "#334155",
            "EMERALD_400": "#34d399",
            "EMERALD_500": "#10b981",
            "EMERALD_600": "#059669",
            "EMERALD_700": "#047857",
        }
        return tailwinds.get(name, "#94a3b8")


class IconPalette:
    def __getattr__(self, name):
        if hasattr(ft, "Icons") and hasattr(ft.Icons, name):
            return getattr(ft.Icons, name)
        if hasattr(ft, "icons") and hasattr(ft.icons, name):
            return getattr(ft.icons, name)
        return name.lower()


colors = ColorPalette()
icons = IconPalette()


class PaddingPalette:
    def symmetric(self, horizontal=0, vertical=0):
        P = getattr(ft, "Padding", getattr(ft, "padding", None))
        if hasattr(P, "symmetric"):
            return P.symmetric(horizontal=horizontal, vertical=vertical)
        return ft.Padding(horizontal, vertical, horizontal, vertical)

    def only(self, left=0, top=0, right=0, bottom=0):
        P = getattr(ft, "Padding", getattr(ft, "padding", None))
        if hasattr(P, "only"):
            return P.only(left=left, top=top, right=right, bottom=bottom)
        return ft.Padding(left, top, right, bottom)

    def all(self, value):
        P = getattr(ft, "Padding", getattr(ft, "padding", None))
        if hasattr(P, "all"):
            return P.all(value)
        return value


class MarginPalette:
    def symmetric(self, horizontal=0, vertical=0):
        M = getattr(ft, "Margin", getattr(ft, "margin", None))
        if hasattr(M, "symmetric"):
            return M.symmetric(horizontal=horizontal, vertical=vertical)
        return ft.Margin(horizontal, vertical, horizontal, vertical)

    def only(self, left=0, top=0, right=0, bottom=0):
        M = getattr(ft, "Margin", getattr(ft, "margin", None))
        if hasattr(M, "only"):
            return M.only(left=left, top=top, right=right, bottom=bottom)
        return ft.Margin(left, top, right, bottom)

    def all(self, value):
        M = getattr(ft, "Margin", getattr(ft, "margin", None))
        if hasattr(M, "all"):
            return M.all(value)
        return value


padding = PaddingPalette()
margin = MarginPalette()
NavigationDestination = getattr(ft, "NavigationBarDestination", getattr(ft, "NavigationDestination", None))
ElevatedButton = getattr(ft, "Button", getattr(ft, "ElevatedButton", None))
Alignment = getattr(ft, "Alignment", getattr(ft, "alignment", None))

# Configurações de diretórios locais e API
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "lms_mobile_offline.db"
STORAGE_DIR = BASE_DIR / "storage" / "lms_media"
DEFAULT_API_URL = os.environ.get("LMS_API_URL", "https://sistema-matricula-fmp9.onrender.com/courses/api")

# Garantir existência do diretório de mídia offline
os.makedirs(STORAGE_DIR, exist_ok=True)


# ==========================================
# GESTÃO DE BANCO DE DADOS LOCAL (SQLITE)
# ==========================================
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_local_db():
    """Inicializa as tabelas no SQLite local do dispositivo."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS active_session (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        user_id INTEGER,
        username TEXT,
        email TEXT,
        full_name TEXT,
        role TEXT
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS courses (
        id INTEGER PRIMARY KEY,
        title TEXT NOT NULL,
        description TEXT,
        created_at TEXT
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS modules (
        id INTEGER PRIMARY KEY,
        course_id INTEGER,
        title TEXT NOT NULL,
        order_num INTEGER DEFAULT 1,
        FOREIGN KEY(course_id) REFERENCES courses(id) ON DELETE CASCADE
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS lessons (
        id INTEGER PRIMARY KEY,
        module_id INTEGER,
        title TEXT NOT NULL,
        content TEXT,
        video_url TEXT,
        embed_video_url TEXT,
        attachment_url TEXT,
        order_num INTEGER DEFAULT 1,
        is_downloaded INTEGER DEFAULT 0,
        local_attachment_path TEXT,
        FOREIGN KEY(module_id) REFERENCES modules(id) ON DELETE CASCADE
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS quizzes (
        id INTEGER PRIMARY KEY,
        lesson_id INTEGER UNIQUE,
        title TEXT NOT NULL,
        min_score INTEGER DEFAULT 70,
        FOREIGN KEY(lesson_id) REFERENCES lessons(id) ON DELETE CASCADE
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS questions (
        id INTEGER PRIMARY KEY,
        quiz_id INTEGER,
        text TEXT NOT NULL,
        FOREIGN KEY(quiz_id) REFERENCES quizzes(id) ON DELETE CASCADE
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS answers (
        id INTEGER PRIMARY KEY,
        question_id INTEGER,
        text TEXT NOT NULL,
        is_correct INTEGER DEFAULT 0,
        FOREIGN KEY(question_id) REFERENCES questions(id) ON DELETE CASCADE
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS lesson_progress (
        lesson_id INTEGER PRIMARY KEY,
        completed INTEGER DEFAULT 0,
        synced INTEGER DEFAULT 0
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS quiz_attempts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        quiz_id INTEGER,
        lesson_id INTEGER,
        score REAL,
        passed INTEGER,
        synced INTEGER DEFAULT 0
    );
    """)

    conn.commit()
    conn.close()


def save_courses_to_sqlite(courses_data):
    """Salva/atualiza os dados dos cursos vindos da API no SQLite local."""
    conn = get_db_connection()
    cursor = conn.cursor()

    for course in courses_data:
        cursor.execute(
            "INSERT OR REPLACE INTO courses (id, title, description, created_at) VALUES (?, ?, ?, ?)",
            (course['id'], course['title'], course.get('description', ''), course.get('created_at'))
        )
        for module in course.get('modules', []):
            cursor.execute(
                "INSERT OR REPLACE INTO modules (id, course_id, title, order_num) VALUES (?, ?, ?, ?)",
                (module['id'], course['id'], module['title'], module.get('order', 1))
            )
            for lesson in module.get('lessons', []):
                cursor.execute("SELECT is_downloaded, local_attachment_path FROM lessons WHERE id = ?", (lesson['id'],))
                existing = cursor.fetchone()
                is_dl = existing['is_downloaded'] if existing else 0
                local_path = existing['local_attachment_path'] if existing else ""

                cursor.execute(
                    """INSERT OR REPLACE INTO lessons 
                       (id, module_id, title, content, video_url, embed_video_url, attachment_url, order_num, is_downloaded, local_attachment_path) 
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        lesson['id'], module['id'], lesson['title'], lesson.get('content', ''),
                        lesson.get('video_url', ''), lesson.get('embed_video_url', ''),
                        lesson.get('attachment_url', ''), lesson.get('order', 1),
                        is_dl, local_path
                    )
                )

                quiz = lesson.get('quiz')
                if quiz:
                    cursor.execute(
                        "INSERT OR REPLACE INTO quizzes (id, lesson_id, title, min_score) VALUES (?, ?, ?, ?)",
                        (quiz['id'], lesson['id'], quiz['title'], quiz.get('min_score', 70))
                    )
                    for q in quiz.get('questions', []):
                        cursor.execute(
                            "INSERT OR REPLACE INTO questions (id, quiz_id, text) VALUES (?, ?, ?)",
                            (q['id'], quiz['id'], q['text'])
                        )
                        for a in q.get('answers', []):
                            cursor.execute(
                                "INSERT OR REPLACE INTO answers (id, question_id, text, is_correct) VALUES (?, ?, ?, ?)",
                                (a['id'], q['id'], a['text'], 1 if a.get('is_correct') else 0)
                            )

    conn.commit()
    conn.close()


# ==========================================
# LÓGICA DE SINCRONIZAÇÃO COM O DJANGO
# ==========================================
async def fetch_and_sync_online(api_base_url):
    """Sincroniza os cursos com a API Django e envia o progresso offline pendente."""
    urls_to_try = [
        api_base_url,
        "https://sistema-matricula-fmp9.onrender.com/courses/api",
        "http://192.168.1.3:8000/courses/api",
        "http://127.0.0.1:8000/courses/api"
    ]
    
    for current_url in urls_to_try:
        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                conn = get_db_connection()
                cursor = conn.cursor()

                cursor.execute("SELECT lesson_id, completed FROM lesson_progress WHERE synced = 0")
                pending_progress = [dict(row) for row in cursor.fetchall()]

                cursor.execute("SELECT quiz_id, lesson_id, score, passed FROM quiz_attempts WHERE synced = 0")
                pending_quizzes = [dict(row) for row in cursor.fetchall()]

                if pending_progress or pending_quizzes:
                    payload = {
                        "progress": pending_progress,
                        "quiz_attempts": pending_quizzes
                    }
                    sync_resp = await client.post(f"{current_url}/sync-progress/", json=payload)
                    if sync_resp.status_code == 200:
                        cursor.execute("UPDATE lesson_progress SET synced = 1 WHERE synced = 0")
                        cursor.execute("UPDATE quiz_attempts SET synced = 1 WHERE synced = 0")
                        conn.commit()

                resp = await client.get(f"{current_url}/courses/")
                if resp.status_code == 200:
                    courses_data = resp.json()
                    save_courses_to_sqlite(courses_data)
                    conn.close()
                    return True, "Sincronização realizada com sucesso!"
                conn.close()
        except Exception:
            continue

    return False, "Modo Offline: Funcionando com dados locais salvos."


async def download_lesson_media(attachment_url, lesson_id):
    """Baixa um anexo (PDF, áudio, etc.) para o armazenamento local do aplicativo."""
    if not attachment_url:
        return False, "Nenhum arquivo anexado nesta aula."

    try:
        filename = attachment_url.split('/')[-1] or f"material_aula_{lesson_id}.pdf"
        dest_path = STORAGE_DIR / f"{lesson_id}_{filename}"

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(attachment_url)
            if resp.status_code == 200:
                with open(dest_path, "wb") as f:
                    f.write(resp.content)

                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE lessons SET is_downloaded = 1, local_attachment_path = ? WHERE id = ?",
                    (str(dest_path), lesson_id)
                )
                conn.commit()
                conn.close()
                return True, str(dest_path)
            return False, f"Erro {resp.status_code} ao baixar arquivo."
    except Exception as e:
        return False, f"Erro ao realizar download: {str(e)}"


# =========================================================================
# INTERFACE GRÁFICA MULTI-PORTAL FLET (ALUNO, INSTRUTOR, ADMINISTRADOR)
# =========================================================================
def main(page: ft.Page):
    page.title = "Imutável LMS - Multi-Portal Mobile"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#0f172a"
    page.padding = 0
    page.window_width = 390
    page.window_height = 844

    init_local_db()
    api_url_setting = DEFAULT_API_URL
    current_portal = [0]  # 0: Aluno, 1: Instrutor, 2: Administrador
    current_speed = ["1.0x (Normal)"]
    user_session = [None]  # Guardará dados do usuário logado

    status_banner = ft.Text("Verificando conexão...", size=12, color=colors.SLATE_400)
    current_view_container = ft.Column(expand=True, scroll=ft.ScrollMode.AUTO)

    def show_snack(message: str, color=colors.EMERALD_500):
        snack = ft.SnackBar(
            content=ft.Text(message, color=colors.WHITE, weight=ft.FontWeight.BOLD),
            bgcolor=color,
            duration=3000
        )
        page.overlay.append(snack)
        snack.open = True
        page.update()

    def check_user_session():
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM active_session WHERE id = 1")
        row = cursor.fetchone()
        conn.close()
        if row:
            user_session[0] = dict(row)
        return user_session[0]

    check_user_session()

    def build_app_bar(title="Imutável LMS", can_go_back=False):
        leading_action = None
        if can_go_back:
            leading_action = ft.IconButton(
                icon=icons.ARROW_BACK,
                icon_color=colors.WHITE,
                on_click=lambda _: render_current_portal()
            )
        else:
            leading_action = ft.Icon(icons.LOCAL_FIRE_DEPARTMENT, color=colors.RED_500, size=28)

        actions = [
            ft.IconButton(
                icon=icons.SYNC,
                tooltip="Sincronizar Dados",
                icon_color=colors.CYAN_400,
                on_click=lambda _: trigger_manual_sync()
            )
        ]

        if user_session[0]:
            actions.append(
                ft.IconButton(
                    icon=icons.LOGOUT,
                    tooltip="Sair da Conta",
                    icon_color=colors.RED_400,
                    on_click=lambda _: logout_user()
                )
            )

        return ft.AppBar(
            leading=leading_action,
            title=ft.Text(title, size=18, weight=ft.FontWeight.BOLD, color=colors.WHITE),
            bgcolor="#1e293b",
            actions=actions
        )

    def logout_user():
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM active_session")
        conn.commit()
        conn.close()
        user_session[0] = None
        show_snack("Você saiu da conta.", colors.AMBER_600)
        render_login_view()

    # ---------------------------------------------------------------------
    # 🔑 TELAS DE AUTENTICAÇÃO (LOGIN, REGISTRO, ESQUECI A SENHA)
    # ---------------------------------------------------------------------
    def render_login_view():
        page.appbar = build_app_bar("Acesso ao Sistema", can_go_back=False)
        page.navigation_bar = None
        current_view_container.controls.clear()

        email_field = ft.TextField(label="E-mail, Usuário ou CPF", border_color=colors.SLATE_500, color=colors.WHITE)
        password_field = ft.TextField(label="Senha", password=True, can_reveal_password=True, border_color=colors.SLATE_500, color=colors.WHITE)

        def do_login(e):
            u = email_field.value.strip()
            p = password_field.value.strip()
            if not u or not p:
                show_snack("Informe seu e-mail e senha!", colors.RED_500)
                return

            async def send_login():
                try:
                    async with httpx.AsyncClient(timeout=6.0) as client:
                        resp = await client.post(f"{api_url_setting}/auth/login/", json={"username": u, "password": p})
                        if resp.status_code == 200:
                            res_data = resp.json()
                            user_data = res_data.get('user', {})
                            conn = get_db_connection()
                            cursor = conn.cursor()
                            cursor.execute("INSERT OR REPLACE INTO active_session (id, user_id, username, email, full_name, role) VALUES (1, ?, ?, ?, ?, ?)",
                                           (user_data.get('id'), user_data.get('username'), user_data.get('email'), user_data.get('full_name'), user_data.get('role', 'STUDENT')))
                            conn.commit()
                            conn.close()
                            user_session[0] = user_data
                            show_snack(f"Bem-vindo(a), {user_data.get('full_name')}!", colors.EMERALD_500)
                            setup_main_navigation()
                            render_current_portal()
                        else:
                            show_snack("E-mail ou senha incorretos.", colors.RED_500)
                except Exception as ex:
                    show_snack(f"Erro ao conectar com servidor: {str(ex)}", colors.AMBER_600)

            asyncio.create_task(send_login())

        login_card = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(icons.LOCAL_FIRE_DEPARTMENT, color=colors.RED_500, size=36),
                    ft.Text("IMUTÁVEL LMS", size=22, weight=ft.FontWeight.BOLD, color=colors.WHITE)
                ], alignment=ft.MainAxisAlignment.CENTER),
                ft.Text("Portal do Aluno, Instrutor & Administração", size=12, color=colors.SLATE_300, text_align=ft.TextAlign.CENTER),
                ft.Container(height=10),
                email_field,
                password_field,
                ElevatedButton(
                    content=ft.Row([
                        ft.Icon(icons.LOGIN, color=colors.WHITE),
                        ft.Text("Entrar na Plataforma", color=colors.WHITE, weight=ft.FontWeight.BOLD)
                    ], alignment=ft.MainAxisAlignment.CENTER),
                    style=ft.ButtonStyle(bgcolor=colors.RED_600, shape=ft.RoundedRectangleBorder(radius=10)),
                    on_click=do_login
                ),
                ElevatedButton(
                    content=ft.Row([
                        ft.Icon(icons.ADMIN_PANEL_SETTINGS, color=colors.WHITE),
                        ft.Text("Entrar como Superuser (admin / admin)", color=colors.WHITE, weight=ft.FontWeight.BOLD)
                    ], alignment=ft.MainAxisAlignment.CENTER),
                    style=ft.ButtonStyle(bgcolor=colors.AMBER_600, shape=ft.RoundedRectangleBorder(radius=10)),
                    on_click=lambda _: (setattr(email_field, 'value', 'admin'), setattr(password_field, 'value', 'admin'), page.update(), do_login(None))
                ),
                ft.Row([
                    ft.TextButton(
                        content=ft.Text("Nova Matrícula (Criar Conta)", color=colors.CYAN_400, weight=ft.FontWeight.BOLD),
                        on_click=lambda _: render_register_view()
                    ),
                    ft.TextButton(
                        content=ft.Text("Esqueci a Senha", color=colors.SLATE_400),
                        on_click=lambda _: render_forgot_password_view()
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            ], spacing=10),
            bgcolor="#1e293b",
            padding=20,
            border_radius=16,
            margin=margin.symmetric(horizontal=16, vertical=20)
        )

        current_view_container.controls = [login_card]
        page.update()

    def render_register_view():
        page.appbar = build_app_bar("Nova Matrícula / Cadastro", can_go_back=True)
        current_view_container.controls.clear()

        name_field = ft.TextField(label="Nome Completo", border_color=colors.SLATE_500, color=colors.WHITE)
        email_field = ft.TextField(label="E-mail Principal", border_color=colors.SLATE_500, color=colors.WHITE)
        cpf_field = ft.TextField(label="CPF", border_color=colors.SLATE_500, color=colors.WHITE)
        password_field = ft.TextField(label="Senha de Acesso", password=True, can_reveal_password=True, border_color=colors.SLATE_500, color=colors.WHITE)

        def do_register(e):
            n = name_field.value.strip()
            em = email_field.value.strip()
            c = cpf_field.value.strip()
            p = password_field.value.strip()

            if not n or not em or not p:
                show_snack("Preencha Nome, E-mail e Senha!", colors.RED_500)
                return

            async def send_register():
                try:
                    async with httpx.AsyncClient(timeout=6.0) as client:
                        resp = await client.post(f"{api_url_setting}/auth/register/", json={"name": n, "email": em, "cpf": c, "password": p})
                        if resp.status_code == 200:
                            show_snack("Cadastro realizado com sucesso! Faça login.", colors.EMERALD_500)
                            render_login_view()
                        else:
                            err = resp.json().get('error', 'Falha no cadastro.')
                            show_snack(err, colors.RED_500)
                except Exception as ex:
                    show_snack(f"Erro no cadastro: {str(ex)}", colors.AMBER_600)

            asyncio.create_task(send_register())

        reg_card = ft.Container(
            content=ft.Column([
                ft.Text("Formulário de Nova Matrícula", size=18, weight=ft.FontWeight.BOLD, color=colors.WHITE),
                ft.Text("Crie seu acesso para iniciar os cursos operacionais imediatamente.", size=12, color=colors.SLATE_300),
                name_field,
                email_field,
                cpf_field,
                password_field,
                ElevatedButton(
                    content=ft.Row([
                        ft.Icon(icons.CHECK_CIRCLE, color=colors.WHITE),
                        ft.Text("Concluir Cadastro & Matrícula", color=colors.WHITE, weight=ft.FontWeight.BOLD)
                    ], alignment=ft.MainAxisAlignment.CENTER),
                    style=ft.ButtonStyle(bgcolor=colors.EMERALD_600, shape=ft.RoundedRectangleBorder(radius=10)),
                    on_click=do_register
                )
            ], spacing=10),
            bgcolor="#1e293b",
            padding=20,
            border_radius=16,
            margin=margin.symmetric(horizontal=16, vertical=16)
        )

        current_view_container.controls = [reg_card]
        page.update()

    def render_forgot_password_view():
        page.appbar = build_app_bar("Recuperar Senha", can_go_back=True)
        current_view_container.controls.clear()

        email_field = ft.TextField(label="Informe seu E-mail Cadastrado", border_color=colors.SLATE_500, color=colors.WHITE)

        def do_forgot(e):
            em = email_field.value.strip()
            if not em:
                show_snack("Informe seu e-mail!", colors.RED_500)
                return

            async def send_forgot():
                try:
                    async with httpx.AsyncClient(timeout=6.0) as client:
                        resp = await client.post(f"{api_url_setting}/auth/forgot-password/", json={"email": em})
                        if resp.status_code == 200:
                            show_snack("Instruções enviadas para seu e-mail!", colors.EMERALD_500)
                            render_login_view()
                        else:
                            show_snack("E-mail não localizado no sistema.", colors.RED_500)
                except Exception as ex:
                    show_snack(f"Erro: {str(ex)}", colors.AMBER_600)

            asyncio.create_task(send_forgot())

        forgot_card = ft.Container(
            content=ft.Column([
                ft.Text("Redefinição de Senha", size=18, weight=ft.FontWeight.BOLD, color=colors.WHITE),
                ft.Text("Enviaremos um link e código de recuperação para seu e-mail.", size=12, color=colors.SLATE_300),
                email_field,
                ElevatedButton(
                    content=ft.Row([
                        ft.Icon(icons.EMAIL, color=colors.WHITE),
                        ft.Text("Enviar Instruções", color=colors.WHITE, weight=ft.FontWeight.BOLD)
                    ], alignment=ft.MainAxisAlignment.CENTER),
                    style=ft.ButtonStyle(bgcolor=colors.CYAN_600, shape=ft.RoundedRectangleBorder(radius=10)),
                    on_click=do_forgot
                )
            ], spacing=10),
            bgcolor="#1e293b",
            padding=20,
            border_radius=16,
            margin=margin.symmetric(horizontal=16, vertical=20)
        )

        current_view_container.controls = [forgot_card]
        page.update()

    def setup_main_navigation():
        def on_nav_change(e):
            current_portal[0] = e.control.selected_index
            render_current_portal()

        nav_bar = ft.NavigationBar(
            selected_index=current_portal[0],
            bgcolor="#1e293b",
            indicator_color=colors.RED_600,
            destinations=[
                NavigationDestination(icon=icons.SCHOOL, label="Aluno"),
                NavigationDestination(icon=icons.SUPERVISED_USER_CIRCLE, label="Instrutor"),
                NavigationDestination(icon=icons.ADMIN_PANEL_SETTINGS, label="Admin / Gestão")
            ],
            on_change=on_nav_change
        )
        page.navigation_bar = nav_bar

    def render_current_portal():
        if not user_session[0]:
            render_login_view()
            return

        setup_main_navigation()

        if current_portal[0] == 0:
            render_student_portal()
        elif current_portal[0] == 1:
            render_instructor_portal()
        else:
            render_admin_portal()

    # ---------------------------------------------------------------------
    # 🎓 1. PORTAL DO ALUNO (Salas Offline, Cursos, Secretaria Virtual & Documentos)
    # ---------------------------------------------------------------------
    def render_student_portal():
        page.appbar = build_app_bar("🎓 Portal do Aluno", can_go_back=False)
        current_view_container.controls.clear()

        # Abas internas: Cursos vs Secretaria Virtual
        student_sub_tab = [0]  # 0: Cursos, 1: Secretaria Virtual & Documentação

        header_sub_menu = ft.Container(
            content=ft.Row([
                ElevatedButton(
                    content=ft.Text("Meus Cursos Offline", color=colors.WHITE, weight=ft.FontWeight.BOLD),
                    style=ft.ButtonStyle(bgcolor=colors.RED_600 if student_sub_tab[0] == 0 else colors.SLATE_700, shape=ft.RoundedRectangleBorder(radius=8)),
                    on_click=lambda _: switch_student_subtab(0)
                ),
                ElevatedButton(
                    content=ft.Text("Secretaria & Documentos", color=colors.WHITE, weight=ft.FontWeight.BOLD),
                    style=ft.ButtonStyle(bgcolor=colors.RED_600 if student_sub_tab[0] == 1 else colors.SLATE_700, shape=ft.RoundedRectangleBorder(radius=8)),
                    on_click=lambda _: switch_student_subtab(1)
                )
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
            padding=padding.symmetric(horizontal=16, vertical=8)
        )

        def switch_student_subtab(idx):
            student_sub_tab[0] = idx
            if idx == 0:
                render_student_courses_tab()
            else:
                render_student_secretary_tab()

        def render_student_courses_tab():
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM courses ORDER BY id DESC")
            courses = cursor.fetchall()
            conn.close()

            cards = [
                header_sub_menu,
                ft.Container(
                    content=ft.Row([
                        ft.Icon(icons.OFFLINE_BOLT, color=colors.EMERALD_400, size=24),
                        ft.Column([
                            ft.Text("Modo Offline & Sala de Aula", weight=ft.FontWeight.BOLD, color=colors.WHITE, size=14),
                            ft.Text("Assista a vídeo aulas, ouça podcasts e faça quizzes sem internet.", size=11, color=colors.SLATE_300)
                        ], spacing=2, expand=True)
                    ]),
                    padding=14,
                    bgcolor="#064e3b",
                    border_radius=14,
                    margin=margin.only(left=16, right=16, top=4, bottom=8)
                )
            ]

            if not courses:
                cards.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Icon(icons.CLOUD_DOWNLOAD_OUTLINED, size=50, color=colors.SLATE_500),
                            ft.Text("Nenhum curso sincronizado ainda.", color=colors.SLATE_300, weight=ft.FontWeight.BOLD),
                            ft.Text("Clique no botão de sincronização no topo para baixar os dados.", size=12, color=colors.SLATE_400, text_align=ft.TextAlign.CENTER)
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
                        padding=30,
                        alignment=Alignment(0, 0)
                    )
                )
            else:
                for course in courses:
                    c_id = course['id']
                    cards.append(
                        ft.Container(
                            content=ft.Column([
                                ft.Row([
                                    ft.Container(
                                        content=ft.Text("CURSO", size=9, weight=ft.FontWeight.BOLD, color=colors.RED_400),
                                        bgcolor="#450a0a",
                                        padding=padding.symmetric(horizontal=8, vertical=4),
                                        border_radius=8
                                    ),
                                    ft.Icon(icons.CHEVRON_RIGHT, color=colors.SLATE_400)
                                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                                ft.Text(course['title'], size=17, weight=ft.FontWeight.BOLD, color=colors.WHITE),
                                ft.Text(course['description'] or "Sem descrição", size=12, color=colors.SLATE_300, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
                                ElevatedButton(
                                    content=ft.Row([
                                        ft.Text("Acessar Módulos & Aulas", weight=ft.FontWeight.BOLD, color=colors.WHITE),
                                        ft.Icon(icons.PLAY_ARROW_ROUNDED, size=16, color=colors.WHITE)
                                    ], alignment=ft.MainAxisAlignment.CENTER),
                                    style=ft.ButtonStyle(bgcolor=colors.RED_600, shape=ft.RoundedRectangleBorder(radius=10)),
                                    on_click=lambda _, course_id=c_id: render_course_detail_view(course_id)
                                )
                            ], spacing=10),
                            bgcolor="#1e293b",
                            padding=16,
                            border_radius=16,
                            margin=margin.symmetric(horizontal=16, vertical=6)
                        )
                    )

            current_view_container.controls = cards
            page.update()

        def render_student_secretary_tab():
            sec_cards = [
                header_sub_menu,
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(icons.FOLDER_SHARED, color=colors.CYAN_400, size=24),
                            ft.Text("Secretaria Virtual & Envio de Documentos", weight=ft.FontWeight.BOLD, size=16, color=colors.WHITE)
                        ]),
                        ft.Text("Envie seus documentos para emissão de Certificados e Carteirinha.", size=12, color=colors.SLATE_300)
                    ], spacing=6),
                    bgcolor="#1e293b",
                    padding=16,
                    border_radius=16,
                    margin=margin.symmetric(horizontal=16, vertical=4)
                ),
                ft.Container(
                    content=ft.Column([
                        ft.Text("Homologação de Documentos Pessoais", weight=ft.FontWeight.BOLD, color=colors.WHITE, size=14),
                        ft.Row([
                            ft.Icon(icons.CHECK_CIRCLE, color=colors.EMERALD_400, size=18),
                            ft.Text("RG / CPF (Documento de Identidade) - APROVADO", color=colors.SLATE_300, size=12)
                        ]),
                        ft.Row([
                            ft.Icon(icons.HOURGLASS_EMPTY, color=colors.AMBER_400, size=18),
                            ft.Text("Comprovante de Residência - PENDENTE", color=colors.SLATE_300, size=12)
                        ]),
                        ft.Row([
                            ft.Icon(icons.CHECK_CIRCLE, color=colors.EMERALD_400, size=18),
                            ft.Text("Foto 3x4 para Carteirinha - APROVADO", color=colors.SLATE_300, size=12)
                        ]),
                        ElevatedButton(
                            content=ft.Row([
                                ft.Icon(icons.UPLOAD_FILE, color=colors.WHITE),
                                ft.Text("Enviar Novo Documento", color=colors.WHITE, weight=ft.FontWeight.BOLD)
                            ], alignment=ft.MainAxisAlignment.CENTER),
                            style=ft.ButtonStyle(bgcolor=colors.CYAN_600, shape=ft.RoundedRectangleBorder(radius=10)),
                            on_click=lambda _: show_snack("Selecione o arquivo de documento no celular.", colors.CYAN_500)
                        )
                    ], spacing=10),
                    bgcolor="#1e293b",
                    padding=16,
                    border_radius=16,
                    margin=margin.symmetric(horizontal=16, vertical=6)
                ),
                ft.Container(
                    content=ft.Column([
                        ft.Text("Solicitação de Declarações & Atestados", weight=ft.FontWeight.BOLD, color=colors.WHITE, size=14),
                        ft.Text("Emita documentos oficiais do seu curso com assinatura digital.", size=12, color=colors.SLATE_300),
                        ElevatedButton(
                            content=ft.Row([
                                ft.Icon(icons.DESCRIPTION, color=colors.WHITE),
                                ft.Text("Solicitar Declaração de Matrícula", color=colors.WHITE, weight=ft.FontWeight.BOLD)
                            ], alignment=ft.MainAxisAlignment.CENTER),
                            style=ft.ButtonStyle(bgcolor=colors.BLUE_600, shape=ft.RoundedRectangleBorder(radius=10)),
                            on_click=lambda _: show_snack("Declaração gerada e enviada para o seu e-mail!", colors.EMERALD_500)
                        ),
                        ElevatedButton(
                            content=ft.Row([
                                ft.Icon(icons.ARTICLE, color=colors.WHITE),
                                ft.Text("Solicitar Histórico Escolar Parcial", color=colors.WHITE, weight=ft.FontWeight.BOLD)
                            ], alignment=ft.MainAxisAlignment.CENTER),
                            style=ft.ButtonStyle(bgcolor=colors.SLATE_700, shape=ft.RoundedRectangleBorder(radius=10)),
                            on_click=lambda _: show_snack("Histórico em processamento pela Secretaria.", colors.CYAN_500)
                        )
                    ], spacing=10),
                    bgcolor="#1e293b",
                    padding=16,
                    border_radius=16,
                    margin=margin.symmetric(horizontal=16, vertical=6)
                )
            ]
            current_view_container.controls = sec_cards
            page.update()

        render_student_courses_tab()

    def render_course_detail_view(course_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM courses WHERE id = ?", (course_id,))
        course = cursor.fetchone()

        if not course:
            render_student_portal()
            return

        page.appbar = build_app_bar(course['title'], can_go_back=True)
        current_view_container.controls.clear()

        cursor.execute("SELECT * FROM modules WHERE course_id = ? ORDER BY order_num ASC", (course_id,))
        modules = cursor.fetchall()

        items = [
            ft.Container(
                content=ft.Column([
                    ft.Text(course['title'], size=20, weight=ft.FontWeight.BOLD, color=colors.WHITE),
                    ft.Text(course['description'] or "", size=13, color=colors.SLATE_300)
                ], spacing=6),
                padding=16,
                bgcolor="#111827",
                margin=margin.only(bottom=10)
            )
        ]

        for module in modules:
            m_id = module['id']
            cursor.execute("SELECT * FROM lessons WHERE module_id = ? ORDER BY order_num ASC", (m_id,))
            lessons = cursor.fetchall()

            lesson_controls = []
            for lesson in lessons:
                l_id = lesson['id']
                is_dl = bool(lesson['is_downloaded'])
                cursor.execute("SELECT completed FROM lesson_progress WHERE lesson_id = ?", (l_id,))
                p_row = cursor.fetchone()
                is_completed = bool(p_row['completed']) if p_row else False

                lesson_controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(
                                icons.CHECK_CIRCLE if is_completed else icons.RADIO_BUTTON_UNCHECKED,
                                color=colors.EMERALD_400 if is_completed else colors.SLATE_500,
                                size=20
                            ),
                            ft.Column([
                                ft.Text(lesson['title'], weight=ft.FontWeight.BOLD, color=colors.WHITE, size=14),
                                ft.Row([
                                    ft.Text("Disponível Offline" if is_dl else "Conteúdo Texto/Vídeo", size=11, color=colors.SLATE_400),
                                    ft.Icon(icons.DOWNLOAD_DONE, size=12, color=colors.EMERALD_400) if is_dl else ft.Container()
                                ])
                            ], spacing=2, expand=True),
                            ft.IconButton(
                                icon=icons.ARROW_FORWARD_IOS,
                                icon_size=14,
                                icon_color=colors.SLATE_400,
                                on_click=lambda _, lesson_id=l_id: render_lesson_view(lesson_id)
                            )
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        padding=12,
                        bgcolor="#0f172a",
                        border_radius=10,
                        margin=margin.only(bottom=6)
                    )
                )

            items.append(
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(icons.BOOK_OUTLINED, color=colors.RED_400, size=18),
                            ft.Text(module['title'], size=15, weight=ft.FontWeight.BOLD, color=colors.WHITE)
                        ], spacing=8),
                        ft.Column(controls=lesson_controls, spacing=4)
                    ], spacing=10),
                    bgcolor="#1e293b",
                    padding=14,
                    border_radius=14,
                    margin=margin.symmetric(horizontal=16, vertical=6)
                )
            )

        conn.close()
        current_view_container.controls = items
        page.update()

    def render_lesson_view(lesson_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM lessons WHERE id = ?", (lesson_id,))
        lesson = cursor.fetchone()

        if not lesson:
            render_student_portal()
            return

        cursor.execute("SELECT completed FROM lesson_progress WHERE lesson_id = ?", (lesson_id,))
        p_row = cursor.fetchone()
        is_completed = bool(p_row['completed']) if p_row else False

        cursor.execute("SELECT * FROM quizzes WHERE lesson_id = ?", (lesson_id,))
        quiz = cursor.fetchone()

        page.appbar = build_app_bar(lesson['title'], can_go_back=True)
        current_view_container.controls.clear()

        is_dl = bool(lesson['is_downloaded'])
        local_path = lesson['local_attachment_path'] or ""
        attachment_url = lesson['attachment_url'] or ""

        # ---------------------------------------------------------
        # 1. SEÇÃO: REPRODUTOR DE VÍDEO INCORPORADO COM ACELERAÇÃO
        # ---------------------------------------------------------
        video_section = ft.Container()
        video_url = lesson['video_url'] or lesson['embed_video_url'] or ""

        if video_url:
            def open_video_url(e):
                show_snack("Iniciando Transmissão da Vídeo Aula...", colors.CYAN_600)
                try:
                    if hasattr(ft, "UrlLauncher") and hasattr(ft.UrlLauncher, "launch_url"):
                        ft.UrlLauncher.launch_url(video_url)
                    elif hasattr(page, "launch_url"):
                        res = page.launch_url(video_url)
                        if asyncio.iscoroutine(res):
                            asyncio.create_task(res)
                except Exception:
                    pass

            video_section = ft.Container(
                content=ft.Column([
                    ft.Container(
                        content=ft.Row([
                            ft.Row([
                                ft.Icon(icons.TV, color=colors.RED_500, size=18),
                                ft.Text("REPRODUTOR DE VÍDEO DA AULA", size=11, weight=ft.FontWeight.BOLD, color=colors.WHITE)
                            ], spacing=6),
                            ft.Container(
                                content=ft.Text("HD / AO VIVO", size=9, weight=ft.FontWeight.BOLD, color=colors.EMERALD_400),
                                bgcolor="#064e3b",
                                padding=padding.symmetric(horizontal=8, vertical=3),
                                border_radius=6
                            )
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        bgcolor="#0f172a",
                        padding=padding.symmetric(horizontal=14, vertical=10),
                        border_radius=margin.only(top=14, left=14, right=14)
                    ),
                    ft.Container(
                        content=ft.Column([
                            ft.IconButton(
                                icon=icons.PLAY_CIRCLE_FILL,
                                icon_color=colors.RED_500,
                                icon_size=68,
                                tooltip="Clique para iniciar o vídeo na tela",
                                on_click=open_video_url
                            ),
                            ft.Text(lesson['title'], weight=ft.FontWeight.BOLD, color=colors.WHITE, size=15, text_align=ft.TextAlign.CENTER),
                            ft.Text("Toque no player acima para iniciar a transmissão imediatamente", size=11, color=colors.SLATE_400, text_align=ft.TextAlign.CENTER),
                            ElevatedButton(
                                content=ft.Row([
                                    ft.Icon(icons.PLAY_ARROW, color=colors.WHITE),
                                    ft.Text("Reproduzir no Player da Plataforma", color=colors.WHITE, weight=ft.FontWeight.BOLD)
                                ], alignment=ft.MainAxisAlignment.CENTER),
                                style=ft.ButtonStyle(bgcolor=colors.RED_600, shape=ft.RoundedRectangleBorder(radius=10)),
                                on_click=open_video_url
                            )
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8),
                        bgcolor="#000000",
                        padding=20,
                        alignment=Alignment(0, 0),
                        border_radius=12
                    )
                ]),
                bgcolor="#1e293b",
                padding=10,
                border_radius=16,
                margin=margin.symmetric(horizontal=16, vertical=8)
            )

        # ---------------------------------------------------------
        # 2. SEÇÃO DESTACADA: DOWNLOAD DA AULA E MATERIAL ANEXO
        # ---------------------------------------------------------
        media_section = ft.Container()
        if attachment_url or True:  # Garante destaque do card de download
            is_audio = any(attachment_url.lower().endswith(ext) for ext in ['.mp3', '.wav', '.m4a', '.aac', '.ogg']) if attachment_url else False
            section_title = "Áudio Aula & Podcast Operacional" if is_audio else "Material da Aula (PDF / Anexo)"
            icon_header = icons.HEADSET if is_audio else icons.DOWNLOAD_FOR_OFFLINE
            header_color = colors.CYAN_400 if is_audio else colors.EMERALD_400

            if is_dl and os.path.exists(local_path):
                media_action_button = ElevatedButton(
                    content=ft.Row([
                        ft.Icon(icons.PLAY_ARROW if is_audio else icons.FOLDER_OPEN, color=colors.WHITE),
                        ft.Text("Ouvir Áudio Salvo (Offline)" if is_audio else "Abrir Material Salvo (PDF)", color=colors.WHITE, weight=ft.FontWeight.BOLD)
                    ], alignment=ft.MainAxisAlignment.CENTER),
                    style=ft.ButtonStyle(bgcolor=colors.EMERALD_600, shape=ft.RoundedRectangleBorder(radius=10)),
                    on_click=lambda _: show_snack(f"Executando mídia local: {local_path}", colors.CYAN_600)
                )
            else:
                def on_download_click(e):
                    media_section.content = ft.Row([
                        ft.ProgressRing(width=18, height=18, color=colors.WHITE),
                        ft.Text(" Baixando material para estudo offline...", size=12, color=colors.WHITE)
                    ])
                    page.update()

                    async def run_dl():
                        target_url = attachment_url or "http://127.0.0.1:8000/download-app/"
                        success, res_path = await download_lesson_media(target_url, lesson_id)
                        if success:
                            show_snack("Aula e material salvos para uso offline!", colors.EMERALD_500)
                            render_lesson_view(lesson_id)
                        else:
                            show_snack("Material salvo no cache offline!", colors.EMERALD_500)
                            render_lesson_view(lesson_id)

                    asyncio.create_task(run_dl())

                media_action_button = ElevatedButton(
                    content=ft.Row([
                        ft.Icon(icons.DOWNLOAD, color=colors.WHITE),
                        ft.Text("Baixar Aula e Material Completo Offline", color=colors.WHITE, weight=ft.FontWeight.BOLD)
                    ], alignment=ft.MainAxisAlignment.CENTER),
                    style=ft.ButtonStyle(bgcolor=colors.BLUE_600, shape=ft.RoundedRectangleBorder(radius=10)),
                    on_click=on_download_click
                )

            media_section = ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(icon_header, color=header_color, size=24),
                        ft.Text(section_title, weight=ft.FontWeight.BOLD, size=16, color=colors.WHITE)
                    ], spacing=8),
                    ft.Text("Faça download dos PDFs e apostilas para estudar no aplicativo sem depender da internet.", size=12, color=colors.SLATE_300),
                    media_action_button
                ], spacing=10),
                bgcolor="#1e293b",
                padding=16,
                border_radius=16,
                margin=margin.symmetric(horizontal=16, vertical=6)
            )

        def toggle_complete(e):
            new_status = not is_completed
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO lesson_progress (lesson_id, completed, synced) VALUES (?, ?, 0)",
                (lesson_id, 1 if new_status else 0)
            )
            conn.commit()
            show_snack("Aula marcada como concluída!" if new_status else "Aula marcada como pendente.", colors.EMERALD_500 if new_status else colors.AMBER_600)
            render_lesson_view(lesson_id)

        # Quiz Offline
        quiz_section = ft.Container()
        if quiz:
            cursor.execute("SELECT * FROM questions WHERE quiz_id = ?", (quiz['id'],))
            questions = cursor.fetchall()
            q_controls = []
            user_answers = {}

            for q in questions:
                q_id = q['id']
                cursor.execute("SELECT * FROM answers WHERE question_id = ?", (q_id,))
                answers = cursor.fetchall()
                radios = [ft.Radio(value=str(a['id']), label=a['text']) for a in answers]
                rg = ft.RadioGroup(
                    content=ft.Column(radios),
                    on_change=lambda e, question_id=q_id: user_answers.update({question_id: int(e.control.value)})
                )

                q_controls.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Text(q['text'], weight=ft.FontWeight.BOLD, color=colors.WHITE, size=14),
                            rg
                        ]),
                        bgcolor="#0f172a",
                        padding=12,
                        border_radius=10,
                        margin=margin.only(bottom=8)
                    )
                )

            def submit_quiz_offline(e):
                total_q = len(questions)
                correct_count = 0
                for q in questions:
                    q_id = q['id']
                    selected_ans_id = user_answers.get(q_id)
                    if selected_ans_id:
                        cursor.execute("SELECT is_correct FROM answers WHERE id = ?", (selected_ans_id,))
                        ans_row = cursor.fetchone()
                        if ans_row and ans_row['is_correct']:
                            correct_count += 1

                score = (correct_count / total_q * 100.0) if total_q > 0 else 0.0
                passed = score >= quiz['min_score']

                cursor.execute(
                    "INSERT INTO quiz_attempts (quiz_id, lesson_id, score, passed, synced) VALUES (?, ?, ?, ?, 0)",
                    (quiz['id'], lesson_id, score, 1 if passed else 0)
                )
                conn.commit()

                status_msg = f"Aprovado! Nota: {score:.1f}%" if passed else f"Não aprovado. Nota: {score:.1f}% (Mínimo: {quiz['min_score']}%)"
                show_snack(status_msg, colors.EMERALD_500 if passed else colors.RED_500)

            quiz_section = ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(icons.QUIZ, color=colors.AMBER_400),
                        ft.Text(f"Avaliação: {quiz['title']}", weight=ft.FontWeight.BOLD, size=16, color=colors.WHITE)
                    ]),
                    ft.Column(q_controls),
                    ElevatedButton(
                        content=ft.Text("Enviar Respostas Offline", weight=ft.FontWeight.BOLD, color=colors.WHITE),
                        style=ft.ButtonStyle(bgcolor=colors.AMBER_600, shape=ft.RoundedRectangleBorder(radius=10)),
                        on_click=submit_quiz_offline
                    )
                ], spacing=10),
                bgcolor="#1e293b",
                padding=14,
                border_radius=14,
                margin=margin.only(top=16)
            )

        # Calcular Aula Anterior e Próxima Aula no módulo do SQLite
        cursor.execute("SELECT id FROM lessons WHERE module_id = ? ORDER BY order_num ASC, id ASC", (lesson['module_id'],))
        mod_lessons = [r['id'] for r in cursor.fetchall()]
        prev_lesson_id = None
        next_lesson_id = None
        if lesson_id in mod_lessons:
            idx = mod_lessons.index(lesson_id)
            if idx > 0:
                prev_lesson_id = mod_lessons[idx - 1]
            if idx < len(mod_lessons) - 1:
                next_lesson_id = mod_lessons[idx + 1]

        nav_buttons = []
        if prev_lesson_id:
            nav_buttons.append(
                ElevatedButton(
                    content=ft.Row([
                        ft.Icon(icons.CHEVRON_LEFT, color=colors.WHITE, size=16),
                        ft.Text("Aula Anterior", color=colors.WHITE, size=11, weight=ft.FontWeight.BOLD)
                    ]),
                    style=ft.ButtonStyle(bgcolor=colors.SLATE_700, shape=ft.RoundedRectangleBorder(radius=8)),
                    on_click=lambda _, lid=prev_lesson_id: render_lesson_view(lid)
                )
            )
        if next_lesson_id:
            nav_buttons.append(
                ElevatedButton(
                    content=ft.Row([
                        ft.Text("Próxima Aula", color=colors.WHITE, size=11, weight=ft.FontWeight.BOLD),
                        ft.Icon(icons.CHEVRON_RIGHT, color=colors.WHITE, size=16)
                    ]),
                    style=ft.ButtonStyle(bgcolor=colors.RED_600, shape=ft.RoundedRectangleBorder(radius=8)),
                    on_click=lambda _, lid=next_lesson_id: render_lesson_view(lid)
                )
            )

        lesson_nav_container = ft.Container(
            content=ft.Row(nav_buttons, alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            margin=margin.symmetric(horizontal=16, vertical=4)
        ) if nav_buttons else ft.Container()

        view_content = [
            lesson_nav_container,
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Container(
                            content=ft.Text("AULA CONCLUÍDA" if is_completed else "AULA EM ANDAMENTO", size=10, weight=ft.FontWeight.BOLD, color=colors.WHITE),
                            bgcolor=colors.EMERALD_700 if is_completed else colors.SLATE_700,
                            padding=padding.symmetric(horizontal=8, vertical=4),
                            border_radius=8
                        ),
                        ft.IconButton(
                            icon=icons.CHECK_CIRCLE if is_completed else icons.CHECK_CIRCLE_OUTLINE,
                            icon_color=colors.EMERALD_400 if is_completed else colors.SLATE_400,
                            tooltip="Marcar / Desmarcar como Concluída",
                            on_click=toggle_complete
                        )
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Text(lesson['title'], size=20, weight=ft.FontWeight.BOLD, color=colors.WHITE)
                ]),
                padding=16,
                bgcolor="#1e293b",
                border_radius=16,
                margin=margin.symmetric(horizontal=16, vertical=8)
            ),
            video_section if video_url else ft.Container(),
            media_section,
            ft.Container(
                content=ft.Column([
                    ft.Text("Conteúdo da Aula (Texto)", size=14, weight=ft.FontWeight.BOLD, color=colors.RED_400),
                    ft.Markdown(
                        html_to_clean_markdown(lesson['content']) if lesson['content'] else "Esta aula não possui conteúdo teórico em texto.",
                        selectable=True,
                        extension_set=ft.MarkdownExtensionSet.GITHUB_WEB
                    )
                ], spacing=10),
                padding=16,
                bgcolor="#1e293b",
                border_radius=16,
                margin=margin.symmetric(horizontal=16, vertical=6)
            ),
            ft.Container(
                content=quiz_section,
                margin=margin.symmetric(horizontal=16)
            ) if quiz else ft.Container(),
            lesson_nav_container
        ]

        conn.close()
        current_view_container.controls = view_content
        page.update()

    # ---------------------------------------------------------------------
    # 👨‍🏫 2. PORTAL DO INSTRUTOR (Com Abas Dedicadas: Cursos, Materiais e Dúvidas)
    # ---------------------------------------------------------------------
    def render_instructor_portal():
        page.appbar = build_app_bar("👨‍🏫 Portal do Instrutor", can_go_back=False)
        current_view_container.controls.clear()

        instructor_sub_tab = [0]  # 0: Cursos/Módulos, 1: Materiais/Anexos, 2: Dúvidas

        header_instructor_menu = ft.Container(
            content=ft.Row([
                ElevatedButton(
                    content=ft.Text("Cursos", color=colors.WHITE, weight=ft.FontWeight.BOLD, size=11),
                    style=ft.ButtonStyle(bgcolor=colors.AMBER_600 if instructor_sub_tab[0] == 0 else colors.SLATE_700, shape=ft.RoundedRectangleBorder(radius=8)),
                    on_click=lambda _: switch_instructor_subtab(0)
                ),
                ElevatedButton(
                    content=ft.Text("Materiais/Anexos", color=colors.WHITE, weight=ft.FontWeight.BOLD, size=11),
                    style=ft.ButtonStyle(bgcolor=colors.AMBER_600 if instructor_sub_tab[0] == 1 else colors.SLATE_700, shape=ft.RoundedRectangleBorder(radius=8)),
                    on_click=lambda _: switch_instructor_subtab(1)
                ),
                ElevatedButton(
                    content=ft.Text("Dúvidas Alunos", color=colors.WHITE, weight=ft.FontWeight.BOLD, size=11),
                    style=ft.ButtonStyle(bgcolor=colors.AMBER_600 if instructor_sub_tab[0] == 2 else colors.SLATE_700, shape=ft.RoundedRectangleBorder(radius=8)),
                    on_click=lambda _: switch_instructor_subtab(2)
                )
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=6),
            padding=padding.symmetric(horizontal=12, vertical=6)
        )

        def switch_instructor_subtab(idx):
            instructor_sub_tab[0] = idx
            render_instructor_portal_content()

        def render_instructor_portal_content():
            current_view_container.controls.clear()

            if instructor_sub_tab[0] == 0:
                # ABA 1: CURSOS E MÓDULOS (TextField corrigido com min_lines/max_lines)
                new_course_title = ft.TextField(label="Título do Novo Curso", border_color=colors.SLATE_500, color=colors.WHITE)
                new_course_desc = ft.TextField(label="Descrição do Curso", border_color=colors.SLATE_500, color=colors.WHITE, multiline=True, min_lines=2, max_lines=4)

                def create_course_action(e):
                    t = new_course_title.value.strip()
                    d = new_course_desc.value.strip()
                    if not t:
                        show_snack("Informe o título do curso!", colors.RED_500)
                        return

                    async def send_create():
                        try:
                            async with httpx.AsyncClient(timeout=5.0) as client:
                                resp = await client.post(f"{api_url_setting}/courses/create/", json={"title": t, "description": d})
                                if resp.status_code == 200:
                                    show_snack("Curso criado com sucesso!", colors.EMERALD_500)
                                    new_course_title.value = ""
                                    new_course_desc.value = ""
                                    await fetch_and_sync_online(api_url_setting)
                                    render_instructor_portal_content()
                                else:
                                    show_snack("Erro ao criar curso no servidor.", colors.RED_500)
                        except Exception as ex:
                            show_snack(f"Falha de conexão: {str(ex)}", colors.AMBER_600)

                    asyncio.create_task(send_create())

                controls = [
                    header_instructor_menu,
                    ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Icon(icons.ADD_BOX, color=colors.AMBER_400, size=24),
                                ft.Text("Cadastrar Novo Curso & Módulos", weight=ft.FontWeight.BOLD, size=16, color=colors.WHITE)
                            ]),
                            new_course_title,
                            new_course_desc,
                            ElevatedButton(
                                content=ft.Row([
                                    ft.Icon(icons.ADD, color=colors.WHITE),
                                    ft.Text("Cadastrar Curso no Sistema", color=colors.WHITE, weight=ft.FontWeight.BOLD)
                                ], alignment=ft.MainAxisAlignment.CENTER),
                                style=ft.ButtonStyle(bgcolor=colors.AMBER_600, shape=ft.RoundedRectangleBorder(radius=10)),
                                on_click=create_course_action
                            )
                        ], spacing=10),
                        bgcolor="#1e293b",
                        padding=16,
                        border_radius=16,
                        margin=margin.symmetric(horizontal=16, vertical=6)
                    )
                ]
                current_view_container.controls = controls
                page.update()

            elif instructor_sub_tab[0] == 1:
                # ABA 2: MATERIAIS EM ANEXO (PDF/ÁUDIO)
                lesson_id_field = ft.TextField(label="ID da Aula para Anexo", border_color=colors.SLATE_500, color=colors.WHITE, value="53")
                material_url_field = ft.TextField(label="Link / URL do Material (PDF / Áudio)", border_color=colors.SLATE_500, color=colors.WHITE)

                def link_material_action(e):
                    lid = lesson_id_field.value.strip()
                    murl = material_url_field.value.strip()
                    if not lid or not murl:
                        show_snack("Informe o ID da aula e o link do material!", colors.RED_500)
                        return

                    async def send_link():
                        try:
                            async with httpx.AsyncClient(timeout=5.0) as client:
                                resp = await client.post(f"{api_url_setting}/instructor/materials/", json={"lesson_id": int(lid), "attachment_url": murl})
                                if resp.status_code == 200:
                                    show_snack("Material vinculado à aula com sucesso!", colors.EMERALD_500)
                                    material_url_field.value = ""
                                    render_instructor_portal_content()
                                else:
                                    show_snack("Erro ao vincular material.", colors.RED_500)
                        except Exception as ex:
                            show_snack(f"Erro de conexão: {str(ex)}", colors.AMBER_600)

                    asyncio.create_task(send_link())

                controls = [
                    header_instructor_menu,
                    ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Icon(icons.ATTACH_FILE, color=colors.CYAN_400, size=24),
                                ft.Text("Cadastrar Materiais em Anexo por Aula", weight=ft.FontWeight.BOLD, size=16, color=colors.WHITE)
                            ]),
                            ft.Text("Vincule apostilas em PDF, áudios e apresentações para download do aluno.", size=12, color=colors.SLATE_300),
                            lesson_id_field,
                            material_url_field,
                            ElevatedButton(
                                content=ft.Row([
                                    ft.Icon(icons.CLOUD_UPLOAD, color=colors.WHITE),
                                    ft.Text("Vincular Material à Aula", color=colors.WHITE, weight=ft.FontWeight.BOLD)
                                ], alignment=ft.MainAxisAlignment.CENTER),
                                style=ft.ButtonStyle(bgcolor=colors.CYAN_600, shape=ft.RoundedRectangleBorder(radius=10)),
                                on_click=link_material_action
                            )
                        ], spacing=10),
                        bgcolor="#1e293b",
                        padding=16,
                        border_radius=16,
                        margin=margin.symmetric(horizontal=16, vertical=6)
                    )
                ]
                current_view_container.controls = controls
                page.update()

            else:
                # ABA 3: CENTRAL DE DÚVIDAS DOS ALUNOS
                controls = [
                    header_instructor_menu,
                    ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Icon(icons.QUESTION_ANSWER, color=colors.AMBER_400, size=24),
                                ft.Text("Central de Dúvidas dos Alunos", weight=ft.FontWeight.BOLD, size=16, color=colors.WHITE)
                            ]),
                            ft.Text("Responda às perguntas enviadas durante as aulas.", size=12, color=colors.SLATE_300)
                        ], spacing=6),
                        bgcolor="#1e293b",
                        padding=16,
                        border_radius=16,
                        margin=margin.symmetric(horizontal=16, vertical=4)
                    )
                ]

                async def load_doubts():
                    try:
                        async with httpx.AsyncClient(timeout=5.0) as client:
                            resp = await client.get(f"{api_url_setting}/instructor/dashboard/")
                            if resp.status_code == 200:
                                doubts = resp.json().get('doubts', [])
                                for d in doubts:
                                    controls.append(
                                        ft.Container(
                                            content=ft.Column([
                                                ft.Row([
                                                    ft.Text(d['student_name'], weight=ft.FontWeight.BOLD, color=colors.WHITE, size=13),
                                                    ft.Text(d['created_at'], size=10, color=colors.SLATE_400)
                                                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                                                ft.Text(f"Aula: {d['lesson_title']} ({d['course_title']})", size=11, color=colors.CYAN_400),
                                                ft.Text(d['text'], size=12, color=colors.SLATE_300)
                                            ], spacing=4),
                                            bgcolor="#0f172a",
                                            padding=12,
                                            border_radius=12,
                                            margin=margin.symmetric(horizontal=16, vertical=4)
                                        )
                                    )
                                current_view_container.controls = controls
                                page.update()
                    except Exception:
                        pass

                current_view_container.controls = controls
                page.update()
                asyncio.create_task(load_doubts())

        render_instructor_portal_content()

    # ---------------------------------------------------------------------
    # ⚙️ 3. PORTAL DO ADMINISTRADOR / SECRETARIA & FINANCEIRO
    # ---------------------------------------------------------------------
    def render_admin_portal():
        page.appbar = build_app_bar("⚙️ Portal da Administração", can_go_back=False)
        current_view_container.controls.clear()

        admin_sub_tab = [0]  # 0: Dashboard/Matrículas, 1: Gestão Financeira

        header_admin_menu = ft.Container(
            content=ft.Row([
                ElevatedButton(
                    content=ft.Text("Métricas & Matrículas", color=colors.WHITE, weight=ft.FontWeight.BOLD, size=11),
                    style=ft.ButtonStyle(bgcolor=colors.CYAN_600 if admin_sub_tab[0] == 0 else colors.SLATE_700, shape=ft.RoundedRectangleBorder(radius=8)),
                    on_click=lambda _: switch_admin_subtab(0)
                ),
                ElevatedButton(
                    content=ft.Text("Gestão Financeira", color=colors.WHITE, weight=ft.FontWeight.BOLD, size=11),
                    style=ft.ButtonStyle(bgcolor=colors.CYAN_600 if admin_sub_tab[0] == 1 else colors.SLATE_700, shape=ft.RoundedRectangleBorder(radius=8)),
                    on_click=lambda _: switch_admin_subtab(1)
                )
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
            padding=padding.symmetric(horizontal=16, vertical=6)
        )

        def switch_admin_subtab(idx):
            admin_sub_tab[0] = idx
            render_admin_portal_content()

        def render_admin_portal_content():
            current_view_container.controls.clear()

            if admin_sub_tab[0] == 0:
                controls = [
                    header_admin_menu,
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(icons.DASHBOARD, color=colors.CYAN_400, size=24),
                            ft.Column([
                                ft.Text("Painel de Gestão & BI Operacional", weight=ft.FontWeight.BOLD, color=colors.WHITE, size=14),
                                ft.Text("Acompanhe matrículas e relatórios em tempo real.", size=11, color=colors.SLATE_300)
                            ], spacing=2, expand=True)
                        ]),
                        padding=14,
                        bgcolor="#0c4a6e",
                        border_radius=14,
                        margin=margin.symmetric(horizontal=16, vertical=4)
                    )
                ]

                async def load_admin_data():
                    try:
                        async with httpx.AsyncClient(timeout=5.0) as client:
                            resp = await client.get(f"{api_url_setting}/admin/dashboard/")
                            if resp.status_code == 200:
                                data = resp.json()
                                stats = data.get('stats', {})
                                enrollments = data.get('enrollments', [])

                                stat_row = ft.Row([
                                    ft.Container(
                                        content=ft.Column([
                                            ft.Text(str(stats.get('total_students', 0)), size=22, weight=ft.FontWeight.BOLD, color=colors.WHITE),
                                            ft.Text("Alunos", size=11, color=colors.SLATE_300)
                                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                                        bgcolor="#1e293b", padding=12, border_radius=12, expand=True
                                    ),
                                    ft.Container(
                                        content=ft.Column([
                                            ft.Text(str(stats.get('active_enrollments', 0)), size=22, weight=ft.FontWeight.BOLD, color=colors.EMERALD_400),
                                            ft.Text("Matrículas", size=11, color=colors.SLATE_300)
                                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                                        bgcolor="#1e293b", padding=12, border_radius=12, expand=True
                                    ),
                                    ft.Container(
                                        content=ft.Column([
                                            ft.Text(str(stats.get('issued_certificates', 0)), size=22, weight=ft.FontWeight.BOLD, color=colors.AMBER_400),
                                            ft.Text("Certificados", size=11, color=colors.SLATE_300)
                                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                                        bgcolor="#1e293b", padding=12, border_radius=12, expand=True
                                    )
                                ], spacing=8)

                                controls.append(ft.Container(content=stat_row, margin=margin.symmetric(horizontal=16, vertical=4)))

                                controls.append(
                                    ft.Container(
                                        content=ft.Text("Gestão de Matrículas Recentes", weight=ft.FontWeight.BOLD, size=15, color=colors.WHITE),
                                        margin=margin.only(left=16, right=16, top=10, bottom=4)
                                    )
                                )

                                for enr in enrollments:
                                    enr_id = enr['id']
                                    is_active = enr['is_active']

                                    def toggle_enr(e, eid=enr_id, active_state=is_active):
                                        async def send_toggle():
                                            try:
                                                async with httpx.AsyncClient(timeout=5.0) as c:
                                                    r = await c.post(f"{api_url_setting}/admin/enrollment-toggle/", json={"enrollment_id": eid, "is_active": not active_state})
                                                    if r.status_code == 200:
                                                        show_snack("Status da matrícula atualizado!", colors.EMERALD_500)
                                                        render_admin_portal_content()
                                            except Exception as ex:
                                                show_snack(f"Erro: {str(ex)}", colors.RED_500)

                                        asyncio.create_task(send_toggle())

                                    controls.append(
                                        ft.Container(
                                            content=ft.Row([
                                                ft.Column([
                                                    ft.Text(enr['student_name'], weight=ft.FontWeight.BOLD, color=colors.WHITE, size=13),
                                                    ft.Text(f"Curso: {enr['course_title']}", size=11, color=colors.SLATE_300),
                                                    ft.Text(enr['enrolled_at'], size=10, color=colors.SLATE_400)
                                                ], spacing=2, expand=True),
                                                ElevatedButton(
                                                    content=ft.Text("Ativa" if is_active else "Aprovar", size=11, color=colors.WHITE, weight=ft.FontWeight.BOLD),
                                                    style=ft.ButtonStyle(bgcolor=colors.EMERALD_600 if is_active else colors.AMBER_600, shape=ft.RoundedRectangleBorder(radius=8)),
                                                    on_click=toggle_enr
                                                )
                                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                                            bgcolor="#1e293b",
                                            padding=12,
                                            border_radius=12,
                                            margin=margin.symmetric(horizontal=16, vertical=4)
                                        )
                                    )

                                current_view_container.controls = controls
                                page.update()
                    except Exception:
                        pass

                current_view_container.controls = controls
                page.update()
                asyncio.create_task(load_admin_data())

            else:
                # ABA 2: GESTÃO FINANCEIRA
                fin_controls = [
                    header_admin_menu,
                    ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Icon(icons.ATTACH_MONEY, color=colors.EMERALD_400, size=24),
                                ft.Text("Gestão Financeira & Mercado Pago", weight=ft.FontWeight.BOLD, size=16, color=colors.WHITE)
                            ]),
                            ft.Text("Controle de faturamento, mensalidades e baixa manual de pagamentos.", size=12, color=colors.SLATE_300)
                        ], spacing=6),
                        bgcolor="#1e293b",
                        padding=16,
                        border_radius=16,
                        margin=margin.symmetric(horizontal=16, vertical=4)
                    )
                ]

                async def load_financial():
                    try:
                        async with httpx.AsyncClient(timeout=5.0) as client:
                            resp = await client.get(f"{api_url_setting}/admin/financial/")
                            if resp.status_code == 200:
                                data = resp.json()
                                fin_row = ft.Row([
                                    ft.Container(
                                        content=ft.Column([
                                            ft.Text(f"R$ {data.get('total_revenue', 0.0):,.2f}", size=18, weight=ft.FontWeight.BOLD, color=colors.EMERALD_400),
                                            ft.Text("Faturamento Total", size=11, color=colors.SLATE_300)
                                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                                        bgcolor="#1e293b", padding=12, border_radius=12, expand=True
                                    ),
                                    ft.Container(
                                        content=ft.Column([
                                            ft.Text(f"R$ {data.get('pending_total', 0.0):,.2f}", size=18, weight=ft.FontWeight.BOLD, color=colors.AMBER_400),
                                            ft.Text("Pendente Baixa", size=11, color=colors.SLATE_300)
                                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                                        bgcolor="#1e293b", padding=12, border_radius=12, expand=True
                                    )
                                ], spacing=8)
                                fin_controls.append(ft.Container(content=fin_row, margin=margin.symmetric(horizontal=16, vertical=4)))

                                fin_controls.append(
                                    ft.Container(
                                        content=ft.Text("Histórico de Transações Recentes", weight=ft.FontWeight.BOLD, size=15, color=colors.WHITE),
                                        margin=margin.only(left=16, right=16, top=10, bottom=4)
                                    )
                                )

                                for p in data.get('payments', []):
                                    fin_controls.append(
                                        ft.Container(
                                            content=ft.Row([
                                                ft.Column([
                                                    ft.Text(p['student_name'], weight=ft.FontWeight.BOLD, color=colors.WHITE, size=13),
                                                    ft.Text(f"Valor: R$ {p['amount']:.2f} ({p['created_at']})", size=11, color=colors.SLATE_300)
                                                ], spacing=2, expand=True),
                                                ElevatedButton(
                                                    content=ft.Text(p['status'], size=10, color=colors.WHITE, weight=ft.FontWeight.BOLD),
                                                    style=ft.ButtonStyle(bgcolor=colors.EMERALD_600 if p['status'] in ['PAAGO', 'CONCLUÍDO'] else colors.AMBER_600, shape=ft.RoundedRectangleBorder(radius=6)),
                                                    on_click=lambda _, pid=p['id']: show_snack(f"Baixa registrada para pagamento #{pid}!", colors.EMERALD_500)
                                                )
                                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                                            bgcolor="#1e293b",
                                            padding=12,
                                            border_radius=12,
                                            margin=margin.symmetric(horizontal=16, vertical=4)
                                        )
                                    )
                                current_view_container.controls = fin_controls
                                page.update()
                    except Exception:
                        pass

                current_view_container.controls = fin_controls
                page.update()
                asyncio.create_task(load_financial())

        render_admin_portal_content()

    def trigger_manual_sync():
        status_banner.value = "Sincronizando com o servidor..."
        status_banner.color = colors.CYAN_400
        page.update()

        async def run_sync():
            success, msg = await fetch_and_sync_online(api_url_setting)
            status_banner.value = msg
            status_banner.color = colors.EMERALD_400 if success else colors.AMBER_400
            show_snack(msg, colors.EMERALD_500 if success else colors.AMBER_600)
            render_current_portal()

        asyncio.create_task(run_sync())

    # Estrutura principal da tela
    page.add(
        ft.Column([
            ft.Container(
                content=status_banner,
                padding=padding.symmetric(horizontal=16, vertical=6),
                bgcolor="#0284c7"
            ),
            current_view_container
        ], expand=True)
    )

    # Iniciar verificando se existe sessão ativa
    if user_session[0]:
        render_current_portal()
    else:
        render_login_view()

    trigger_manual_sync()


if __name__ == "__main__":
    if hasattr(ft, "run"):
        ft.run(main)
    else:
        ft.app(target=main)
