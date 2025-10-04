"""
Django settings for avtolider_bot project.
"""

import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-1q8%28=3rx+q5fmd4wvii*dh4#(&e_4^j+^ryl$f&=f&+g+oy='  # Keyinroq environment variable ga o'tkazish maqsadga muvofiq

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False  # ✅ Production uchun False qiling

ALLOWED_HOSTS = [
    "avtolider.medias.uz", 
    "localhost", 
    "127.0.0.1",
    "www.avtolider.medias.uz",  # ✅ WWW uchun qo'shing
    "45.151.122.32"  # ✅ Server IP manzilingizni qo'shing
]


# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'admin_auto_filters',

    'bot',
    'users',
    'payments',
    'subscriptions',
    'quizzes',
    'tests',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'avtolider_bot.urls'

TEMPLATES = [
    {
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
    },
]

WSGI_APPLICATION = 'avtolider_bot.wsgi.application'


# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'avtolider_db',
        'USER': 'postgres',
        'PASSWORD': 'bunyod1202',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# Password validation
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


# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Tashkent'
USE_I18N = True
USE_TZ = False


# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')  # ✅ staticfiles papkasiga o'zgartiring
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),  # ✅ Development uchun static papka
]

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media/')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# CSRF
CSRF_TRUSTED_ORIGINS = [
    "https://avtolider.medias.uz",
    "https://www.avtolider.medias.uz",  # ✅ WWW uchun qo'shing
]

# ✅ Xavfsizlik sozlamalari
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# ✅ Session sozlamalari
SESSION_COOKIE_SECURE = True  # ✅ HTTPS uchun
CSRF_COOKIE_SECURE = True     # ✅ HTTPS uchun