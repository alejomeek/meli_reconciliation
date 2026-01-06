# Guía de Despliegue en Streamlit Cloud

## Pasos para Desplegar

### 1. Crear Repositorio en GitHub

1. Ve a https://github.com y crea una cuenta si no tienes
2. Haz clic en "New repository"
3. Nombre sugerido: `meli-reconciliation`
4. Marca como **Private** (para proteger tus datos)
5. **NO** inicialices con README, .gitignore ni licencia
6. Haz clic en "Create repository"

### 2. Subir Código a GitHub

Abre una terminal en la carpeta del proyecto y ejecuta:

```bash
# Inicializar Git
git init

# Agregar todos los archivos
git add .

# Hacer commit
git commit -m "Initial commit - Meli Reconciliation App"

# Conectar con GitHub (reemplaza TU_USUARIO y TU_REPO)
git remote add origin https://github.com/TU_USUARIO/TU_REPO.git

# Subir código
git branch -M main
git push -u origin main
```

### 3. Configurar Streamlit Cloud

1. Ve a https://share.streamlit.io
2. Inicia sesión con tu cuenta de GitHub
3. Haz clic en "New app"
4. Selecciona:
   - **Repository**: tu repositorio (ej: `meli-reconciliation`)
   - **Branch**: `main`
   - **Main file path**: `app.py`
5. Haz clic en "Advanced settings"

### 4. Configurar Secretos (IMPORTANTE)

En "Secrets", pega lo siguiente (reemplaza con tus valores reales):

```toml
[supabase]
url = "TU_SUPABASE_URL"
key = "TU_SUPABASE_KEY"

[mercadolibre]
client_id = "TU_ML_CLIENT_ID"
client_secret = "TU_ML_CLIENT_SECRET"
redirect_uri = "TU_ML_REDIRECT_URI"
```

**¿Dónde encontrar estos valores?**
- Supabase: En tu archivo `.env` o en el dashboard de Supabase
- Mercado Libre: En tu archivo `config.py` o en el portal de desarrolladores de ML

### 5. Actualizar Código para Usar Secretos de Streamlit

El archivo `config.py` debe leer de Streamlit secrets en producción:

```python
import streamlit as st
import os

# Intentar cargar desde Streamlit secrets (producción)
try:
    SUPABASE_URL = st.secrets["supabase"]["url"]
    SUPABASE_KEY = st.secrets["supabase"]["key"]
    ML_CLIENT_ID = st.secrets["mercadolibre"]["client_id"]
    ML_CLIENT_SECRET = st.secrets["mercadolibre"]["client_secret"]
    ML_REDIRECT_URI = st.secrets["mercadolibre"]["redirect_uri"]
except:
    # Fallback a variables de entorno (desarrollo local)
    from dotenv import load_dotenv
    load_dotenv()
    
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY')
    ML_CLIENT_ID = os.getenv('ML_CLIENT_ID')
    ML_CLIENT_SECRET = os.getenv('ML_CLIENT_SECRET')
    ML_REDIRECT_URI = os.getenv('ML_REDIRECT_URI')
```

### 6. Desplegar

1. Haz clic en "Deploy!"
2. Espera 2-5 minutos mientras se instalan las dependencias
3. Tu app estará disponible en una URL como: `https://tu-app.streamlit.app`

### 7. Actualizar la Aplicación

Cada vez que hagas cambios:

```bash
git add .
git commit -m "Descripción de los cambios"
git push
```

Streamlit Cloud detectará los cambios y redesplegará automáticamente.

## Notas Importantes

- **Tokens de ML**: Los tokens se guardan en `meli_tokens.json` localmente. En Streamlit Cloud, necesitarás volver a autenticarte la primera vez.
- **Archivos Excel**: Los archivos que subas (RESUXDOC.XLS) solo existen durante la sesión. No se guardan permanentemente.
- **Base de datos**: Supabase funciona igual en local y en la nube.

## Solución de Problemas

Si la app no funciona:
1. Revisa los logs en Streamlit Cloud
2. Verifica que todos los secretos estén configurados correctamente
3. Asegúrate de que `requirements.txt` tenga todas las dependencias
