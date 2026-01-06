"""
Sistema de Reconciliación Mercado Libre - DIDÁCTICOS JUGANDO Y EDUCANDO
Página Principal / Home
"""

import streamlit as st

# Configuración de la página
st.set_page_config(
    page_title="Home - Reconciliación ML",
    page_icon="🏪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# PÁGINA PRINCIPAL
# ============================================================================

st.title("🏪 Sistema de Reconciliación Mercado Libre")
st.markdown("### Didácticos Jugando y Educando")

st.markdown("---")

st.markdown("""
## 👋 Bienvenido al Sistema de Reconciliación

Este sistema te ayuda a reconciliar tus pedidos de **Mercado Libre Flex** con las facturas del sistema **TBC**.

### 📋 Funcionalidades:

""")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    #### 📝 Página 1: Asignación de Remisiones
    - Ver pedidos de Mercado Libre
    - Asignar números de remisión de TBC
    - Gestionar remisiones pendientes
    - Sincronizar con Mercado Libre
    
    **[👉 Ir a Asignación](/Asignacion)**
    """)

with col2:
    st.markdown("""
    #### 🔍 Página 2: Reconciliación
    - Cargar archivo RESUXDOC.XLS
    - Comparar ML vs TBC automáticamente
    - Detectar discrepancias
    - Exportar reportes a Excel
    
    **[👉 Ir a Reconciliación](/Reconciliacion)**
    """)

st.markdown("---")

st.markdown("""
## 🚀 Flujo de Trabajo Recomendado:

1. **Sincronizar Órdenes** - Actualiza los pedidos desde Mercado Libre
2. **Asignar Remisiones** - Ingresa las remisiones de TBC para cada pedido
3. **Exportar de TBC** - Genera el archivo RESUXDOC.XLS desde TBC
4. **Reconciliar** - Carga el archivo y compara automáticamente
5. **Revisar Discrepancias** - Corrige los errores encontrados
6. **Exportar Reporte** - Descarga el reporte en Excel

---

## 💡 Consejos:

- ✅ Sincroniza las órdenes diariamente para mantener los datos actualizados
- ✅ Asigna las remisiones el mismo día que facturas en TBC
- ✅ Usa la misma fecha de factura en ML y TBC
- ✅ Revisa las discrepancias inmediatamente para corregir errores

---

## 📊 Estado del Sistema:

""")

# Mostrar información del sistema
import config
from database import supabase_client as db
from services import ml_api

# Verificar conexiones
col1, col2, col3 = st.columns(3)

with col1:
    try:
        stats = db.get_estadisticas_generales()
        st.success("✅ Supabase conectado")
        st.metric("Total Órdenes", stats['total_ordenes'])
    except:
        st.error("❌ Error conectando a Supabase")

with col2:
    try:
        token = ml_api.load_ml_token()
        if token:
            st.success("✅ Token ML disponible")
        else:
            st.warning("⚠️ Token ML no encontrado")
    except:
        st.error("❌ Error con token ML")

with col3:
    st.info("ℹ️ Sistema operativo")
    st.metric("Versión", "1.0.0")

st.markdown("---")
st.caption("🏪 Didácticos Jugando y Educando © 2026 | Sistema de Reconciliación ML-TBC")
