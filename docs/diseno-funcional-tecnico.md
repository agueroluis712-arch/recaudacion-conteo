# Sistema de consolidación de recaudación

## Diseño funcional y técnico — etapa 1

Estado: diseño funcional aprobado y propuesta técnica preparada para implementación. La infraestructura institucional definitiva queda expresamente reservada para una etapa posterior.

## 1. Resumen ejecutivo

Se recomienda iniciar con un **monolito modular**: una única aplicación desplegable, con módulos internos y dependencias bien delimitadas. Para el volumen y el dominio descriptos, una arquitectura de microservicios agregaría fallas distribuidas, despliegues y observabilidad sin aportar todavía una ventaja proporcional. Los módulos podrán extraerse en el futuro porque se comunicarán mediante servicios de aplicación y eventos internos, no mediante acceso cruzado a tablas.

Principios no negociables:

1. La recaudación real es inmutable luego de aprobarse. Una corrección se representa mediante anulación o reemplazo, nunca por sobrescritura.
2. La progresión visible se calcula; no se contabiliza ni altera datos reales.
3. Cada carga conserva archivo, hash, reglas aplicadas, configuración de progresión, versión del algoritmo, usuario y marcas de tiempo.
4. Todas las operaciones administrativas se autorizan en backend y generan auditoría.
5. El dinero se procesa con `Decimal` y se persiste como `NUMERIC`, con una escala definida explícitamente.
6. Las fechas/hora se persisten en UTC y se muestran usando `America/Argentina/Buenos_Aires`, salvo configuración posterior.
7. La pantalla pública del salón y el panel interno son superficies separadas: la primera recibe únicamente datos agregados expresamente autorizados; la segunda requiere autenticación y permisos.

## 2. Alcance de esta etapa

Incluye:

- arquitectura propuesta;
- stack tecnológico recomendado;
- modelo relacional lógico completo;
- claves, restricciones e índices;
- flujo de importación, aprobación, anulación y reemplazo;
- especificación de los cuatro métodos de progresión;
- riesgos, decisiones confirmadas y mejoras;
- plan de implementación por etapas.

No incluye todavía código de producción, migraciones definitivas, pantallas ni decisiones funcionales que requieren aprobación.

## 3. Arquitectura propuesta

### 3.1 Vista general

```text
Smart TV / navegador público        Usuarios internos
        │ HTTPS                         │ HTTPS + sesión
        ▼                               ▼
Pantalla pública de solo lectura    Panel interno React/TypeScript
        │ API pública agregada           │ API interna autorizada
        └───────────────┬────────────────┘
                        ▼
Backend Django + Django REST Framework
  ├── Identidad y autorización
  ├── Catálogos
  ├── Importaciones y validaciones
  ├── Cargas y versionado
  ├── Progresión
  ├── Consultas de dashboard
  ├── Configuración
  └── Auditoría
       │                 │
       ▼                 ▼
 PostgreSQL        Almacenamiento de objetos
                    (archivos originales)
```

Redis y un worker de tareas se incorporan únicamente cuando el tamaño de archivos o las mediciones reales justifiquen validación asíncrona. No son necesarios para calcular la progresión ni para refrescar el dashboard.

### 3.2 Módulos y responsabilidades

| Módulo | Responsabilidad | No debe hacer |
|---|---|---|
| Identidad | Usuarios, autenticación, roles, permisos y sesiones | Decidir reglas contables |
| Catálogos | Canales, cuentas, conceptos, grupos y alias de importación | Modificar códigos ya utilizados |
| Importaciones | Guardar archivo, parsear, normalizar, previsualizar y validar | Aprobar silenciosamente |
| Cargas | Ciclo de vida, detalle, aprobación, anulación y reemplazo | Borrar físicamente historia |
| Progresión | Calcular fracción y monto visible en un instante | Escribir importes visibles periódicos |
| Pantalla pública | Mostrar en el Smart TV la recaudación visible autorizada, en modo de solo lectura | Exponer valores reales, usuarios, archivos, cuentas o acciones internas |
| Dashboard interno | Consultas agregadas, filtros y DTO de administración | Contener lógica contable o de progresión |
| Configuración | Valores generales y defaults versionados | Cambiar retroactivamente cargas existentes |
| Auditoría | Registro append-only de acciones y resultados | Ser editable desde la aplicación |

### 3.3 Capas internas

- **Dominio:** entidades, invariantes, estados y algoritmos puros.
- **Aplicación:** casos de uso y límites transaccionales.
- **Infraestructura:** ORM, PostgreSQL, almacenamiento de archivos, correo/logs y tareas.
- **API:** serialización, autenticación, autorización y contratos HTTP.
- **Frontend:** interacción y visualización; consume resultados, no recalcula reglas críticas.

Las transiciones sensibles (`APROBAR`, `ANULAR`, `REEMPLAZAR`) deben ejecutarse en una transacción de base de datos y bloquear la carga afectada para evitar carreras.

## 4. Stack tecnológico recomendado

| Área | Recomendación | Motivo |
|---|---|---|
| Backend | Python, Django y Django REST Framework | `Decimal`, ORM maduro, migraciones, seguridad, administración y permisos probados |
| Frontend | React + TypeScript + Vite | UI tipada, ecosistema de tablas y gráficos, separación clara de API |
| Base | PostgreSQL | Transacciones, `NUMERIC`, `JSONB`, índices parciales y restricciones robustas |
| Archivos | API compatible con S3; MinIO local y S3/servicio equivalente en producción | Conservación, hash, versionado y políticas de retención |
| Procesamiento | `openpyxl` para XLSX y parser estricto para CSV | Lectura controlada sin depender de Excel instalado |
| Tareas | Ejecución síncrona inicialmente; Celery + Redis si las pruebas de carga lo exigen | Evita infraestructura prematura |
| Autenticación | Sesión segura y cookies `HttpOnly` para despliegue mismo origen; OIDC si existe identidad institucional | Menor exposición de tokens en navegador |
| Observabilidad | Logs JSON, métricas y trazas con identificador de correlación | Diagnóstico y trazabilidad operativa |
| Empaquetado | Contenedores y despliegues reproducibles | Paridad entre ambientes y recuperación simple |

Las versiones concretas se fijarán a versiones estables soportadas al iniciar la implementación. Si la organización ya posee proveedor de identidad, almacenamiento, monitoreo o plataforma de despliegue, esas decisiones prevalecen y deben confirmarse antes de construir autenticación o infraestructura.

Para la primera etapa se aprueba un despliegue local, empaquetado en contenedores, con PostgreSQL, almacenamiento protegido en el equipo/servidor local y usuarios administrados por la aplicación. Debe funcionar sin depender de servicios externos. Base, archivos, secretos y configuración se mantienen separados del código para permitir una migración posterior a infraestructura institucional. El dominio, SSO, almacenamiento definitivo y política corporativa de backup se retomarán después de validar funcionalmente el sistema.

## 5. Convenciones de datos

- Identificadores: `UUID` para entidades de negocio expuestas por API; claves pequeñas internas pueden usar `BIGINT` si no salen del sistema.
- Dinero: `NUMERIC(20,2)`. Los importes aceptados y mostrados tienen exactamente dos decimales; no se usan `float`.
- Fechas de negocio: `DATE`.
- Instantes: `TIMESTAMPTZ`, almacenados en UTC.
- Códigos: mayúsculas, estables y únicos.
- Baja lógica: `activo`, `desactivado_en`, `desactivado_por` para catálogos; estados de dominio para cargas.
- Auditoría técnica: `creado_en`, `creado_por`, `modificado_en`, `modificado_por` donde corresponda.
- JSON: solo para parámetros variables, snapshots y evidencia; nunca sustituye relaciones centrales.

## 6. Modelo relacional propuesto

### 6.1 Identidad y permisos

#### `usuarios`

