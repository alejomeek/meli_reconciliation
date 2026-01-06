"""
Configuración general de la aplicación
"""

import os

# ============================================================================
# SUPABASE
# ============================================================================

# Intentar cargar desde Streamlit secrets (producción)
SUPABASE_URL = None
SUPABASE_KEY = None
ML_APP_ID = None
ML_CLIENT_SECRET = None
ML_REDIRECT_URI = None
ML_SITE_ID = "MCO"

try:
    import streamlit as st
    # Verificar si estamos en Streamlit Cloud
    if hasattr(st, 'secrets') and len(st.secrets) > 0:
        SUPABASE_URL = st.secrets["supabase"]["url"]
        SUPABASE_KEY = st.secrets["supabase"]["key"]
        ML_APP_ID = st.secrets["mercadolibre"]["app_id"]
        ML_CLIENT_SECRET = st.secrets["mercadolibre"]["client_secret"]
        ML_REDIRECT_URI = st.secrets["mercadolibre"]["redirect_uri"]
        ML_SITE_ID = st.secrets["mercadolibre"].get("site_id", "MCO")
    else:
        # No hay secrets configurados, intentar .env
        raise KeyError("No secrets found")
except (ImportError, KeyError, FileNotFoundError):
    # Fallback a variables de entorno (desarrollo local)
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    ML_APP_ID = os.getenv("ML_APP_ID")
    ML_CLIENT_SECRET = os.getenv("ML_CLIENT_SECRET")
    ML_REDIRECT_URI = os.getenv("ML_REDIRECT_URI", "https://www.google.com")
    ML_SITE_ID = os.getenv("ML_SITE_ID", "MCO")

# ============================================================================
# CONFIGURACIÓN GENERAL
# ============================================================================

TIMEZONE = os.getenv("TIMEZONE", "America/Bogota")

# Evento TBC para Mercado Libre Flex
TBC_EVENTO_FLEX = "S66"

# Configuración de paginación
ITEMS_PER_PAGE = 20
MAX_ORDERS_TO_FETCH = 50

# ============================================================================
# VALIDACIONES
# ============================================================================

def validate_config():
    """Valida que todas las variables de entorno necesarias estén configuradas"""
    
    required_vars = {
        "SUPABASE_URL": SUPABASE_URL,
        "SUPABASE_KEY": SUPABASE_KEY,
        "ML_APP_ID": ML_APP_ID,
        "ML_CLIENT_SECRET": ML_CLIENT_SECRET
    }
    
    missing = [key for key, value in required_vars.items() if not value]
    
    if missing:
        raise ValueError(f"Faltan las siguientes variables de entorno: {', '.join(missing)}")
    
    return True
