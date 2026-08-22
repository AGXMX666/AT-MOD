import os
from pathlib import Path
import django.contrib.admin
BASE_DIR = Path(__file__).resolve().parent.parent


INSTALLED_APPS = [
    'daphne',
    'channels',
    'simpleui',
    'AT',
    'database',
    'captcha',
    'import_export',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    }
}

MIDDLEWARE = [
    'AT.middleware.SuppressDebugMiddleware', 
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / "templates", ],
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

ROOT_URLCONF = 'AT.urls'
WSGI_APPLICATION = 'AT.wsgi.application'
LANGUAGE_CODE = 'zh-Hans'
TIME_ZONE = 'Asia/Shanghai'
USE_I18N = True
USE_TZ = True
STATIC_ROOT =os.path.join(BASE_DIR, 'resources') 
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
STATIC_ADMIN = os.path.join(Path(django.contrib.admin.__file__).parent,'static')
STATIC_URL = '/static/'
SIMPLEUI_DEFAULT_THEME = 'admin.lte.css'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',       
    }
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
ASGI_APPLICATION = 'AT.asgi.application'

# SECRET_KEY 通过环境变量注入；默认值仅供本地开发（DEBUG=True）使用
SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY',
    'django-insecure-_8)f@=g5+%vz8!j@9%cae!2(=__!a5$53a0e=x-(c_8suo$xby'
)
# API 签名共享密钥：生产环境务必用环境变量单独设置，与 SECRET_KEY 分离
API_SECRET_KEY = os.environ.get('API_SECRET_KEY', SECRET_KEY)

DEBUG = os.environ.get('DJANGO_DEBUG', 'True').strip().lower() in ('1', 'true', 'yes', 'on')
ALLOWED_HOSTS = ['at.agxmx.cn','127.0.0.1',]
CSRF_TRUSTED_ORIGINS = ['https://at.agxmx.cn','http://127.0.0.1:8000',]
TEMPLATE_DEBUG = DEBUG
SESSION_COOKIE_SECURE = os.environ.get('DJANGO_SESSION_COOKIE_SECURE', str(not DEBUG)).strip().lower() in ('1', 'true', 'yes', 'on')
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_SECURE = os.environ.get('DJANGO_CSRF_COOKIE_SECURE', str(not DEBUG)).strip().lower() in ('1', 'true', 'yes', 'on')
SECURE_CONTENT_TYPE_NOSNIFF = True
DEBUG_PAGE_OFF = False

MAX_UPLOAD_SIZE = 10 * 1024 * 1024 
UPLOAD_OPTIME=60