| Campo | Tipo | Reglas |
|---|---|---|
| `id` | UUID | PK |
| `username` | VARCHAR(150) | único, no nulo |
| `email` | VARCHAR(254) | único normalizado, no nulo |
| `password_hash` | VARCHAR | nulo si autenticación exclusivamente OIDC |
| `nombre`, `apellido` | VARCHAR | no nulos |
| `activo` | BOOLEAN | default verdadero |
| `ultimo_acceso_en` | TIMESTAMPTZ | nulo |
| `creado_en`, `modificado_en` | TIMESTAMPTZ | no nulos |

Índices: únicos sobre `lower(username)` y `lower(email)`; índice parcial sobre usuarios activos.

#### `roles`

`id` UUID PK, `codigo` VARCHAR único e inmutable, `nombre`, `descripcion`, `es_sistema`, `activo`, marcas de auditoría.

Semillas iniciales: `ADMINISTRADOR`, `SUPERVISOR`, `OPERADOR`.

#### `permisos`

`id` UUID PK, `codigo` VARCHAR único, `recurso`, `accion`, `descripcion`.

Ejemplos: `carga.crear`, `carga.aprobar`, `carga.anular`, `carga.reemplazar`, `auditoria.ver`, `configuracion.editar`, `usuario.administrar`.

#### `usuario_roles`

`usuario_id` FK, `rol_id` FK, `asignado_en`, `asignado_por` FK. PK compuesta (`usuario_id`, `rol_id`).

#### `rol_permisos`

`rol_id` FK, `permiso_id` FK, `asignado_en`, `asignado_por` FK. PK compuesta (`rol_id`, `permiso_id`).

No se recomienda codificar permisos por nombre de rol: el backend debe verificar permisos granulares.

### 6.2 Catálogos

#### `grupos_conceptos`

`id` UUID PK, `codigo` VARCHAR único e inmutable, `nombre`, `orden_visualizacion`, `activo`, `descripcion`, marcas de auditoría.

Grupos iniciales confirmados:

- `INMOBILIARIO`: concepto `INM`;
- `AUTOMOTOR`: concepto `AUT`;
- `INGRESOS_BRUTOS`: todos los códigos `IIBB_*`;
- `SELLOS`: conceptos `SEL`, `AG_SEL` y `TRS` (Tasa Retributiva);
- `OTROS`: concepto `OTROS`.

Los grupos pueden administrarse posteriormente con auditoría, sin modificar los códigos de concepto ni alterar la clasificación histórica ya consolidada en reportes cerrados.

#### `conceptos`

| Campo | Tipo | Reglas |
|---|---|---|
| `id` | UUID | PK |
| `codigo` | VARCHAR(40) | único, no nulo, inmutable tras su primer uso |
| `nombre` | VARCHAR(150) | no nulo |
| `grupo_id` | UUID | FK a `grupos_conceptos` |
| `orden_visualizacion` | INTEGER | no nulo, mayor o igual a cero |
| `activo` | BOOLEAN | no nulo |
| `descripcion` | TEXT | nulo |
| auditoría técnica | varios | no nulos según corresponda |

Índices: (`grupo_id`, `activo`, `orden_visualizacion`); único opcional (`grupo_id`, `orden_visualizacion`) si el negocio exige posiciones sin empate.

Semillas iniciales. Se usan saltos de diez en el orden para poder insertar nuevos conceptos sin renumerar todo el catálogo:

| Orden | Código | Nombre canónico |
|---:|---|---|
| 10 | `INM` | INMOBILIARIO |
| 20 | `AUT` | AUTOMOTOR |
| 30 | `IIBB_LOC` | II.BB (Local) |
| 40 | `IIBB_RS` | II.BB. (Reg. Simplificado) |
| 50 | `IIBB_RET` | II.BB. (Retención) |
| 60 | `IIBB_PER` | II.BB. (Percepción) |
| 70 | `IIBB_RET_CM` | II.BB. (RET. C.M.) |
| 80 | `IIBB_PER_CM` | II.BB. (PERCEP. C.M.) |
| 90 | `IIBB_CM` | II.BB. (Conv. Multil.) |
| 100 | `IIBB_ARB` | II.BB. (Ag.Rec.B.) |
| 110 | `IIBB_SIRCREB` | II.BB. (Sircreb) |
| 120 | `SEL` | SELLOS |
| 130 | `AG_SEL` | AG. DE SELLOS |
| 140 | `TRS` | TASA RETRIBUTIVA |
| 150 | `OTROS` | Otros |

Un administrador puede agregar conceptos indicando código único, nombre, grupo y orden. El código queda inmutable después del primer uso; el nombre, grupo, orden y estado activo pueden cambiar con auditoría. Cambiar el orden no modifica cargas históricas. Un concepto utilizado no se elimina físicamente: se desactiva.

#### `concepto_aliases`

Permite reconocer encabezados o valores diferentes por canal sin cambiar códigos internos: `id` UUID PK, `concepto_id` FK, `canal_id` FK nulo para alias global, `alias_original`, `alias_normalizado`, `activo`. Restricción única (`canal_id`, `alias_normalizado`).

Para comparar nombres se recortan espacios al principio y al final, se reducen espacios internos consecutivos a uno y se ignoran mayúsculas/minúsculas. Por ejemplo, `  inmobiliario `, `INMOBILIARIO` e `Inmobiliario` identifican el mismo concepto. No se aplican coincidencias difusas automáticas: variantes de puntuación, abreviaturas o nombres especiales deben estar registradas como alias para evitar confundir conceptos similares de Ingresos Brutos. Un alias desconocido genera una observación y requiere selección humana; un usuario autorizado puede guardar esa equivalencia para futuras cargas.

#### `cuentas_bancarias`

`id` UUID PK, `codigo` único, `banco`, `nombre`, `moneda`, `cbu_cifrado` o referencia segura, `cbu_ultimos4`, `activo`, marcas de auditoría. No se deben exponer números completos al frontend salvo permiso y necesidad explícitos.

#### `canales_cobro`

`id` UUID PK, `codigo` único e inmutable, `nombre`, `activo`, `modalidad_cuenta` (`OBLIGATORIA`, `OPCIONAL`, `NO_APLICA`), `cuenta_bancaria_default_id` FK nula, `configuracion_progresion_default_id` FK nula, `parametros` JSONB validado contra esquema, marcas de auditoría.

Semillas sugeridas: `PAGO_FACIL`, `RAPIPAGO`, `COBRO_EXPRESS`, `FISERV`, `QR_EMVCO`, `BOTON_PAGO`. Los códigos definitivos deben aprobarse.

#### `canal_cuentas`

Si un canal admite más de una cuenta: `canal_id` FK, `cuenta_bancaria_id` FK, `desde`, `hasta`, `es_default`. PK compuesta (`canal_id`, `cuenta_bancaria_id`, `desde`). Una restricción/índice parcial asegura un único default vigente por canal. Al cargar, se completa el default; el operador solo puede elegir cuentas vigentes asociadas al canal. Usar una cuenta no asociada requiere supervisor o administrador y motivo auditado. La cuenta guardada en una carga es histórica y no cambia cuando se modifica el default.

### 6.3 Configuración

#### `configuraciones_progresion`

Plantillas reutilizables: `id` UUID PK, `nombre`, `metodo`, `frecuencia_minutos`, `porcentaje_variacion`, `intensidad_aleatoriedad`, `intervalos_suavizado_final`, `parametros` JSONB, `version`, `activo`, marcas de auditoría.

Valores iniciales aprobados: método `LINEAL_ALEATORIO_CONTROLADO`, frecuencia 5 minutos, variación máxima ±20 %, intensidad aleatoria 70 % y suavizado durante los últimos 5 intervalos. La pantalla pública anima cada nuevo valor durante 5 segundos. Para `ACELERADO_AL_FINAL`, el valor inicial de `gamma` es 2. Todos estos valores son configurables y se copian al snapshot de cada carga.

Restricciones:

- método en `LINEAL`, `LINEAL_ALEATORIO_CONTROLADO`, `ACELERADO_AL_FINAL`, `INMEDIATO`;
- frecuencia mayor que cero salvo `INMEDIATO`;
- variación entre 0 y un máximo operativo aprobado;
- intensidad entre 0 y 1;
- suavizado mayor o igual a cero;
- (`nombre`, `version`) único.

