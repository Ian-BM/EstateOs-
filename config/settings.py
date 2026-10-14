import os
from pathlib import Path
from django.core.exceptions import ImproperlyConfigured
BASE_DIR = Path(__file__).resolve().parent.parent
DEBUG = os.environ.get('DJANGO_DEBUG', '1') == '1'
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
if not SECRET_KEY:
    if not DEBUG:
        raise ImproperlyConfigured('Set DJANGO_SECRET_KEY in production.')
    secret_file = BASE_DIR / '.local-secret'
    if not secret_file.exists():
        import secrets
        secret_file.write_text(secrets.token_urlsafe(64))
        secret_file.chmod(0o600)
    SECRET_KEY = secret_file.read_text().strip()
ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS','127.0.0.1,localhost,testserver').split(',')
INSTALLED_APPS = ['django.contrib.admin','django.contrib.auth','django.contrib.contenttypes','django.contrib.sessions','django.contrib.messages','django.contrib.staticfiles','django.contrib.humanize','core','accounts','agencies','properties','management','crm']
MIDDLEWARE = ['django.middleware.security.SecurityMiddleware','django.contrib.sessions.middleware.SessionMiddleware','django.middleware.common.CommonMiddleware','django.middleware.csrf.CsrfViewMiddleware','django.contrib.auth.middleware.AuthenticationMiddleware','django.contrib.messages.middleware.MessageMiddleware','django.middleware.clickjacking.XFrameOptionsMiddleware']
ROOT_URLCONF = 'config.urls'
TEMPLATES = [{'BACKEND':'django.template.backends.django.DjangoTemplates','DIRS':[BASE_DIR/'templates'],'APP_DIRS':True,'OPTIONS':{'context_processors':['django.template.context_processors.request','django.contrib.auth.context_processors.auth','django.contrib.messages.context_processors.messages','core.context.workspace']}}]
WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'
DATABASES = {'default': {'ENGINE':os.environ.get('DB_ENGINE','django.db.backends.sqlite3'),'NAME':os.environ.get('DB_NAME',str(BASE_DIR/'db.sqlite3'))}}
if DATABASES['default']['ENGINE'] != 'django.db.backends.sqlite3':
    DATABASES['default'].update({key:os.environ.get('DB_'+key,'') for key in ['USER','PASSWORD','HOST','PORT']})
AUTH_PASSWORD_VALIDATORS = [{'NAME':'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},{'NAME':'django.contrib.auth.password_validation.MinimumLengthValidator'},{'NAME':'django.contrib.auth.password_validation.CommonPasswordValidator'},{'NAME':'django.contrib.auth.password_validation.NumericPasswordValidator'}]
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Dar_es_Salaam'
USE_I18N = True
USE_TZ = True
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR/'static']
STATIC_ROOT = Path(os.environ.get('DJANGO_STATIC_ROOT', str(BASE_DIR/'staticfiles')))
MEDIA_URL = '/media/'
MEDIA_ROOT = Path(os.environ.get('DJANGO_MEDIA_ROOT', str(BASE_DIR/'media')))
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/workspace/'
LOGOUT_REDIRECT_URL = '/'
EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND','django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = os.environ.get('EMAIL_HOST','localhost')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT','587'))
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER','')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD','')
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS','1') == '1'
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL','Estate OS <noreply@example.invalid>')
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000
DATA_UPLOAD_MAX_MEMORY_SIZE = 10485760
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880

CSRF_TRUSTED_ORIGINS = [origin for origin in os.environ.get('DJANGO_CSRF_TRUSTED_ORIGINS','').split(',') if origin]
# Enable only behind a controlled proxy that overwrites X-Forwarded-Proto.
if os.environ.get('DJANGO_TRUST_PROXY','0') == '1':
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO','https')
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False

STATIC_ASSET_VERSION = os.environ.get('DJANGO_ASSET_VERSION', BASE_DIR.name if BASE_DIR.parent.name == 'releases' else 'local-mobile-v1')
