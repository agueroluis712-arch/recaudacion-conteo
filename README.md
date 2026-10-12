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

Esta versión es apta para evaluación local. Antes de una puesta en producción institucional aún se deben activar autenticación por roles, HTTPS, PostgreSQL administrado, backups y configuración de red.

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