Editar una plantilla crea una versión nueva. Las cargas guardan un snapshot y nunca dependen del valor mutable de esta tabla para reconstruir el pasado.

#### `configuraciones_sistema`

`id` UUID PK, `clave`, `valor` JSONB, `tipo`, `version`, `vigente_desde`, `vigente_hasta`, `creado_por`, `creado_en`. Único parcial sobre `clave` donde `vigente_hasta IS NULL`.

Claves iniciales: zona horaria, moneda, criterio temporal, hora de cierre, `demora_publicacion_minutos` (inicialmente 30), refresco de dashboard, visibilidad real/visible, `contador_solo_recaudacion_bruta` y gráficos habilitados. Cada clave debe tener esquema de validación propio.

#### `pantallas_publicas`

Configuración administrable del modo salón: `id` UUID PK, `codigo` único, `nombre`, `activo`, `token_acceso_hash` nulo si el acceso se limita por red, `frecuencia_refresco_segundos`, `mostrar_total`, `mostrar_desglose_conceptos`, `mostrar_desglose_canales`, `tema` JSONB validado, `filtros_publicacion` JSONB validado, `ultimo_acceso_en` y marcas de auditoría. Esta tabla no almacena importes; solo define qué vista agregada puede consumir cada pantalla.

### 6.4 Importación y cargas

#### `cargas`

| Campo | Tipo | Reglas |
|---|---|---|
| `id` | UUID | PK |
| `numero` | BIGINT | único, legible para soporte |
| `canal_id` | UUID | FK, no nulo |
| `cuenta_bancaria_id` | UUID | FK, nulo según canal |
| `fecha_recaudacion` | DATE | no nulo |
| `fecha_transferencia_tgp` | DATE | no nulo |
| `origen_carga` | VARCHAR | `ARCHIVO_EXCEL` o `PEGADO_EXCEL` |
| `estado` | VARCHAR | enum de dominio |
| `version` | INTEGER | >= 1 |
| `lineage_id` | UUID | identifica todas las versiones del mismo hecho |
| `reemplaza_a_id` | UUID | FK a `cargas`, nulo, único |
| `fecha_hora_carga` | TIMESTAMPTZ | generada por servidor, no nula |
| `creado_por` | UUID | FK a `usuarios`, no nulo |
| `aprobado_en`, `aprobado_por` | varios | nulos hasta aprobación |
| `anulado_en`, `anulado_por`, `motivo_anulacion` | varios | nulos hasta anulación |
| `observaciones` | TEXT | nulo |
| `revision` | INTEGER | control optimista de concurrencia |
| `creado_en`, `modificado_en` | TIMESTAMPTZ | no nulos |

Estados y transiciones propuestas:

```text
BORRADOR → VALIDANDO → APROBADA
                    ↘ OBSERVADA → VALIDANDO
BORRADOR/OBSERVADA → ANULADA
APROBADA → ANULADA
APROBADA → REEMPLAZADA, únicamente dentro de la transacción que aprueba su reemplazo
```

`REEMPLAZADA` y `ANULADA` son estados terminales y no pueden volver a estar vigentes. El creador puede cancelar una carga `BORRADOR` u `OBSERVADA`. Anular una carga `APROBADA`, publicada o no, requiere supervisor o administrador. Si ya llegó la fecha de transferencia a TGP, la operación queda reservada al administrador y exige motivo. Ninguna anulación elimina físicamente la carga ni sus archivos.

Cuando se anula una carga ya publicada, su aporte se retira del contador aplicando la regla excepcional de corrección negativa y mostrando temporalmente `Monto actualizado por corrección`. La acción completa queda auditada.

Índices:

- (`fecha_recaudacion`, `estado`);
- (`fecha_transferencia_tgp`, `estado`);
- (`canal_id`, `fecha_recaudacion`);
- (`cuenta_bancaria_id`, `fecha_transferencia_tgp`);
- (`creado_por`, `fecha_hora_carga` DESC);
- (`lineage_id`, `version`), único;
- índice parcial de cargas vigentes donde `estado = 'APROBADA'`.

#### `archivos_carga`

`id` UUID PK, `carga_id` FK, `tipo` (`ORIGINAL`, `PEGADO_ORIGINAL`, `NORMALIZADO`, `REPORTE_ERRORES`), `nombre_original`, `content_type_detectado`, `extension`, `tamano_bytes`, `sha256`, `storage_key`, `version_storage`, `creado_en`, `creado_por`.

Restricciones: único (`carga_id`, `tipo`) para `ORIGINAL`; `sha256` con formato hexadecimal válido; tamaño positivo. Índice en `sha256` para advertir duplicados. No se propone unicidad global del hash: un mismo archivo puede requerir investigación, reintento o reemplazo y no debe ser descartado sin contexto.

#### `carga_detalles`

| Campo | Tipo | Reglas |
|---|---|---|
| `id` | UUID | PK |
| `carga_id` | UUID | FK, no nulo |
| `concepto_id` | UUID | FK, no nulo |
| `cantidad_comprobantes` | BIGINT | entero >= 0 |
| `recaudacion_bruta` | NUMERIC(20,2) | >= 0 |
| `comision` | NUMERIC(20,2) | >= 0 |
| `iva_comision` | NUMERIC(20,2) | >= 0 |
| `otros_gastos` | NUMERIC(20,2) | >= 0 |
| `recaudacion_neta` | NUMERIC(20,2) | >= 0 |
| `fila_origen` | INTEGER | trazabilidad al archivo, nulo si agregado |
| `datos_origen` | JSONB | snapshot opcional de valores normalizados |

Único (`carga_id`, `concepto_id`) si cada concepto debe quedar consolidado en una sola fila. Si una planilla contiene varias filas del mismo concepto, el importador las agrega conservando el detalle de origen en staging.

Regla funcional confirmada:

`recaudacion_neta = recaudacion_bruta - comision - iva_comision`

`otros_gastos` se conserva como dato informativo y auditable, pero no interviene en el cálculo de la recaudación neta. La igualdad debe validarse durante la importación y aplicarse como restricción de consistencia en los datos aprobados. Las cargas normales no admiten importes negativos. Los errores se corrigen mediante reemplazo o anulación; una futura necesidad de devoluciones reales se modelará como un tipo de movimiento específico y diferenciado.

#### `carga_totales`

Opcional pero recomendado como snapshot de control: `carga_id` PK/FK, cantidades e importes totales, `calculado_en`. Se genera desde detalles dentro de la misma transacción; nunca se acepta como fuente independiente. Puede evitar agregaciones repetidas y deja evidencia del total aprobado.

#### `carga_progresiones`

Snapshot inmutable uno a uno:

| Campo | Tipo | Reglas |
|---|---|---|
| `carga_id` | UUID | PK y FK |
| `demora_publicacion_minutos` | INTEGER | snapshot del valor configurado, inicialmente 30 |
| `fecha_hora_inicio` | TIMESTAMPTZ | `fecha_hora_carga + demora_publicacion_minutos` |
| `fecha_hora_cierre` | TIMESTAMPTZ | posterior al inicio, salvo método inmediato |
| `frecuencia_minutos` | INTEGER | > 0 salvo inmediato |
| `metodo` | VARCHAR | enum |
| `porcentaje_variacion` | NUMERIC(6,5) | por ejemplo 0.20000 |
| `intensidad_aleatoriedad` | NUMERIC(6,5) | 0..1 |
| `intervalos_suavizado_final` | INTEGER | >= 0 |
| `seed_cifrada` o `seed` | VARCHAR | no nula para método aleatorio |
| `algoritmo_version` | VARCHAR | no nulo |
| `parametros` | JSONB | validado, no nulo |
| `creado_en` | TIMESTAMPTZ | no nulo |

Índice (`fecha_hora_cierre`) parcial para cargas en curso. El snapshot no se modifica cuando cambia la configuración general o la de un canal.

#### `carga_validaciones`

