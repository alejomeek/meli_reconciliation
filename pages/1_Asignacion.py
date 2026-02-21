"""
Sistema de Reconciliación Mercado Libre - DIDÁCTICOS JUGANDO Y EDUCANDO
Aplicación principal
"""

import streamlit as st
from datetime import datetime, timedelta
import json
import pytz

# Importar módulos
import config
from database import supabase_client as db
from services import ml_api

# Timezone de Colombia
COLOMBIA_TZ = pytz.timezone('America/Bogota')

# ============================================================================
# VALIDAR CONFIGURACIÓN
# ============================================================================

try:
    config.validate_config()
except ValueError as e:
    st.error(f"❌ Error de configuración: {e}")
    st.info("Por favor, verifica que el archivo .env tenga todas las variables necesarias.")
    st.stop()

# ============================================================================
# SIDEBAR
# ============================================================================

with st.sidebar:
    st.image("logo_jye.jpg", width=80)
    st.title("🏪 Didácticos J&E")
    st.markdown("---")
    
    # Botón de sincronización
    st.subheader("🔄 Sincronización")
    
    if st.button("📥 Sincronizar Órdenes ML", use_container_width=True):
        with st.spinner("Sincronizando con Mercado Libre..."):
            try:
                access_token = ml_api.load_ml_token()
                seller_id = ml_api.get_user_id()
                
                if not access_token:
                    st.error("❌ No se encontró el access_token de ML.")
                    st.info("💡 Verifica que hayas configurado 'mercadolibre_token.access_token' en Streamlit Secrets")
                elif not seller_id:
                    st.error("❌ No se encontró el seller_id de ML.")
                    st.info("💡 Verifica que hayas configurado 'mercadolibre_token.user_id' en Streamlit Secrets")
                else:
                    # Intentar sincronizar
                    result = ml_api.sync_orders_to_db(access_token, seller_id, limit=50)
                    
                    if result:
                        st.success(f"✅ Sincronización completada")
                        st.info(f"""
                        📊 **Resultados:**
                        - Total procesadas: {result.get('total_procesadas', 0)}
                        - Nuevas: {result.get('nuevas', 0)}
                        - Existentes: {result.get('existentes', 0)}
                        - Errores: {result.get('errores', 0)}
                        """)
                        
                        # Recargar página para mostrar nuevas órdenes
                        if result.get('nuevas', 0) > 0:
                            st.rerun()
                    else:
                        st.error("❌ Error en la sincronización. No se obtuvieron resultados.")
                        
            except Exception as e:
                st.error(f"❌ Error inesperado: {str(e)}")
                st.exception(e)
    
    st.markdown("---")
    
    # Estadísticas generales (actualizadas correctamente)
    st.subheader("📊 Estadísticas")
    
    # Obtener órdenes para contar correctamente
    todas_ordenes = db.get_ml_orders(fecha_desde=None, fecha_hasta=None, con_remision=None, limit=100)
    ordenes_con_remision = [o for o in todas_ordenes if o['remision'] is not None]
    ordenes_sin_remision = [o for o in todas_ordenes if o['remision'] is None]
    discrepancias = db.get_discrepancias(resuelto=False)
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Órdenes", len(todas_ordenes))
        st.metric("Con Remisión", len(ordenes_con_remision))
    with col2:
        st.metric("Sin Remisión", len(ordenes_sin_remision))
        st.metric("Discrepancias", len(discrepancias))

# ============================================================================
# PÁGINA PRINCIPAL: ASIGNACIÓN DE REMISIONES
# ============================================================================

st.title("📝 Asignación de Remisiones - Mercado Libre Flex")
st.markdown("Asigna el número de remisión de TBC a cada pedido de Mercado Libre")

# ============================================================================
# FILTROS
# ============================================================================

col1, col2 = st.columns([2, 1])

with col1:
    st.info("📊 Mostrando todas las órdenes en la base de datos")

with col2:
    filtro_remision = st.selectbox(
        "Estado",
        ["Todas", "Sin remisión", "Con remisión"]
    )

# Convertir filtro a booleano
con_remision = None
if filtro_remision == "Sin remisión":
    con_remision = False
elif filtro_remision == "Con remisión":
    con_remision = True

# ============================================================================
# OBTENER ÓRDENES (todas las órdenes, sin límite)
# ============================================================================

ordenes = db.get_ml_orders(
    fecha_desde=None,
    fecha_hasta=None,
    con_remision=con_remision,
    limit=10000  # Límite alto para obtener todas las órdenes
)

if len(ordenes) == 0:
    st.info("ℹ️ No se encontraron órdenes con los filtros seleccionados. Intenta sincronizar con el botón en el sidebar.")
    st.stop()

st.markdown("---")

# ============================================================================
# AGRUPAR ÓRDENES POR PACK_ID
# ============================================================================

# Agrupar órdenes por pack_id
packs = {}
for orden in ordenes:
    pack_id = orden['pack_id']
    if pack_id:
        if pack_id not in packs:
            packs[pack_id] = []
        packs[pack_id].append(orden)
    else:
        # Si no tiene pack_id, crear un "pack" individual con el order_id
        fake_pack_id = f"SINGLE_{orden['order_id']}"
        packs[fake_pack_id] = [orden]

# ============================================================================
# MOSTRAR PACKS
# ============================================================================

