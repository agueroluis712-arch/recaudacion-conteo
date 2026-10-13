# Recaudación

Aplicación independiente para cargar, consolidar y publicar de forma progresiva información de recaudación tributaria.

## Estado

Existe una primera versión funcional local que incluye:

- backend Django + Django REST Framework;
- frontend React + TypeScript + Vite;
- PostgreSQL para el entorno local con contenedores;
- catálogo inicial de 15 conceptos y canales de cobro;
- carga de la plantilla `.xlsx` o pegado directo desde Excel;
- validación de códigos, importes y duplicados exactos;
- cálculo de recaudación bruta, comisión, IVA y recaudación neta;
- historial de cargas y pantalla pública de recaudación bruta;
- publicación progresiva luego de una demora configurable por carga.

La interfaz se encuentra en `http://localhost:5173`; la pantalla para el Smart TV se abre desde el botón **Abrir pantalla pública**.

## Usuarios y acceso

El panel interno requiere autenticación. La pantalla pública permanece disponible sin iniciar sesión.

En una instalación local nueva, al abrir el panel por primera vez se muestra el formulario **Crear Administrador inicial**. Esta inicialización desde el navegador solo está habilitada con `DJANGO_DEBUG=true` y deja de estar disponible después de crear el primer usuario.

Roles incluidos:

- `OPERADOR`: consulta el panel y registra cargas.
- `SUPERVISOR`: incorpora las facultades del operador, administra la progresión y queda preparado para aprobar, anular o reemplazar cargas.
- `ADMINISTRADOR`: administra usuarios, roles, catálogos y toda la configuración.

Los permisos se controlan en la API. Ocultar un botón en el frontend no concede ni revoca acceso.

### Recuperación de contraseña

Cada usuario debe tener un correo único. Desde el ingreso puede solicitar un enlace de recuperación de un solo uso, válido durante una hora. En desarrollo, Django imprime el mensaje y el enlace en la consola del backend.

Para enviar correos reales, configurar en `.env` `APP_PUBLIC_URL`, `EMAIL_BACKEND`, `DEFAULT_FROM_EMAIL`, `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` y `EMAIL_USE_TLS` con las credenciales SMTP del proveedor elegido. Las credenciales nunca deben incorporarse al repositorio.

El diseño completo está en [docs/diseno-funcional-tecnico.md](docs/diseno-funcional-tecnico.md).

## Inicio local con contenedores

1. Copiar `.env.example` como `.env` y cambiar las claves.
2. Ejecutar `docker compose up --build`.
3. Backend: `http://localhost:8000/api/health/`.
4. Frontend: `http://localhost:5173`.

Docker todavía debe instalarse en el equipo antes de usar este flujo.

## Inicio local sin Docker

En dos terminales, desde la raíz del proyecto:

```powershell
.\.venv\Scripts\python.exe backend\manage.py runserver 127.0.0.1:8000
```

```powershell
Set-Location frontend
pnpm dev --host 127.0.0.1
```

Esta versión es apta para evaluación local. La configuración productiva está documentada en [docs/despliegue-produccion.md](docs/despliegue-produccion.md) e incluye React compilado con Nginx, Django con Gunicorn y PostgreSQL.

## Ejecución productiva con contenedores

1. Copiar `.env.production.example` como `.env.production` y reemplazar los valores de ejemplo.
2. Configurar el dominio, HTTPS, PostgreSQL persistente y SMTP según la [guía de despliegue](docs/despliegue-produccion.md).
3. Ejecutar:

```powershell
docker compose --env-file .env.production -f compose.prod.yaml up -d --build
```

La configuración local de `compose.yaml` continúa separada y no fue modificada.

## Verificación sin Docker

El backend usa SQLite cuando `DB_ENGINE` no es `postgresql`:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
$env:DB_ENGINE = "sqlite"
Push-Location backend
python manage.py migrate
python manage.py test apps.common
Pop-Location
```

Para el frontend:

```powershell
cd frontend
pnpm install
pnpm build
```

## Plantilla de carga

La plantilla aprobada está en `templates/plantilla-carga-recaudacion.xlsx`.
