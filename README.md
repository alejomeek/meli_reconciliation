# 📦 Sistema de Reconciliación Mercado Libre - TBC

Sistema para reconciliar pedidos de Mercado Libre Flex con facturas del sistema TBC (DIDÁCTICOS JUGANDO Y EDUCANDO).

## 🚀 Instalación

### 1. Clonar el repositorio (o descargar archivos)

```bash
cd meli_reconciliation
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Configurar variables de entorno

El archivo `.env` ya está configurado con tus credenciales.

### 4. Configurar Supabase

#### 4.1. Ir a tu proyecto de Supabase:
https://qqqamcusmbalvbfkeiqb.supabase.co

#### 4.2. Ir a SQL Editor (en el menú lateral)

#### 4.3. Copiar y ejecutar el contenido del archivo `database/schema.sql`

Esto creará las 3 tablas necesarias:
- `ml_orders` - Órdenes de Mercado Libre
- `tbc_facturas` - Facturas del sistema TBC
- `discrepancias` - Log de errores encontrados

### 5. Copiar el token de Mercado Libre

Copia el archivo `meli_tokens.json` (que ya generaste con el script de autenticación) a la carpeta del proyecto.

## 📱 Uso

### Ejecutar la aplicación

```bash
streamlit run app.py
```

La aplicación se abrirá en tu navegador en `http://localhost:8501`

## 🎯 Flujo de Trabajo

### 1️⃣ Sincronizar Órdenes de ML

- Hacer clic en **"📥 Sincronizar Órdenes ML"** en el sidebar
- Esto trae las últimas 50 órdenes de Mercado Libre y las guarda en Supabase

### 2️⃣ Asignar Remisiones

- Filtrar por fecha y estado
- Para cada pedido SIN remisión:
  - Ingresar el número de remisión de TBC
  - Ingresar tu nombre
  - Hacer clic en "💾 Guardar"

### 3️⃣ Reconciliación (Próximamente)

- Cargar archivo RESUXDOC.XLS
- Ver discrepancias automáticamente
- Exportar reporte

## 📂 Estructura del Proyecto

```
meli_reconciliation/
├── .env                          # Credenciales
├── .gitignore
├── requirements.txt
├── README.md
├── app.py                        # Aplicación principal
├── config.py                     # Configuración
│
├── database/
│   ├── __init__.py
│   ├── schema.sql                # Schema de Supabase
│   └── supabase_client.py       # Cliente Supabase
│
└── services/
    ├── __init__.py
    └── ml_api.py                 # API Mercado Libre
```

## 🔧 Troubleshooting

### Error: "No se encontró el token de ML"

Ejecuta primero el script de autenticación:
```bash
python meli_auth_test.py
```

### Error: "Faltan variables de entorno"

Verifica que el archivo `.env` exista y tenga todas las variables configuradas.

### Error al sincronizar órdenes

Verifica que el token de ML no haya expirado (duran 6 horas). Re-ejecuta `meli_auth_test.py` si es necesario.

## 📊 Base de Datos (Supabase)

### Ver datos:

1. Ir a https://qqqamcusmbalvbfkeiqb.supabase.co
2. Ir a "Table Editor"
3. Seleccionar tabla: `ml_orders`, `tbc_facturas`, o `discrepancias`

### Ejecutar queries SQL:

1. Ir a "SQL Editor"
2. Escribir query y ejecutar

Ejemplo:
```sql
SELECT * FROM ml_orders WHERE remision IS NULL;
```

## 🎨 Próximas Funcionalidades

- [ ] Página 2: Reconciliación (cargar RESUXDOC.XLS)
- [ ] Página 3: Dashboard con métricas
- [ ] Exportar reportes a Excel
- [ ] Notificaciones por email
- [ ] Búsqueda por SKU

## 👨‍💻 Soporte

Para problemas o preguntas, contactar a Alejo.

---

🏪 **Didácticos Jugando y Educando** © 2026