for pack_id, pack_ordenes in packs.items():
    # Determinar si es un pack real o una orden individual
    is_real_pack = not pack_id.startswith("SINGLE_")
    
    # Calcular totales del pack (orden['total'] puede ser None si fue creada desde el OMS)
    total_pack = sum((orden['total'] or 0) for orden in pack_ordenes)
    
    # Obtener todos los productos del pack
    todos_productos = []
    for orden in pack_ordenes:
        try:
            productos = json.loads(orden['productos']) if orden['productos'] else []
            todos_productos.extend(productos)
        except:
            pass
    
    # Usar la primera orden para obtener datos comunes
    orden_principal = pack_ordenes[0]
    
    # Verificar si TODAS las órdenes del pack tienen remisión
    todas_con_remision = all(orden['remision'] is not None for orden in pack_ordenes)
    alguna_con_remision = any(orden['remision'] is not None for orden in pack_ordenes)
    
    # Obtener la remisión (debería ser la misma para todo el pack)
    remision_pack = pack_ordenes[0]['remision'] if todas_con_remision else None
    
    # Card del pack
    with st.container():
        # Header
        col_header1, col_header2 = st.columns([3, 1])
        
        with col_header1:
            # Mostrar solo el pack_id o order_id, sin "(X órdenes)"
            if is_real_pack:
                display_id = pack_id
            else:
                display_id = pack_ordenes[0]['order_id']
            
            if todas_con_remision:
                st.markdown(f"### ✅ #{display_id}")
            else:
                st.markdown(f"### ⚠️ #{display_id}")
        
        with col_header2:
            if todas_con_remision:
                st.success(f"REMISIÓN: {remision_pack}")
            elif alguna_con_remision:
                st.warning("REMISIÓN PARCIAL")
            else:
                st.error("SIN REMISIÓN")
        
        # Detalles
        col1, col2, col3 = st.columns([2, 2, 2])
        
        with col1:
            # Convertir fecha a hora de Colombia
            fecha_utc = datetime.fromisoformat(orden_principal['fecha_orden'].replace('Z', '+00:00'))
            fecha_colombia = fecha_utc.astimezone(COLOMBIA_TZ)
            # Formato: "5 ene 19:05"
            fecha_str = fecha_colombia.strftime("%d %b %H:%M")
            st.write(f"📅 **Fecha:** {fecha_str}")
            
            # Mostrar buyer_name (primero intentar nombre completo, luego nickname)
            if orden_principal.get('buyer_name') and orden_principal['buyer_name'].strip():
                st.write(f"👤 **Cliente:** {orden_principal['buyer_name']}")
            elif orden_principal.get('buyer_nickname'):
                st.write(f"👤 **Cliente:** {orden_principal['buyer_nickname']}")
        
        with col2:
            st.write(f"💰 **Total:** ${total_pack:,.0f}")
            # Solo mostrar cantidad de productos, sin mencionar órdenes
            st.write(f"📦 **Productos:** {len(todos_productos)}")
        
        with col3:
            # Espacio vacío (removimos Pack ID y Shipping ID)
            pass
        
        # Mostrar Order IDs del pack (solo si hay más de 1 orden)
        if is_real_pack and len(pack_ordenes) > 1:
            with st.expander(f"🔢 Ver Order IDs"):
                for orden in pack_ordenes:
                    st.write(f"• Order ID: `{orden['order_id']}` - ${orden['total']:,.0f}")
        
        # Lista de productos
        if todos_productos:
            with st.expander("📦 Ver productos"):
                for prod in todos_productos:
                    st.write(f"• **{prod.get('title', 'N/A')}**")
                    st.write(f"  - SKU: {prod.get('sku', 'N/A')} | Cantidad: {prod.get('quantity', 0)} | Precio: ${prod.get('unit_price', 0):,.0f}")
        
        # Input de remisión (solo si no tiene)
        if not todas_con_remision:
            col_input1, col_input2, col_input3 = st.columns([2, 1, 1])
            
            with col_input1:
                remision_input = st.text_input(
                    "✍️ Remisión TBC",
                    key=f"remision_{pack_id}",
                    placeholder="Ej: 12050"
                )
            
            with col_input2:
                fecha_remision_input = st.date_input(
                    "📅 Fecha Remisión",
                    key=f"fecha_{pack_id}",
                    value=datetime.now().date(),
                    max_value=datetime.now().date(),
                    help="Fecha de la factura en TBC"
                )
            
            with col_input3:
                st.write("")  # Espaciador
                st.write("")  # Espaciador
                if st.button("💾 Guardar", key=f"btn_{pack_id}", use_container_width=True):
                    if remision_input.strip():
                        # Actualizar TODAS las órdenes del pack con la misma remisión
                        errores = []
                        exitos = 0
                        
                        for orden in pack_ordenes:
                            result = db.update_ml_order_remision(
                                orden['order_id'],
                                remision_input.strip(),
                                fecha_remision_input.isoformat()
                            )
                            
                            if result['success']:
                                exitos += 1
                            else:
                                errores.append(f"Order {orden['order_id']}: {result.get('error')}")
                        
                        if exitos == len(pack_ordenes):
                            st.success(f"✅ Remisión {remision_input} asignada correctamente")
                            st.rerun()
                        elif exitos > 0:
                            st.warning(f"⚠️ Remisión asignada a {exitos}/{len(pack_ordenes)} órdenes. Errores: {', '.join(errores)}")
                        else:
                            st.error(f"❌ Error: {', '.join(errores)}")
                    else:
                        st.warning("⚠️ Por favor ingresa un número de remisión")
        
        # Si tiene remisión, mostrar info
        else:
            col_info1, col_info2 = st.columns([2, 2])
            
            with col_info1:
                if orden_principal['fecha_remision']:
                    st.write(f"📅 **Fecha Remisión:** {orden_principal['fecha_remision']}")
            
            with col_info2:
                if orden_principal['usuario']:
                    st.write(f"👤 **Asignado por:** {orden_principal['usuario']}")
        
        st.markdown("---")

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.caption("🏪 Didácticos Jugando y Educando © 2026 | Sistema de Reconciliación ML-TBC")
