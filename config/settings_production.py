"""生产配置。通过 DJANGO_SETTINGS_MODULE=config.settings_production 启用。"""
import os
from pathlib import Path
from django.core.exceptions import ImproperlyConfigured
from .settings import *  # noqa: F403


def required(name):
    value = os.environ.get(name, '').strip()
    if not value:
        raise ImproperlyConfigured(f'生产环境必须设置 {name}')
    return value


SECRET_KEY = required('DJANGO_SECRET_KEY')
DEBUG = False
ALLOWED_HOSTS = [host.strip() for host in required('DJANGO_ALLOWED_HOSTS').split(',') if host.strip()]
if not ALLOWED_HOSTS or '*' in ALLOWED_HOSTS:
    raise ImproperlyConfigured('DJANGO_ALLOWED_HOSTS 必须列出具体域名或 IP')
CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in os.environ.get('DJANGO_CSRF_TRUSTED_ORIGINS', '').split(',') if origin.strip()]
DATABASES['default']['NAME'] = Path(os.environ.get('DJANGO_DB_PATH', '/var/lib/course-order/db.sqlite3'))  # noqa: F405
STATIC_URL = '/static/'
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'same-origin'
# SimpleUI 后台使用同源 iframe；仅允许本站嵌入。
X_FRAME_OPTIONS = 'SAMEORIGIN'
RESTORE_FRAME_MIDDLEWARE = True

# 当前站点不发送邮件；如需邮件功能，应配置真实 SMTP 服务。
MAILERS = {'default': {'BACKEND': 'django.core.mail.backends.smtp.EmailBackend'}}
