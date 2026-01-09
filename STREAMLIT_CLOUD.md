# 🚀 Despliegue en Streamlit Cloud

Esta guía te ayudará a desplegar tu aplicación en Streamlit Cloud.

## 📋 Requisitos previos

1. Tener una cuenta en [Streamlit Cloud](https://streamlit.io/cloud)
2. Tener tu código en un repositorio de GitHub
3. Haber ejecutado `python3 meli_auth.py` localmente para obtener los tokens

## 🔧 Paso 1: Preparar el código para GitHub

### 1.1 Verificar que los archivos sensibles estén en `.gitignore`

Asegúrate de que estos archivos **NO** se suban a GitHub:

```
.env
meli_tokens.json
*.xls
*.xlsx
```

Estos ya están en tu `.gitignore`, así que estás protegido.

### 1.2 Hacer commit y push a GitHub

```bash
git add .
git commit -m "Actualizar aplicación con soporte para Streamlit Cloud"
git push origin main
```

> **Nota:** Si es tu primer commit, primero necesitas inicializar el repositorio:
> ```bash
> git init
> git add .
> git commit -m "Initial commit"
> git branch -M main
> git remote add origin https://github.com/TU_USUARIO/TU_REPO.git
> git push -u origin main
> ```

## 🔐 Paso 2: Configurar Streamlit Secrets

En Streamlit Cloud, los secretos se configuran a través de la interfaz web.

### 2.1 Ir a la configuración de tu app

1. Ve a [share.streamlit.io](https://share.streamlit.io)
2. Selecciona tu aplicación (o créala si aún no existe)
3. Haz clic en **"⚙️ Settings"** → **"Secrets"**

### 2.2 Agregar los secretos

Copia y pega el siguiente contenido en el editor de secrets, **reemplazando los valores** con tus credenciales reales:

```toml
# Supabase
[supabase]
url = "https://tu-proyecto.supabase.co"
key = "tu_clave_de_supabase"

# Mercado Libre - Configuración de la app
[mercadolibre]
app_id = "3938652167106247"
client_secret = "tu_client_secret_aqui"
redirect_uri = "https://www.google.com"
site_id = "MCO"

# Mercado Libre - Token de autenticación
[mercadolibre_token]
access_token = "APP_USR-3938652167106247-010912-742f1526c98d8570fc59e2bf4afdffa7-132688207"
refresh_token = "TG-696128d929e5bc0001ff0be5-132688207"
user_id = 132688207
nickname = "JUGANDOYEDUCANDO.COM"
expires_in = 21600
```

### 2.3 Valores que debes reemplazar

| Campo | Dónde encontrarlo |
|-------|-------------------|
| `supabase.url` | Supabase → Settings → API → Project URL |
| `supabase.key` | Supabase → Settings → API → anon/public key |
| `mercadolibre.client_secret` | Tu archivo `.env` local |
| `mercadolibre_token.*` | El archivo `meli_tokens.json` que generaste localmente |

> **⚠️ IMPORTANTE:** Los valores en `mercadolibre_token` son los que obtuviste al ejecutar `python3 meli_auth.py` localmente. Cópialos exactamente como aparecen en tu archivo `meli_tokens.json`.

## 🎯 Paso 3: Desplegar la aplicación

### 3.1 Crear una nueva app (si aún no existe)

1. Ve a [share.streamlit.io](https://share.streamlit.io)
2. Haz clic en **"New app"**
3. Selecciona:
   - **Repository:** Tu repositorio de GitHub
   - **Branch:** `main`
   - **Main file path:** `app.py`
4. Haz clic en **"Deploy"**

### 3.2 Si ya existe la app

1. Ve a tu app en Streamlit Cloud
2. Haz clic en **"⋮"** (menú) → **"Reboot"**
3. Espera a que se reinicie

## ✅ Paso 4: Verificar que funciona

1. Abre tu app en Streamlit Cloud
2. En el sidebar, haz clic en **"📥 Sincronizar Órdenes ML"**
3. Deberías ver que sincroniza correctamente las órdenes

## 🔄 Renovación automática del token

El token se renovará automáticamente cuando expire. Sin embargo, hay una limitación:

- **En Streamlit Cloud, NO se pueden actualizar los secrets automáticamente**
- Cuando el `refresh_token` expire (después de ~6 meses), necesitarás:
  1. Ejecutar `python3 meli_auth.py` localmente de nuevo
  2. Actualizar los valores en Streamlit Secrets manualmente

## 🐛 Solución de problemas

### Error: "No se encontró el token de ML"

- Verifica que hayas configurado correctamente la sección `[mercadolibre_token]` en Streamlit Secrets
- Asegúrate de que los valores sean exactamente los mismos que en tu `meli_tokens.json` local

### Error: "Error de configuración: Faltan variables de entorno"

- Verifica que hayas configurado las secciones `[supabase]` y `[mercadolibre]` en Streamlit Secrets
- Asegúrate de que no haya errores de tipeo en los nombres de las claves

### El token expira constantemente

- Esto es normal, el token de Mercado Libre expira cada 6 horas
- La aplicación debería renovarlo automáticamente
- Si no se renueva, verifica que el `refresh_token` en Streamlit Secrets sea correcto

## 📝 Notas adicionales

- **Seguridad:** Nunca compartas tus secrets de Streamlit Cloud
- **Backup:** Guarda una copia de tus secrets en un lugar seguro (como un gestor de contraseñas)
- **Actualizaciones:** Cada vez que hagas cambios en el código, haz `git push` y Streamlit Cloud se actualizará automáticamente
