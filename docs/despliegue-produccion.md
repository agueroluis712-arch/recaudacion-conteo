# Despliegue en producción

La configuración productiva utiliza tres servicios:

- `frontend`: archivos React compilados, servidos por Nginx; también deriva `/api/` al backend.
- `backend`: Django ejecutado con Gunicorn.
- `db`: PostgreSQL 17 con volumen persistente.

El único puerto publicado por Docker es el del frontend (`8080` por defecto). El proveedor cloud o un proxy externo debe terminar HTTPS y dirigir el dominio a ese puerto.

## 1. Preparar las variables

Copiar `.env.production.example` como `.env.production` y reemplazar todos los valores de ejemplo.

Generar una clave de Django sin guardarla en el historial de comandos:

```powershell
.\.venv\Scripts\python.exe -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Valores obligatorios:

- `DJANGO_SECRET_KEY`: clave aleatoria de al menos 50 caracteres.
- `DJANGO_ALLOWED_HOSTS`: dominio público, sin `https://`.
- `DJANGO_CSRF_TRUSTED_ORIGINS`: URL completa con `https://`.
- `APP_PUBLIC_URL`: URL pública completa.
- `DB_PASSWORD`: contraseña exclusiva y robusta.
- variables `EMAIL_*`: servidor SMTP institucional o del proveedor seleccionado.

No subir `.env.production` a Git. Está excluido por `.gitignore`.

## 2. Construir y verificar

```powershell
docker compose --env-file .env.production -f compose.prod.yaml config
docker compose --env-file .env.production -f compose.prod.yaml build
docker compose --env-file .env.production -f compose.prod.yaml up -d
```

Comprobar:

```powershell
docker compose --env-file .env.production -f compose.prod.yaml ps
docker compose --env-file .env.production -f compose.prod.yaml logs --tail 100 backend
```

Las migraciones y `collectstatic` se ejecutan automáticamente antes de iniciar Gunicorn.

## 3. Crear el primer administrador

Con producción activa, ejecutar una sola vez:

```powershell
docker compose --env-file .env.production -f compose.prod.yaml exec backend python manage.py createsuperuser
```

El formulario web de creación inicial queda deshabilitado en producción porque `DJANGO_DEBUG=false`.

## 4. HTTPS y dominio

Configurar el proveedor para:

1. asociar el dominio elegido;
2. emitir y renovar automáticamente el certificado TLS;
3. enviar `X-Forwarded-Proto: https` al contenedor;
4. redirigir HTTP a HTTPS.

No activar `DJANGO_SECURE_HSTS_PRELOAD=true` hasta verificar el dominio y todos sus subdominios. HSTS queda configurado por un año, pero sin incluir subdominios ni solicitar precarga inicialmente.

## 5. Datos existentes

La base local actual es SQLite. La configuración productiva crea PostgreSQL vacío. Antes de publicar hay que elegir una opción:

- comenzar sin cargas y crear un administrador nuevo; o
- exportar los usuarios, catálogos, configuración y cargas de SQLite e importarlos en PostgreSQL.

No copiar `db.sqlite3` dentro de la imagen de producción.

## 6. Copias de seguridad

Configurar una copia diaria del volumen `postgres_data`, con retención y una restauración de prueba. Si el proveedor ofrece PostgreSQL administrado, activar sus backups automáticos y recuperación a un punto en el tiempo.

El volumen `media_data` queda preparado para archivos persistentes, aunque las planillas actualmente se procesan en memoria y no se conservan.

## 7. Correo

La recuperación de contraseña requiere SMTP real. Después de configurar `EMAIL_*`, probar con una cuenta no crítica y confirmar que el enlace utiliza el dominio HTTPS correcto.

## 8. Actualizaciones

Para desplegar una versión nueva:

```powershell
git pull
docker compose --env-file .env.production -f compose.prod.yaml up -d --build
```

Antes de actualizar, crear un backup de PostgreSQL. Revisar los logs y `/api/health/` al finalizar.
