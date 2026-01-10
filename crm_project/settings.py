from pathlib import Path
import os
import pymysql
from urllib.parse import urlparse
import pymysql

# Cargar variables de entorno desde .env
import dotenv
dotenv.load_dotenv()

pymysql.install_as_MySQLdb()


# Paths
BASE_DIR = Path(__file__).resolve().parent.parent

# Seguridad
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "AlfredoLemusG1022$")
DEBUG = os.getenv("DEBUG", "False") == "True"

ALLOWED_HOSTS = ["*"]  # ⚠️ En producción, reemplazar con dominios específicos

# Aplicaciones
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    "ventas.apps.VentasConfig", 
    'compras', 
    'inventario',
    'reportes',  # Fase 3: Dashboards y reportes
]

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

ROOT_URLCONF = 'crm_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / "templates"],
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

WSGI_APPLICATION = 'crm_project.wsgi.application'

db_url = os.getenv("MYSQL_PUBLIC_URL", "mysql://root:oNwIXFdUIgRVZLWVsUYgdKsbbiaqONCh@mainline.proxy.rlwy.net:23404/railway")
parsed_url = urlparse(db_url)

#PRODUCCION
# ✅ Base de datos usando Railway MySQL (Con seguridad mejorada)
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.mysql',
#         'NAME': os.getenv('MYSQLDATABASE', 'crm_db'),
#         'USER': os.getenv('MYSQLUSER'),
#         'PASSWORD': os.getenv('MYSQLPASSWORD'),
#         'HOST': os.getenv('MYSQLHOST'),
#         'PORT': os.getenv('MYSQLPORT', '3306'),
#     }
# }

#LOCAL:
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'crm_db',  # Reemplázalo por el nombre correcto si es diferente
        'USER': 'root',     # O el usuario que usaste para crear la DB
        'PASSWORD': 'AlfredoLemusG1022$',  # La contraseña local de MySQL
        'HOST': 'localhost',
        'PORT': '3306',
    }
}

# Validación de contraseñas
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internacionalización
LANGUAGE_CODE = 'es-mx'
TIME_ZONE = 'America/Mexico_City'
USE_I18N = True
USE_TZ = True

# Archivos estáticos productivos:
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
# Directorios adicionales donde Django buscará archivos estáticos en desarrollo: Para pro sólo borra loas siguientes  3 líneas
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),  # Asegura que 'static' es el nombre correcto de tu carpeta de estáticos
]

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Aseguramos que los archivos estáticos se sirvan en producción
if not DEBUG:
    STATICFILES_STORAGE = "whitenoise.storage.CompressedStaticFilesStorage"

# Clave primaria automática
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
