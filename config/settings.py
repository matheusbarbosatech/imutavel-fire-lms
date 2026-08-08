import os
from pathlib import Path
import dj_database_url

# 1. DIRETÓRIO BASE DO PROJETO
# Constrói os caminhos dentro do projeto como: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# 2. SEGURANÇA E AMBIENTE
# Usa a SECRET_KEY do ambiente (em produção) ou uma chave fixa apenas para desenvolvimento local
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-sua-chave-secreta-padrao-aqui-troque-em-prod')

# Se a variável 'RENDER' existir no ambiente, estamos em produção, logo DEBUG fica False. 
# Caso contrário (no seu PC), DEBUG fica True.
DEBUG = 'RENDER' not in os.environ

# Permite que o Render acesse a aplicação
ALLOWED_HOSTS = ['*']

# 🟢 ADICIONE ESTAS LINHAS: Diz ao Django para confiar no protocolo HTTPS do Render
CSRF_TRUSTED_ORIGINS = [
    'https://*.onrender.com',
    'https://sistema-matricula-fmp9.onrender.com',
]


# 3. APLICATIVOS INSTALADOS
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Aplicativos do IMUTÁVEL FIRE LMS
    'apps.accounts',
    'apps.courses',
    'apps.quizzes',
    'apps.certificates',
    'apps.management',
]


# 4. MIDDLEWARES (Interceptadores de Requisição)
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # WhiteNoise deve ficar imediatamente abaixo do SecurityMiddleware para otimizar os estáticos
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

# 5. TEMPLATES (Arquivos HTML)
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')], # Aponta para a pasta templates na raiz
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# 6. BANCO DE DADOS
# Usa o PostgreSQL remoto se a variável DATABASE_URL estiver configurada.
# Se não estiver (no seu computador), usa o db.sqlite3 nativo.
DATABASES = {
    'default': dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600
    )
}


# 7. VALIDAÇÃO DE SENHAS
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# 8. INTERNACIONALIZAÇÃO (Idioma e Fuso Horário)
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True


# 9. ARQUIVOS ESTÁTICOS E MÍDIA (CSS, JS, Imagens, PDFs)
STATIC_URL = '/static/'
# Onde ficam seus estáticos de desenvolvimento (css, img, js)
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
# Onde o Django vai juntar todos os estáticos na hora do Deploy
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Ativa a compressão e otimização do WhiteNoise para produção
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Mídias dinâmicas enviadas pelo usuário (Fotos, Documentos e PDFs gerados)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')


# 10. CONFIGURAÇÕES CUSTOMIZADAS DO SISTEMA
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Indica qual é o modelo principal de Usuário do sistema
AUTH_USER_MODEL = 'accounts.CustomUser'

# Redirecionamentos de Login e Logout usando namespaces
LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'courses:student_dashboard'
LOGOUT_REDIRECT_URL = 'accounts:login'