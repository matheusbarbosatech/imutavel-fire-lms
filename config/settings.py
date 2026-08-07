import os
from pathlib import Path
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent

# 🔐 SEGURANÇA
SECRET_KEY = config('SECRET_KEY', default='django-insecure-dev-key-change-in-production')
DEBUG = config('DEBUG', default=True, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=lambda v: [s.strip() for s in v.split(',')])

# 📦 APPS
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',
]

# 🔄 MIDDLEWARE
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'
TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [BASE_DIR / 'templates'],
    'APP_DIRS': True,
    'OPTIONS': {
        'context_processors': [
            'django.template.context_processors.debug',
            'django.template.context_processors.request',
            'django.contrib.auth.context_processors.auth',
            'django.contrib.messages.context_processors.messages',
        ],
    },
}]
WSGI_APPLICATION = 'config.wsgi.application'

# 🗄️ BANCO DE DADOS - USANDO POOLER DO SUPABASE (IPv4 garantido)
if not DEBUG:
    # PRODUÇÃO (Render) - USA O POOLER DO SUPABASE
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': 'postgres',
            # ⚠️ USUÁRIO DO POOLER: postgres.[project-ref]
            'USER': 'postgres.taddgzgbgstttecbvkmc',
            'PASSWORD': 'SenhaMatricula2026!',
            # ⚠️ HOST DO POOLER: substitua pelo que você copiou do Supabase
            'HOST': 'aws-0-us-east-1.pooler.supabase.com',  # ← COLE O SEU HOST DO POOLER AQUI
            'PORT': '6543',
            'OPTIONS': {
                'sslmode': 'require',
                'connect_timeout': 15,
            }
        }
    }
else:
    # DESENVOLVIMENTO LOCAL
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': config('DB_NAME', default='postgres'),
            'USER': config('DB_USER', default='postgres.taddgzgbgstttecbvkmc'),
            'PASSWORD': config('DB_PASSWORD', default='SenhaMatricula2026!'),
            'HOST': config('DB_HOST', default='aws-0-us-east-1.pooler.supabase.com'),
            'PORT': config('DB_PORT', default='6543'),
            'OPTIONS': {
                'sslmode': 'require',
                'connect_timeout': 15,
            }
        }
    }

# 🔐 VALIDAÇÃO DE SENHA
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
]

LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# 📁 ESTÁTICOS
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# 📧 E-MAIL
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST', default='smtp-relay.brevo.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = 'Matrículas <naoresponda@seudominio.com>'

# ☁️ STORAGE
SUPABASE_URL = config('SUPABASE_URL', default='https://taddgzgbgstttecbvkmc.supabase.co')
SUPABASE_SERVICE_KEY = config('SUPABASE_SERVICE_KEY', default='')
SUPABASE_BUCKET = config('SUPABASE_BUCKET', default='matricula-docs')
DEFAULT_FILE_STORAGE = 'core.storage.SupabaseStorage'

# 🔒 SEGURANÇA PRODUÇÃO
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

    # Permite qualquer host temporariamente para evitar bloqueios do proxy do Render
ALLOWED_HOSTS = ['*']

# FORÇA O DJANGO A IMPRIMIR ERROS 500 NO CONSOLE DO RENDER
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': True,
        },
    },
}

BREVO_API_KEY = config('BREVO_API_KEY', default='')