`id` UUID PK, `carga_id` FK, `ejecucion` INTEGER, `codigo`, `severidad` (`ERROR`, `ADVERTENCIA`, `INFO`), `fila`, `columna`, `mensaje`, `contexto` JSONB, `creado_en`. Índices (`carga_id`, `ejecucion`, `severidad`) y (`codigo`).

#### `carga_filas_staging`

Representa la vista previa antes de aprobar: `id` UUID PK, `carga_id` FK, `numero_fila`, `datos_originales` JSONB, `datos_normalizados` JSONB, `concepto_id` FK nulo, `es_valida`, `errores` JSONB. Único (`carga_id`, `numero_fila`). Puede purgarse según una política de retención aprobada después de conservar evidencia suficiente.

### 6.5 Auditoría

#### `auditoria_eventos`

| Campo | Tipo | Reglas |
|---|---|---|
| `id` | UUID/UUIDv7 | PK |
| `fecha_hora` | TIMESTAMPTZ | generada por servidor |
| `usuario_id` | UUID | FK nula para eventos de sistema |
| `accion` | VARCHAR | catálogo controlado |
| `entidad` | VARCHAR | no nulo |
| `registro_id` | VARCHAR | no nulo |
| `valor_anterior` | JSONB | nulo |
| `valor_nuevo` | JSONB | nulo |
| `ip_origen` | INET | nulo según contexto |
| `user_agent` | TEXT | nulo |
| `correlation_id` | UUID | no nulo |
| `resultado` | VARCHAR | `EXITO` o `FALLO` |
| `motivo` | TEXT | nulo |
| `metadata` | JSONB | no nulo, default `{}` |

Índices: (`entidad`, `registro_id`, `fecha_hora`), (`usuario_id`, `fecha_hora`), (`accion`, `fecha_hora`) y BRIN sobre `fecha_hora` cuando el volumen lo justifique. Los permisos de base para la cuenta de aplicación deben impedir `UPDATE` y `DELETE` sobre esta tabla.

Los secretos, hashes de contraseña, semillas sensibles, CBU completo y contenido binario no deben copiarse a `valor_anterior`/`valor_nuevo`.

## 7. Relaciones principales

- Un usuario posee muchos roles y un rol muchos permisos.
- Un grupo contiene muchos conceptos; un concepto pertenece a un grupo vigente a la vez.
- Un canal puede operar con varias cuentas y tiene una cuenta/default de progresión opcionales.
- Una carga pertenece a un canal, una cuenta y un usuario; contiene muchos detalles y archivos.
- Una carga tiene exactamente un snapshot de progresión antes de aprobarse.
- Una carga puede reemplazar a una sola carga; `lineage_id` agrupa toda la cadena y `version` la ordena.
- Un detalle referencia un concepto estable; desactivar el concepto no elimina historia.
- Las validaciones y filas de staging pertenecen a una ejecución de importación de la carga.
- Auditoría referencia entidades de forma lógica para conservar eventos aun si un catálogo se desactiva.

## 8. Flujo de importación

### 8.1 Plantilla Excel propuesta

La aplicación acepta inicialmente archivos `.xlsx`. Los datos de cabecera se seleccionan en el formulario de carga y no se repiten en cada fila de Excel:

- canal de cobro;
- fecha de recaudación;
- fecha de transferencia a TGP;
- cuenta bancaria, cuando corresponda;
- fecha y hora de cierre.

La hoja importable se denomina `Detalle` y contiene una fila por concepto. Columnas recomendadas:

| Columna | Obligatoria | Tipo y regla | Observación |
|---|---|---|---|
| `CODIGO_CONCEPTO` | Sí | texto del catálogo | Clave estable: `INM`, `AUT`, `IIBB_LOC`, etc. |
| `CONCEPTO` | Sí | texto | Nombre visible para facilitar la revisión; debe corresponder al código |
| `CANTIDAD_COMPROBANTES` | Sí | entero >= 0 | Se muestra solo en el panel interno |
| `RECAUDACION_BRUTA` | Sí | decimal >= 0, dos decimales | Importe que alimenta la progresión pública |
| `COMISION` | Sí | decimal >= 0, dos decimales | Valor real, sin progresión |
| `IVA_COMISION` | Sí | decimal >= 0, dos decimales | Valor real, sin progresión |
| `OTROS_GASTOS` | Sí | decimal >= 0, dos decimales | Informativo; no se descuenta del neto |
| `OBSERVACIONES` | No | texto breve | Aclaración de la fila, sin fórmulas ni datos sensibles |

`RECAUDACION_NETA` no se ingresa como dato editable. La calcula la aplicación con la regla confirmada `RECAUDACION_BRUTA - COMISION - IVA_COMISION`. La vista previa muestra el neto calculado y los totales antes de aceptar la carga.

La plantilla inicial contiene los 15 conceptos en el orden canónico, incluso cuando no tengan movimientos. Los nuevos conceptos activos se incorporan a las plantillas posteriores según `orden_visualizacion`. Cuando un concepto no tiene movimientos se carga cero en cantidad e importes. El importador no depende del orden de las filas: prioriza `CODIGO_CONCEPTO` y rechaza códigos duplicados o desconocidos.

Puede incluirse una fila de totales visual fuera de la tabla importable, pero el sistema siempre recalcula los totales desde el detalle. No se importan fórmulas, celdas combinadas, macros, filas subtotales ni columnas auxiliares.

Validaciones recomendadas en la plantilla:

- lista protegida de códigos y nombres de concepto;
- cantidad como entero no negativo;
- importes numéricos no negativos con exactamente dos decimales;
- una sola fila por código;
- encabezados fijos;
- celdas editables diferenciadas visualmente de códigos y fórmulas protegidas.

### 8.2 Copiar y pegar desde Excel

Además de subir el archivo `.xlsx`, el panel interno ofrece `Pegar desde Excel`. El navegador recibe el bloque copiado como filas separadas por saltos de línea y columnas separadas por tabulaciones, y lo coloca en una grilla de vista previa.

El formulario solicita como mínimo:

- canal de cobro;
- fecha de recaudación;
- fecha de ingreso/transferencia a TGP.

La cuenta bancaria se completa desde el default del canal y se solicita solamente cuando el canal lo requiere o el usuario autorizado necesita cambiarla. La hora de cierre se toma de la configuración aplicable y puede mostrarse para revisión.

La grilla precarga los conceptos activos en su orden canónico y usa las mismas columnas y reglas que la hoja `Detalle`. El usuario puede pegar valores sobre esas filas. Si el bloque incluye código, el sistema lo usa como clave; si incluye solo el nombre, aplica la normalización de espacios y mayúsculas/minúsculas y luego consulta los alias. El sistema:

1. detecta y descarta una fila de encabezados reconocida;
2. valida cantidad de columnas, códigos o nombres normalizados, duplicados, enteros y decimales;
3. mantiene visibles los 15 conceptos iniciales y todos los conceptos activos agregados; completa con cero únicamente cuando el usuario confirma que no tienen movimientos;
4. calcula neto y totales;
5. presenta errores y advertencias por celda;
6. exige una confirmación antes de crear la carga.

La fecha/hora de carga y el comienzo de la demora de publicación se fijan al presionar `Confirmar carga`, no al primer pegado. Esto evita consumir la ventana de revisión mientras el usuario todavía está editando la grilla.

Para conservar trazabilidad sin un archivo original, el backend guarda el texto tabulado pegado en su forma original como `PEGADO_ORIGINAL`, calcula su SHA-256 y genera además un snapshot canónico normalizado. Ambos quedan asociados a la carga, al usuario y al instante de confirmación. Las validaciones, reemplazos, auditoría y detección de duplicados son idénticos a los de un archivo subido.

1. El usuario selecciona canal y fechas, confirma la cuenta cuando corresponda y elige entre adjuntar el archivo o pegar datos desde Excel.
2. Al confirmar, el servidor crea la carga `BORRADOR`, toma `fecha_hora_carga`, calcula SHA-256 mientras guarda el archivo o bloque pegado original y captura metadatos.
3. Se valida extensión permitida, firma real/MIME, tamaño, cantidad de hojas/filas, archivos comprimidos y fórmulas no evaluadas.
4. La carga pasa a `VALIDANDO`; el adaptador del canal transforma filas a un formato canónico.
5. Se validan columnas, conceptos/alias, enteros, decimales, fechas, signos, fórmula de neto, totales y duplicados internos.
6. Se buscan cargas similares por hash y por clave de negocio. El hash igual genera como mínimo una advertencia y puede bloquear según política.
7. La vista previa presenta filas, agregados, errores y advertencias. Ningún error bloqueante permite aprobar.
8. El operador confirma la carga. Si no existen errores bloqueantes, en una transacción se crean detalles consolidados y totales, se fija el snapshot de progresión y se pasa a `APROBADA`. No requiere una segunda aprobación para el flujo normal.
9. Se emite auditoría con resultado, configuración aplicada y correlación.

Adaptadores por canal permiten incorporar formatos nuevos sin condicionales dispersos. Cada adaptador declara versión, columnas, reglas de normalización y fórmula de control.

## 9. Detección de duplicados

Se establecen tres niveles:

- **Exacto:** mismo contenido canónico, canal y fecha de recaudación. Bloquea la creación de una nueva carga.
- **Archivo exacto:** mismo SHA-256 y tamaño. También bloquea, aunque cambie el nombre del archivo.
- **Clave de negocio similar:** mismo canal, fecha de recaudación, cuenta e importes totales, pero contenido o archivo diferente. Genera una advertencia de alta confianza.

Una advertencia por similitud puede exceptuarse únicamente con un permiso específico y un motivo obligatorio. La excepción queda auditada. Si el segundo contenido corrige al primero, debe utilizarse `Reemplazar carga`: se conserva la versión anterior y no se crea un duplicado independiente. Los reemplazos autorizados pueden reutilizar un archivo o contenido previamente detectado porque pertenecen a la misma cadena versionada.

## 10. Progresión visual

### 10.1 Modelo común

Para una carga válida y habilitada para publicación se define:

- `M`: recaudación bruta real de la carga, expresada en centavos;
- `d`: demora de publicación configurable, inicialmente 30 minutos, copiada al snapshot de la carga;
- `t0`: inicio de publicación, igual a `fecha_hora_carga + d`;
- `t1`: cierre;
- `f`: frecuencia en minutos;
- `K = ceil((t1 - t0) / f)`: cantidad total de intervalos;
- `i(t)`: intervalos completos transcurridos, limitado a `[0, K]`;
- `p(t)`: fracción visible, limitada a `[0, 1]`.

Antes de `t0`, `p=0`; desde `t1`, `p=1` exactamente para una carga sin correcciones. La publicación comienza al finalizar la demora configurada y no se posterga por el horario de aprobación. Para evitar publicar datos inválidos, el archivo debe haber superado las validaciones automáticas bloqueantes y no estar marcado como observado o anulado. La hora del servidor es la autoridad. El frontend recibe el resultado y el instante de cálculo, y no inventa el monto.

La progresión se aplica a la `recaudacion_bruta` de todos los conceptos de la carga, incluidos los conceptos con valor cero. Comisión, IVA, otros gastos y recaudación neta permanecen como valores reales y no se fraccionan visualmente.

Para preservar el redondeo, los cálculos finales se hacen en centavos con enteros. Si la distribución de la recaudación bruta entre intervalos produce una diferencia de centavos, esa diferencia se suma o resta en el último tramo, exactamente en la fecha/hora de corte. Esta compensación se limita al residuo técnico de redondeo y no puede utilizarse para trasladar al cierre un desvío material del algoritmo. Siempre deben cumplirse:

- visible >= 0;
- visible <= real;
- visible nunca decrece;
- al cierre visible = real;
- la suma reconciliada de detalles visibles = total visible.

### 10.2 Correcciones y reemplazos durante la progresión

Durante la demora de publicación —30 minutos inicialmente— puede cargarse una versión corregida sin que la versión errónea haya aparecido en el Smart TV. “Sobrescribir” significa reemplazo funcional: el archivo anterior se conserva para auditoría, se marca `REEMPLAZADA` y la nueva versión pasa por validación. Cada nueva versión toma un snapshot de la demora configurada al momento de su carga.

Si la corrección se aprueba después de que el monto ya comenzó a mostrarse:

- si el nuevo bruto corregido es mayor que el valor ya visible, se conserva el ritmo que traía la progresión y se detiene al alcanzar el nuevo monto. Una corrección hacia abajo puede, por lo tanto, completar la carga antes de la hora de cierre;
- si una corrección hacia arriba no pudiera alcanzar el nuevo monto manteniendo el ritmo antes del cierre, se recalculan y suavizan los incrementos restantes para llegar al monto correcto en el cierre;
- si el nuevo total real es menor que lo ya mostrado, resulta matemáticamente imposible llegar al valor correcto sin que el contador disminuya en algún momento.

En este último caso se confirma como regla aplicar la corrección negativa al confirmar el reemplazo y mostrar temporalmente la leyenda `Monto actualizado por corrección`. Esta es la única situación en la que el contador público puede disminuir. La auditoría interna registra ambos valores, usuario, motivo e instante. No se oculta la diferencia ni se compensa con cargas futuras.

La llegada anticipada al monto corregido es una excepción propia del reemplazo. Las cargas sin correcciones continúan llegando al 100 % en su hora de cierre configurada.

### 10.3 `LINEAL`

`p(t) = i(t) / K` para actualización por escalones según la frecuencia configurada. Cuando el Smart TV recibe un nuevo valor, anima suavemente la transición durante unos segundos y luego permanece estable hasta la siguiente actualización. La animación es exclusivamente visual: no interpola datos contables, no modifica la secuencia y nunca supera el nuevo valor confirmado por el backend.

Los incrementos intermedios se expresan con dos decimales. El residuo de centavos que resulte de dividir `M` entre `K` se netea en el último tramo; en el cierre el valor se fija exactamente en `M`.

### 10.4 `LINEAL_ALEATORIO_CONTROLADO`

El algoritmo recomendado construye una secuencia determinística de `K` pesos una vez de forma lógica, pero la reconstruye en memoria cuando se consulta. No persiste una fila por intervalo.

#### Parámetros

- `v`: porcentaje máximo de variación, inicialmente propuesto 0,20;
- `a`: intensidad, entre 0 y 1;
- `S`: cantidad de intervalos de suavizado final;
- `seed`: semilla propia de la carga;
- `algoritmo_version`: fija exactamente el generador y las reglas históricas.

#### Construcción

1. Se genera para cada intervalo un valor pseudoaleatorio determinístico `r_j` en `[-1, 1]`, usando un PRNG especificado por versión y la semilla de la carga. No se usa el generador por defecto del lenguaje sin fijar algoritmo.
2. La desviación candidata es `d_j = r_j × v × a`.
3. Durante los últimos `S` intervalos se reduce gradualmente el límite de desviación. Esto hace que los incrementos converjan hacia el incremento lineal y evita un salto visual al final.
4. Se proyecta el vector de desviaciones sobre la restricción `sum(d_j)=0`, respetando en cada intervalo sus límites. Puede resolverse buscando un desplazamiento `lambda` tal que `sum(clamp(d_j-lambda, limite_inferior_j, limite_superior_j))=0`.
5. El peso final es `w_j = 1 + d_j`. Como los pesos son positivos y suman exactamente `K`, la secuencia es monótona y el total teórico coincide exactamente con `M`.
6. `M × w_j / K` se convierte a centavos. Los primeros `K-1` incrementos se expresan con dos decimales y el residuo técnico de redondeo se suma o resta en el último incremento. Así, la suma de los `K` incrementos es exactamente `M`. La construcción balanceada de pesos evita que este ajuste incluya desvíos de progresión distintos del redondeo.
7. El visible en el instante `t` es la suma prefija de los primeros `i(t)` incrementos.

Este enfoque corrige el desvío a través de toda la secuencia y reduce su libertad en los últimos `S` intervalos; el último intervalo no absorbe una deuda arbitraria. Para que el suavizado sea material, se recomienda `S = min(configurado, K)` y advertir cuando `K` es demasiado pequeño.

#### Reproducibilidad

La identidad completa de una secuencia es:

`(carga_id, seed, algoritmo_version, M, t0, t1, frecuencia, variacion, intensidad, suavizado)`.

Cambiar una configuración global no cambia esa tupla. Una nueva carga obtiene otra semilla criptográficamente segura. Para evitar que un operador elija semillas buscando una curva favorable, la semilla debe generarse en backend; puede almacenarse cifrada o derivarse mediante HMAC de un secreto versionado y el UUID de carga.

#### Propiedades a probar

- misma entrada produce exactamente la misma serie;
- semilla diferente normalmente produce otra serie;
- cada incremento queda dentro del límite, salvo una tolerancia de una unidad mínima por redondeo;
- ninguna suma prefija decrece ni excede `M`;
- la suma final es `M`;
- el tramo final no contiene un incremento desproporcionado;
- funciona con `M=0`, `K=1`, `S=0`, `S>K` e importes menores que `K` centavos.

### 10.5 `ACELERADO_AL_FINAL`

Se propone una curva de potencia:

`p(t) = (i(t)/K)^gamma`, con `gamma > 1`.

`gamma` debe ser configurable dentro de límites aprobados; por ejemplo, 2 produce 25 % visible a mitad del tiempo. Debe guardarse en el snapshot. Al cierre se fuerza exactamente 1.

### 10.6 `INMEDIATO`

`p(t)=1` desde `t0`. No requiere intervalos ni tarea programada.

### 10.7 Progresión por concepto

Todos los detalles de una carga comparten la misma fracción o, preferentemente, la misma secuencia de intervalos de la carga. Solo se distribuye la recaudación bruta; los demás importes del detalle son reales. Para un instante:

1. se calcula la recaudación bruta visible total de la carga;
2. se calcula la recaudación bruta visible provisional de cada concepto con la misma fracción acumulada;
3. se reconcilian centavos por mayores restos y orden estable de concepto;
4. se garantiza que la suma de conceptos sea idéntica al total visible.

No se debe generar una secuencia aleatoria independiente por concepto: podría distorsionar la composición del bruto total y hacer más difícil explicar el dashboard.

La cantidad de comprobantes no progresa. Se muestra completa únicamente en el panel interno y no forma parte de la pantalla pública del Smart TV.

## 11. Consultas del dashboard

Existen dos superficies con contratos de API diferentes:

### 11.1 Pantalla pública del salón

Es una vista de solo lectura, optimizada para ejecutarse a pantalla completa en el navegador de un Smart TV. Su objetivo es comunicar al público y a los empleados cómo avanza la recaudación, con tipografía legible a distancia, alto contraste, actualización automática y recuperación automática ante cortes temporales de red.

La respuesta pública contiene solamente datos agregados permitidos, por ejemplo:

- recaudación bruta visible total;
- porcentaje de avance, si se decide publicarlo;
- desglose visible por concepto, si está habilitado;
- fecha/hora de última actualización;
- rótulos institucionales configurados.

El contador consulta periódicamente el valor calculado por el backend. Si cambió, anima la transición desde el valor anterior durante una duración corta configurable; si no cambió, permanece estable. Al recargar la página solicita nuevamente el valor del servidor y no intenta reconstruir la animación perdida.

Nunca contiene cantidad de comprobantes, recaudación real final antes del cierre, comisión, IVA, neto, cuentas bancarias, nombres de archivo, usuarios, historial de cargas, observaciones ni identificadores internos. No ofrece filtros libres ni operaciones de escritura. El frontend público no llama endpoints administrativos.

El contador principal puede configurarse para mostrar únicamente la recaudación bruta visible agregada. La progresión subyacente se calcula sobre la recaudación bruta de todos los conceptos aunque el desglose por concepto no se muestre en el televisor.

### 11.2 Panel interno

El backend construye una consulta base de cargas `APROBADA` vigentes. Por defecto excluye `ANULADA`, `REEMPLAZADA`, borradores y observadas. Los filtros se aplican antes de agregar.

El criterio temporal selecciona una columna de negocio:

- fecha de recaudación; o
- fecha de transferencia TGP.

La progresión, en cambio, siempre usa los instantes de carga/cierre y el instante actual. No debe confundirse el eje de filtro con el reloj de progresión.

Para mantener los 15 conceptos visibles, la consulta parte del catálogo de conceptos iniciales y hace `LEFT JOIN` con los agregados filtrados, reemplazando nulos por cero. Un concepto desactivado que posea historia debe seguir apareciendo al consultar ese período.

En los indicadores, `recaudación visible` significa **recaudación bruta visible** y `recaudación real` significa **recaudación bruta real**. La tabla por concepto debe calcular y mostrar `bruto real` y `bruto visible` para todos los conceptos; comisión, IVA, otros gastos y neto se muestran como valores reales. Por lo tanto, el campo originalmente solicitado como `neto visible` se reemplaza por `bruto visible`.

El panel interno contiene la configuración, la carga y validación de archivos, la administración de catálogos, usuarios y permisos, la auditoría y las consultas reales. También ofrece una vista previa exacta de lo que verá el Smart TV. Cuando `contador_solo_recaudacion_bruta` esté activa, el contador excluye comisión, IVA, otros gastos y neto, sin ocultar esos datos en las tablas o vistas internas de detalle. La opción cambia la presentación, nunca el cálculo ni los datos almacenados.

En volúmenes iniciales se calculan agregados en consulta. Si las mediciones muestran lentitud, se agregan vistas materializadas o tablas de lectura reconstruibles; nunca se sustituye la fuente real.

Objetivo inicial de capacidad: hasta 50 usuarios registrados, 10 usuarios simultáneos, 500 cargas diarias y archivos Excel de hasta 10 MB. El panel interno debe responder en menos de 2 segundos para consultas habituales y la actualización del Smart TV no debe presentar interrupciones perceptibles. Son objetivos de dimensionamiento y prueba, no límites rígidos del modelo.

## 12. Seguridad

- TLS obligatorio y cookies `Secure`, `HttpOnly`, `SameSite`.
- CSRF para autenticación por sesión.
- Contraseñas con el hasher robusto provisto por el framework y política institucional; preferencia por OIDC/MFA si está disponible.
- Autorización por permiso en cada caso de uso y filtrado de objetos para operadores.
- Límite de tamaño, timeout, cantidad de filas/columnas y descompresión; rechazo de macros y contenido ejecutable.
- Verificación por firma/contenido además de extensión.
- Archivos fuera del directorio servido públicamente, con nombres internos aleatorios y descarga autorizada.
- Fórmulas de planilla tratadas como datos no confiables; exportaciones protegen contra formula injection.
- Rate limiting en inicio de sesión y carga, con límites específicos por usuario/rol.
- Secretos únicamente en gestor de secretos o variables de ambiente; nunca en repositorio ni auditoría.
- Cabeceras de seguridad, CSP y sanitización contextual.
- Separación de cuentas de base para migración, aplicación, lectura/reportes y backup cuando la operación lo permita.
- Contrato y ruta separados para la pantalla pública; nunca reutiliza serializadores del panel interno.
- La pantalla pública se limita preferentemente a la red del organismo. Si debe ser accesible desde Internet, requiere token rotatorio o mecanismo equivalente, rate limiting, caché y revisión específica de exposición.
- Ante pérdida de conexión, el Smart TV puede conservar temporalmente el último valor con un aviso visible de “sin conexión” y la hora de la última actualización; no debe simular nuevos incrementos localmente.

## 13. Backup y recuperación

Se respaldan como una unidad lógica:

- PostgreSQL con recuperación a un punto en el tiempo;
- bucket de archivos con versionado y retención;
- configuración de infraestructura y despliegue;
- claves/secretos mediante el mecanismo seguro institucional;
- auditoría con retención acorde a normativa.

Para la instalación local se aprueba:

- backup de base de datos cada hora;
- backup completo diario de base, originales, contenido pegado y configuración;
- una copia adicional en otro disco o equipo;
- conservación de backups diarios durante 30 días;
- conservación de un backup mensual durante 12 meses;
- backup adicional antes de actualizar la aplicación;
- RPO objetivo de una hora y RTO objetivo de cuatro horas;
- conservación sin purga automática de cargas aprobadas, originales y auditoría hasta definir la política institucional.

Una copia no es un backup verificado hasta realizar restauraciones periódicas. La restauración debe comprobar la relación entre la base y las versiones de archivos, no solo que ambos soportes puedan leerse. La retención definitiva, cifrado, ubicación secundaria y responsables se revisarán con la normativa institucional.

## 14. Consistencia y concurrencia

- Estados implementados con transiciones explícitas, no con actualizaciones arbitrarias.
- Aprobación idempotente: repetir la misma solicitud no duplica detalles ni eventos de éxito.
- `revision` o ETag evita que dos usuarios confirmen sobre una vista previa distinta.
- Anulación/reemplazo bloquea la fila de carga y valida estado dentro de la transacción.
- Todos los totales se recalculan desde detalle usando `Decimal` y política de redondeo única.
- El archivo se considera durable antes de aprobar la carga.
- Una transacción fallida registra el fallo sin dejar una aprobación parcial.
- Cambios de nombre, grupo o estado de un concepto no alteran sus códigos ni detalles históricos.

## 15. Riesgos e inconsistencias detectadas

1. **Ajustes y valores negativos resueltos.** Las cargas normales no aceptan importes negativos. Los errores se corrigen por reemplazo o anulación. Las devoluciones reales no se mezclan con conceptos comunes y, si se incorporan, usarán un tipo de movimiento específico con permisos y presentación diferenciados.
2. **Entradas fuera de escala.** La escala fue confirmada en dos decimales y el residuo de la progresión se netea en el último tramo. Un valor de origen con más de dos decimales debe informarse como error de validación, no normalizarse silenciosamente.
3. **Momento de inicio resuelto.** La publicación comienza cuando vence la demora configurable tomada al cargar el archivo, inicialmente 30 minutos. No espera una aprobación posterior, pero exige no tener errores automáticos bloqueantes ni estado observado/anulado.
4. **Hora de cierre inválida resuelta.** Si la fecha/hora de cierre es igual o anterior al inicio de la progresión, la carga queda bloqueada y debe corregirse. El sistema no la convierte automáticamente en inmediata ni traslada el cierre.
5. **Zona horaria y horario de verano.** Buenos Aires no presenta cambios actualmente, pero deben usarse identificadores IANA y resolver instantes, no offsets fijos.
6. **Duplicado versus reemplazo resuelto.** El duplicado exacto se bloquea; una coincidencia de canal, fecha, cuenta y totales genera advertencia. Solo un usuario con permiso específico puede continuar indicando motivo. Las correcciones se registran como reemplazos versionados.
7. **Aprobación por el cargador resuelta.** El operador puede confirmar y aprobar una carga normal que supere todas las validaciones. Supervisor o administrador es obligatorio para reemplazar una carga publicada, anular, exceptuar un posible duplicado o resolver observaciones.
8. **Fechas TGP.** Falta definir si pueden ser anteriores a recaudación y cómo se manejan feriados/días hábiles.
9. **Conceptos sin movimiento resuelto.** Se muestran los 15 conceptos iniciales y los conceptos agregados que estén activos, respetando el orden del catálogo. Los conceptos históricos desactivados reaparecen cuando se consulta un período en el que tuvieron movimientos.
10. **Interpretación visual.** Se confirmó que progresa la recaudación bruta de todos los conceptos. La interfaz debe rotular siempre `bruto visible` y `bruto real` para impedir que el valor progresado se interprete como neto disponible o transferible. El contador principal puede configurarse para mostrar solo el bruto agregado.
11. **Comprobantes internos.** Se confirmó que no progresan y no se muestran en la pantalla pública. El panel interno debe identificarlos claramente como cantidad real.
12. **Archivos soportados.** Faltan formatos exactos, hojas, columnas, separadores, moneda, locales y layouts por canal.
13. **Cuenta por canal resuelta.** Cada canal define modalidad obligatoria, opcional o no aplicable, puede tener cuenta predeterminada y restringe al operador a cuentas asociadas. Una excepción requiere supervisor o administrador y queda auditada.
14. **Retención.** No están definidos plazos para originales, staging, logs, auditoría y datos personales.
15. **Visibilidad por rol resuelta.** El operador accede a la pantalla pública y a sus propias cargas, validaciones y estados. El supervisor accede a todas las cargas, canales, valores reales/visibles, observaciones y reemplazos. El administrador posee acceso completo, incluida configuración, usuarios, cuentas y auditoría. Los alcances adicionales por canal se conceden mediante permisos explícitos.
16. **Parámetros JSON.** Requieren esquema versionado; JSON libre haría imposible validar o migrar.
17. **Semilla y transparencia resuelta técnicamente.** La semilla es interna, no editable y no se publica en el Smart TV. El panel de auditoría muestra la versión del algoritmo y los parámetros funcionales necesarios para explicar y reproducir la secuencia.
18. **Anulación posterior a transferencia resuelta.** Se permite únicamente a un administrador, con motivo obligatorio, conservación íntegra del historial y auditoría. Si la carga estaba publicada, se aplica la corrección visible correspondiente.
19. **Exposición de la pantalla pública resuelta.** El Smart TV accede únicamente por red local. Muestra bruto visible, fecha de recaudación y última actualización. No publica bruto real final, porcentaje, comprobantes, comisión, IVA, neto, canales, cuentas ni usuarios. Los desgloses por grupo o concepto son configurables y comienzan desactivados. Ante desconexión conserva el último valor con aviso y hora.
20. **Corrección por debajo de lo ya publicado resuelta.** Una corrección puede terminar anticipadamente si su nuevo total todavía supera lo visible. Si el nuevo bruto real ya es inferior al bruto visible, se aplica inmediatamente el ajuste negativo al confirmar el reemplazo, con leyenda temporal y auditoría. Es la única excepción a la monotonía del contador público.

## 16. Mejoras propuestas

- Incorporar `concepto_aliases` y adaptadores versionados por canal.
- Separar staging de los detalles aprobados.
- Crear un número humano de carga además del UUID.
- Agregar segregación de funciones configurable.
- Guardar huella canónica de contenido además del hash binario.
- Versionar algoritmo de progresión y configuración aplicada.
- Exportar un reporte de validación firmado con hash y correlación.
- Definir contratos de integración futuros mediante API y eventos de dominio (`CargaAprobada`, `CargaAnulada`, `CargaReemplazada`) usando outbox transaccional cuando exista un consumidor real.
- Incluir pruebas basadas en propiedades para dinero y progresión, además de ejemplos.
- Diseñar accesibilidad, contraste y rotulado claro entre “real” y “visible” para evitar interpretación contable errónea.

## 17. Decisiones funcionales confirmadas

Las siguientes decisiones fueron revisadas y aprobadas:

1. **Resuelta:** `recaudacion_neta = recaudacion_bruta - comision - iva_comision`; `otros_gastos` no se descuenta. No se permiten importes negativos en cargas normales. Los errores se resuelven por reemplazo o anulación y las devoluciones reales requerirán un tipo de movimiento específico en una etapa posterior.
2. **Resuelta:** los importes tienen dos decimales y todo residuo de redondeo de la progresión se netea en el último tramo, en la fecha/hora de corte. Una entrada con más de dos decimales se rechaza durante la validación para evitar redondeos silenciosos.
3. **Resuelta:** la progresión visual se aplica a la recaudación bruta de todos los conceptos. El contador principal dispone de una opción para mostrar únicamente la recaudación bruta agregada. Comisión, IVA, otros gastos y recaudación neta quedan disponibles como valores reales en el detalle.
4. **Resuelta:** la cantidad de comprobantes no se muestra en la pantalla pública, no progresa y queda disponible como valor real únicamente en el panel interno.
5. **Resuelta:** la progresión comienza después de una demora configurable desde la carga, inicialmente 30 minutos, sin esperar una aprobación posterior. Una corrección cuyo objetivo aún supere lo visible conserva el ritmo y puede finalizar anticipadamente; una corrección al alza se ajusta para llegar al cierre. Solo cuando el monto corregido sea inferior a lo ya publicado se permite un ajuste negativo inmediato, acompañado por una leyenda temporal y auditoría.
6. **Resuelta:** si la fecha/hora de cierre es igual o anterior al inicio de la progresión, se bloquea la carga y se exige una fecha/hora posterior.
7. **Resuelta:** todos los canales utilizan inicialmente una plantilla Excel `.xlsx` única o la misma estructura mediante copiar y pegar en una grilla. Ambos caminos usan código, nombre, comprobantes, bruto, comisión, IVA, otros gastos y observaciones; el neto lo calcula el sistema. Canal, fecha de recaudación y fecha de ingreso a TGP se completan en pantalla. Un formato particular podrá incorporarse posteriormente mediante un importador específico.
8. **Resuelta:** se bloquea contenido exacto para el mismo canal y fecha, así como el mismo archivo por hash. La similitud por canal, fecha, cuenta y totales genera advertencia; continuar requiere permiso especial y motivo auditado. Las correcciones utilizan `Reemplazar carga`.
9. **Resuelta:** el operador puede cargar y confirmar cuando todas las validaciones sean correctas. Se exige supervisor o administrador para reemplazos publicados, anulaciones, excepciones de duplicados y resolución de observaciones.
10. **Resuelta:** el creador puede cancelar borradores u observadas. Una carga aprobada requiere supervisor o administrador; después de la fecha de transferencia a TGP, únicamente administrador con motivo obligatorio. Anulada y reemplazada son terminales. Nunca hay borrado físico.
11. **Resuelta:** el operador ve la pantalla pública y únicamente sus cargas, validaciones y estados; el supervisor posee vista operativa completa y el administrador acceso integral. Los accesos adicionales por canal requieren permiso explícito.
12. **Resuelta:** cada canal configura cuenta obligatoria, opcional o no aplicable y una cuenta predeterminada. El operador puede seleccionar otra cuenta asociada; una cuenta externa al canal requiere supervisor o administrador. La selección queda fijada históricamente en la carga.
13. **Resuelta:** quedan definidos los códigos, nombres y orden iniciales; pueden agregarse conceptos y reordenarse desde el panel, con código inmutable y auditoría. Los grupos iniciales son `INMOBILIARIO`, `AUTOMOTOR`, `INGRESOS_BRUTOS`, `SELLOS` —incluida Tasa Retributiva— y `OTROS`.
14. **Resuelta:** el backend actualiza la progresión por escalones según la frecuencia configurada. El Smart TV anima suavemente cada transición durante unos segundos y luego mantiene el valor; la animación no altera ni calcula importes.
15. **Resuelta:** método predeterminado `LINEAL_ALEATORIO_CONTROLADO`, frecuencia 5 minutos, variación máxima ±20 %, intensidad 70 %, suavizado final 5 intervalos, animación pública 5 segundos y `gamma = 2` para `ACELERADO_AL_FINAL`. Son configurables y se guardan por carga.
16. **Resuelta para la primera etapa:** despliegue local con contenedores, PostgreSQL, archivos protegidos localmente y usuarios propios de la aplicación, sin dependencias externas obligatorias. La infraestructura institucional, dominio, SSO y almacenamiento definitivo se definirán después de validar el sistema.
17. **Resuelta para la primera etapa:** dimensionar y probar hasta 50 usuarios registrados, 10 simultáneos, 500 cargas diarias, Excel de hasta 10 MB, respuestas habituales del panel menores a 2 segundos y actualización pública sin interrupciones perceptibles.
18. **Resuelta para la etapa local:** backup de base cada hora, completo diario, copia en otro disco/equipo, 30 respaldos diarios, 12 mensuales y copia previa a actualizaciones. RPO de una hora, RTO de cuatro horas y sin purga automática de cargas, originales o auditoría hasta definir la normativa institucional.
19. **Resuelta:** acceso solo desde la red local; contador de bruto visible, fecha de recaudación y hora de actualización. Sin monto real final, porcentaje ni información interna. Desgloses por grupo o concepto opcionales y desactivados inicialmente. Ante desconexión conserva el último valor con aviso.
20. **Resuelta:** si una corrección deja el bruto real por debajo del bruto ya visible, el contador disminuye al confirmar el reemplazo y muestra temporalmente `Monto actualizado por corrección`.

Estas definiciones constituyen la base funcional para las migraciones, contratos de API, pruebas de aceptación y pantallas.

## 18. Plan de implementación propuesto

### Fase 0 — Descubrimiento y contratos

- consolidar las decisiones aprobadas en criterios de aceptación;
- obtener archivos anonimizados por canal;
- documentar fórmula, redondeo, permisos y estados;
- definir criterios de aceptación, volumen, RPO/RTO y amenazas;
- crear ADR para stack, autenticación, archivos y progresión.

Salida: especificación aprobada y casos de prueba funcionales.

### Fase 1 — Fundación

- repositorio, calidad, CI, ambientes y configuración segura;
- modelo de usuarios/roles/permisos;
- catálogos, migraciones y semillas;
- auditoría append-only;
- almacenamiento de archivos y observabilidad mínima.

Salida: administración segura de catálogos y permisos.

### Fase 2 — Importación trazable

- carga de original y hash;
- adaptador del primer canal;
- staging, validaciones y vista previa;
- aprobación transaccional y totales;
- detección de duplicados.

Salida: una carga puede recorrer el circuito completo con evidencia.

### Fase 3 — Versionado administrativo

- estados y permisos;
- anulación y reemplazo atómicos;
- historial y comparación de versiones;
- pruebas de concurrencia e idempotencia.

Salida: correcciones sin pérdida ni sobrescritura.

### Fase 4 — Motor de progresión

- interfaz de estrategias;
- `LINEAL` e `INMEDIATO`;
- `ACELERADO_AL_FINAL`;
- `LINEAL_ALEATORIO_CONTROLADO` con algoritmo versionado;
- reconciliación por concepto y pruebas de propiedades.

Salida: montos reproducibles, monotónicos y exactos al cierre.

### Fase 5 — Dashboard

- pantalla pública para Smart TV, modo de solo lectura y recuperación ante desconexión;
- endpoint público con contrato de datos mínimo y pruebas de no exposición;
- vista previa y configuración de la pantalla desde el panel interno;
- filtros y criterio temporal internos;
- indicadores y tabla de 15 conceptos;
- gráficos y cargas en curso;
- permisos de visibilidad;
- pruebas de rendimiento y accesibilidad.

Salida: dashboard consistente entre totales, detalles, real y visible.

### Fase 6 — Endurecimiento y operación

- revisión de seguridad y amenazas;
- límites de archivos/rate limiting;
- backups y simulacro de restauración;
- métricas, alertas y manuales;
- pruebas de carga, UAT y plan de salida/reversión.

Salida: versión candidata a producción con evidencia operativa.

## 19. Criterios de aceptación transversales

- Ninguna operación visual modifica importes reales.
- Una carga aprobada no se edita: se anula o reemplaza.
- Todo cambio sensible identifica usuario, instante, resultado y correlación.
- El mismo snapshot produce la misma progresión en cualquier refresco o instancia.
- La recaudación bruta visible nunca supera a la recaudación bruta real y coincide exactamente al cierre.
- La suma del bruto visible por concepto coincide exactamente con el bruto visible total.
- Un cambio de configuración no altera cargas previas.
- Archivos inválidos no llegan a detalle aprobado.
- Acciones no autorizadas fallan en backend aunque se intente evitar la UI.
- Backup y restauración se prueban, no solo se configuran.

## 20. Próximo hito recomendado

Preparar la plantilla Excel aprobada, recopilar al menos un archivo real anonimizado de cada canal para verificar compatibilidad y redactar los ADR técnicos. Luego puede iniciarse la fundación del proyecto y convertir este modelo lógico en migraciones, contratos de API y pruebas de aceptación.
