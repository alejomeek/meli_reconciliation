"""
Página 2: Reconciliación TBC vs Mercado Libre
"""

import streamlit as st
from datetime import datetime
import pandas as pd
import json
from io import BytesIO
import tempfile
import os

# Importar módulos
import sys
sys.path.append('..')

from database import supabase_client as db
from services import tbc_parser
from services import reconciliation


st.title("🔍 Reconciliación TBC vs Mercado Libre")
st.markdown("Compara las facturas de TBC con las órdenes de Mercado Libre")

# ============================================================================
# PASO 1: CARGAR ARCHIVO TBC
# ============================================================================

st.markdown("---")
st.subheader("📁 Paso 1: Cargar Archivo TBC")

uploaded_file = st.file_uploader(
    "Selecciona el archivo RESUXDOC.XLS",
    type=['xls', 'XLS'],
    help="Archivo exportado desde TBC con las remisiones de Mercado Libre Flex (Evento S66)"
)

if not uploaded_file:
    st.info("👆 Por favor carga el archivo RESUXDOC.XLS para continuar")
    st.stop()

# Guardar archivo temporalmente
temp_file_path = os.path.join(tempfile.gettempdir(), uploaded_file.name)
with open(temp_file_path, "wb") as f:
    f.write(uploaded_file.getbuffer())

st.success(f"✅ Archivo cargado: {uploaded_file.name}")

# ============================================================================
# PASO 2: PARSEAR ARCHIVO TBC
# ============================================================================

st.markdown("---")
st.subheader("📊 Paso 2: Procesar Archivo TBC")

with st.spinner("Procesando archivo TBC..."):
    resultado_tbc = tbc_parser.procesar_archivo_tbc(temp_file_path)

if not resultado_tbc['facturas']:
    st.error("❌ No se pudieron extraer facturas del archivo. Verifica que sea un archivo RESUXDOC.XLS válido.")
    st.stop()

# Mostrar resumen del archivo TBC
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("📋 Total Líneas", resultado_tbc['total_lineas'])

with col2:
    st.metric("🔢 Remisiones Únicas", len(resultado_tbc['remisiones_unicas']))

with col3:
    # Calcular total facturado
    total_facturado = sum([
        tbc_parser.calcular_total_remision(facturas)
        for facturas in resultado_tbc['agrupadas'].values()
    ])
    st.metric("💰 Total Facturado", f"${total_facturado:,.0f}")

# Mostrar preview de facturas
with st.expander("👁️ Ver preview de facturas TBC"):
    # Convertir a DataFrame para mostrar
    df_facturas = pd.DataFrame(resultado_tbc['facturas'][:20])  # Primeras 20
    st.dataframe(df_facturas, use_container_width=True)

# ============================================================================
# PASO 3: OBTENER ÓRDENES ML
# ============================================================================

st.markdown("---")
st.subheader("📦 Paso 3: Obtener Órdenes de Mercado Libre")

# Extraer fechas únicas del archivo TBC
fechas_tbc = set()
for factura in resultado_tbc['facturas']:
    if factura.get('fecha'):
        fechas_tbc.add(factura['fecha'])

fechas_tbc = sorted(list(fechas_tbc))

# Mostrar fechas encontradas en el archivo TBC
if fechas_tbc:
    if len(fechas_tbc) == 1:
        st.info(f"📅 Buscando órdenes con fecha de remisión: {fechas_tbc[0]}")
    else:
        st.info(f"📅 Buscando órdenes con fecha de remisión entre: {fechas_tbc[0]} y {fechas_tbc[-1]} ({len(fechas_tbc)} fechas)")
        with st.expander("Ver todas las fechas"):
            st.write(", ".join(fechas_tbc))
else:
    st.warning("⚠️ No se encontraron fechas en el archivo TBC")
    st.stop()

with st.spinner("Obteniendo órdenes de ML..."):
    # Obtener todas las órdenes con remisión
    ordenes_ml_todas = db.get_ml_orders(
        fecha_desde=None,
        fecha_hasta=None,
        con_remision=True,  # Solo las que tienen remisión
        limit=10000  # Límite alto para obtener todas las órdenes
    )
    
    # Filtrar por fecha_remision que coincida con fechas del archivo TBC
    ordenes_ml = [
        orden for orden in ordenes_ml_todas 
        if orden.get('fecha_remision') in fechas_tbc
    ]

if not ordenes_ml:
    st.warning(f"⚠️ No se encontraron órdenes con fecha de remisión en: {', '.join(fechas_tbc)}")
    st.info("💡 Verifica que las remisiones estén asignadas con las fechas correctas en la página de 'Asignación de Remisiones'.")
    st.info(f"📊 Total de órdenes con remisión en la base de datos: {len(ordenes_ml_todas)}")
    st.stop()

st.success(f"✅ Se encontraron {len(ordenes_ml)} órdenes con fecha de remisión coincidente (de {len(ordenes_ml_todas)} totales)")

# También obtener órdenes SIN remisión para detectar pedidos antiguos sin facturar
with st.spinner("Obteniendo pedidos sin facturar..."):
    ordenes_sin_remision = db.get_ml_orders(
        fecha_desde=None,
        fecha_hasta=None,
        con_remision=False,  # Solo las que NO tienen remisión
        limit=10000  # Límite alto para obtener todas las órdenes
    )

st.info(f"📊 Pedidos sin remisión encontrados: {len(ordenes_sin_remision)}")

# ============================================================================
# PASO 4: RECONCILIAR
# ============================================================================

st.markdown("---")
st.subheader("🔄 Paso 4: Ejecutar Reconciliación")

if st.button("🚀 Comparar ML vs TBC", type="primary", use_container_width=True):
    with st.spinner("Reconciliando datos..."):
        # Obtener fecha mínima del archivo TBC
        fecha_minima_tbc = min(fechas_tbc) if fechas_tbc else None
        
        resultado = reconciliation.reconciliar_ml_tbc(
            ordenes_ml,
            resultado_tbc['agrupadas'],
            fecha_minima_tbc=fecha_minima_tbc,
            ordenes_sin_remision=ordenes_sin_remision
        )
        
        # Guardar en session state
        st.session_state['resultado_reconciliacion'] = resultado
        st.rerun()

# ============================================================================
# PASO 5: MOSTRAR RESULTADOS
# ============================================================================

if 'resultado_reconciliacion' in st.session_state:
    resultado = st.session_state['resultado_reconciliacion']
    
    st.markdown("---")
    st.subheader("📊 Resultados de la Reconciliación")
    
    # Métricas principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("✅ Coincidencias", len(resultado['coincidencias']))
    
    with col2:
        st.metric("⚠️ Discrepancias", len(resultado['discrepancias']))
    
    with col3:
        st.metric("📊 % Exactitud", f"{resultado['porcentaje_coincidencia']:.1f}%")
    
    with col4:
        # Calcular total de remisiones procesadas
        total_procesado = resultado['total_ordenes_ml'] + resultado['total_facturas_tbc']
        st.metric("🔢 Total Procesado", total_procesado)
    
    st.markdown("---")
    st.subheader(f"✅ Coincidencias ({len(resultado['coincidencias'])})")
    
    if resultado['coincidencias']:
        for i, coincidencia in enumerate(resultado['coincidencias'], 1):
            remision = coincidencia['remision']
            total = coincidencia['total']
            fecha = coincidencia['fecha']
            ordenes_ml = coincidencia.get('ordenes_ml', [])
            facturas_tbc = coincidencia.get('facturas_tbc', [])
            
            # Card de coincidencia
            with st.container():
                col1, col2, col3 = st.columns([2, 2, 2])
                
                with col1:
                    st.write(f"**📋 Remisión:** {remision}")
                
                with col2:
                    st.write(f"**💰 Total:** ${total:,.0f}")
                
                with col3:
                    st.write(f"**📅 Fecha:** {fecha if fecha else 'N/A'}")
                
                # Expander con detalles
                with st.expander(f"🔍 Ver Detalle - Remisión {remision}"):
                    # Sección: Órdenes de Mercado Libre
                    st.markdown("### 📦 Órdenes de Mercado Libre")
                    
                    if ordenes_ml:
                        for orden in ordenes_ml:
                            # Mostrar pack_id si existe, sino order_id
                            display_id = orden.get('pack_id') if orden.get('pack_id') else orden['order_id']
                            st.write(f"**Order ID:** `{display_id}` - Total: ${orden['total']:,.0f}")
                            
                            # Mostrar productos de la orden
                            try:
                                productos = json.loads(orden['productos']) if orden['productos'] else []
                                if productos:
                                    st.write("**Productos:**")
                                    for prod in productos:
                                        sku_ml = prod.get('sku', 'N/A')
                                        title = prod.get('title', 'N/A')
                                        quantity = prod.get('quantity', 0)
                                        unit_price = prod.get('unit_price', 0)
                                        st.write(f"  • {title}")
                                        st.write(f"    - SKU ML: `{sku_ml}` | Cantidad: {quantity} | Precio: ${unit_price:,.0f}")
                            except:
                                st.write("  (No se pudieron cargar los productos)")
                            
                            st.write("")  # Espaciador
                    else:
                        st.info("No hay información de órdenes ML")
                    
                    st.markdown("---")
                    
                    # Sección: Productos en TBC
                    st.markdown("### 🏭 Productos en TBC")
                    
                    if facturas_tbc:
                        # Crear tabla de productos TBC
                        df_tbc = pd.DataFrame([{
                            'SKU TBC': f['producto_codigo'],
                            'Nombre': f['producto_nombre'],
                            'Cantidad': f['cantidad'],
                            'Valor Total': f"${f['valor_total']:,.0f}"
                        } for f in facturas_tbc])
                        
                        st.dataframe(df_tbc, use_container_width=True, hide_index=True)
                    else:
                        st.info("No hay información de productos TBC")
                
                st.markdown("---")
    else:
        st.info("No hay coincidencias exactas")
    
    # ========================================================================
    # DISCREPANCIAS
    # ========================================================================
    
    st.markdown("---")
    st.subheader(f"⚠️ Discrepancias ({len(resultado['discrepancias'])})")
    
    if resultado['discrepancias']:
        # Obtener resumen por tipo
        resumen = reconciliation.generar_resumen_discrepancias(resultado)
        
        # Mostrar resumen
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("💰 Valor Diferente", resumen[reconciliation.TIPO_VALOR_DIFERENTE])
        
        with col2:
            st.metric("📝 Sin Factura en TBC", resumen[reconciliation.TIPO_REMISION_SIN_FACTURA])
        
        with col3:
            st.metric("📋 Sin Remisión en ML", resumen[reconciliation.TIPO_FACTURA_SIN_REMISION])
        
        with col4:
            st.metric("⏰ Sin Facturar", resumen[reconciliation.TIPO_PEDIDOS_SIN_FACTURAR])
        
        # Mostrar cada discrepancia
        st.markdown("### Detalle de Discrepancias")
        
        for i, disc in enumerate(resultado['discrepancias'], 1):
            tipo = disc['tipo']
            remision = disc['remision']
            detalle = disc['detalle']
            
            with st.expander(f"⚠️ Discrepancia #{i}: {tipo.replace('_', ' ').title()} - Remisión {remision}"):
                if tipo == reconciliation.TIPO_VALOR_DIFERENTE:
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.write(f"**ML:** ${detalle['total_ml']:,.0f}")
                    
                    with col2:
                        st.write(f"**TBC:** ${detalle['total_tbc']:,.0f}")
                    
                    with col3:
                        st.write(f"**Diferencia:** ${detalle['diferencia']:,.0f}")
                
                elif tipo == reconciliation.TIPO_REMISION_SIN_FACTURA:
                    st.warning(detalle['mensaje'])
                    st.write(f"**Órdenes ML:** {len(detalle['ordenes_ml'])}")
                    
                    # Mostrar pack_id de cada orden
                    st.write("**Detalles de órdenes:**")
                    for orden in detalle['ordenes_ml']:
                        display_id = orden.get('pack_id') if orden.get('pack_id') else orden['order_id']
                        st.write(f"  • Order ID: `{display_id}` - Total: ${orden['total']:,.0f}")
                
                elif tipo == reconciliation.TIPO_FACTURA_SIN_REMISION:
                    st.warning(detalle['mensaje'])
                    st.write(f"Total TBC: ${detalle['total_tbc']:,.0f}")
                
                elif tipo == reconciliation.TIPO_FECHA_DIFERENTE:
                    st.write(f"**Fecha ML:** {detalle['fecha_ml']}")
                    st.write(f"**Fecha TBC:** {detalle['fecha_tbc']}")
                
                elif tipo == reconciliation.TIPO_PEDIDOS_SIN_FACTURAR:
                    st.warning(detalle['mensaje'])
                    st.write(f"**Pedidos sin facturar:** {detalle['cantidad']}")
                    st.write(f"**Fecha límite:** {detalle['fecha_limite']}")
                    
                    # Mostrar lista de pedidos
                    st.write("**Detalles de pedidos:**")
                    for orden in detalle['ordenes']:
                        display_id = orden.get('pack_id') if orden.get('pack_id') else orden['order_id']
                        fecha_orden = orden.get('fecha_orden', 'N/A')
                        
                        # Formatear fecha para mostrar solo la fecha sin hora (en hora de Colombia)
                        if fecha_orden != 'N/A':
                            from datetime import datetime
                            import pytz
                            COLOMBIA_TZ = pytz.timezone('America/Bogota')
                            
                            fecha_utc = datetime.fromisoformat(fecha_orden.replace('Z', '+00:00'))
                            fecha_colombia = fecha_utc.astimezone(COLOMBIA_TZ)
                            fecha_str = fecha_colombia.strftime('%Y-%m-%d')
                        else:
                            fecha_str = 'N/A'
                        
                        st.write(f"  • Order ID: `{display_id}` - Fecha: {fecha_str} - Total: ${orden['total']:,.0f}")
    else:
        st.success("🎉 ¡No se encontraron discrepancias! Todos los datos coinciden.")
    
    # ========================================================================
    # EXPORTAR REPORTE
    # ========================================================================
    
    st.markdown("---")
    st.subheader("📥 Exportar Reporte")
    
    if st.button("📊 Generar Reporte Excel", use_container_width=True):
        import pytz
        COLOMBIA_TZ = pytz.timezone('America/Bogota')
        
        # Crear archivo Excel
        output = BytesIO()
        
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            workbook = writer.book
            
            # ================================================================
            # FORMATOS
            # ================================================================
            
            # Formato para encabezados
            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#4472C4',
                'font_color': 'white',
                'border': 1,
                'align': 'center',
                'valign': 'vcenter'
            })
            
            # Formato para título de resumen
            title_format = workbook.add_format({
                'bold': True,
                'font_size': 14,
                'bg_color': '#2E5090',
                'font_color': 'white',
                'align': 'center',
                'valign': 'vcenter'
            })
            
            # Formatos por tipo de discrepancia
            formato_sin_facturar = workbook.add_format({
                'bg_color': '#FFF2CC',  # Amarillo claro
                'border': 1
            })
            
            formato_remision_sin_factura = workbook.add_format({
                'bg_color': '#FFE699',  # Amarillo
                'border': 1
            })
            
            formato_factura_sin_remision = workbook.add_format({
                'bg_color': '#F4B084',  # Naranja claro
                'border': 1
            })
            
            formato_valor_diferente = workbook.add_format({
                'bg_color': '#F8CBAD',  # Rojo claro
                'border': 1
            })
            
            formato_normal = workbook.add_format({
                'border': 1
            })
            
            # ================================================================
            # HOJA 1: RESUMEN EJECUTIVO
            # ================================================================
            
            worksheet_resumen = workbook.add_worksheet('Resumen')
            
            # Título
            worksheet_resumen.merge_range('A1:B1', 'RESUMEN EJECUTIVO - RECONCILIACIÓN', title_format)
            
            # Información general
            row = 2
            worksheet_resumen.write(row, 0, 'Fecha de Reconciliación:', header_format)
            worksheet_resumen.write(row, 1, datetime.now(COLOMBIA_TZ).strftime('%Y-%m-%d %H:%M'))
            
            row += 1
            worksheet_resumen.write(row, 0, 'Rango de Fechas:', header_format)
            if fechas_tbc:
                rango = f"{fechas_tbc[0]} a {fechas_tbc[-1]}" if len(fechas_tbc) > 1 else fechas_tbc[0]
                worksheet_resumen.write(row, 1, rango)
            
            row += 2
            worksheet_resumen.write(row, 0, 'Total Coincidencias:', header_format)
            worksheet_resumen.write(row, 1, len(resultado['coincidencias']))
            
            row += 1
            worksheet_resumen.write(row, 0, 'Total Discrepancias:', header_format)
            worksheet_resumen.write(row, 1, len(resultado['discrepancias']))
            
            # Resumen por tipo
            if resultado['discrepancias']:
                resumen = reconciliation.generar_resumen_discrepancias(resultado)
                
                row += 2
                worksheet_resumen.write(row, 0, 'DISCREPANCIAS POR TIPO', title_format)
                worksheet_resumen.write(row, 1, '', title_format)
                
                row += 1
                worksheet_resumen.write(row, 0, 'Pedidos sin facturar:', formato_sin_facturar)
                worksheet_resumen.write(row, 1, resumen[reconciliation.TIPO_PEDIDOS_SIN_FACTURAR], formato_sin_facturar)
                
                row += 1
                worksheet_resumen.write(row, 0, 'Remisión sin factura en TBC:', formato_remision_sin_factura)
                worksheet_resumen.write(row, 1, resumen[reconciliation.TIPO_REMISION_SIN_FACTURA], formato_remision_sin_factura)
                
                row += 1
                worksheet_resumen.write(row, 0, 'Factura sin remisión en ML:', formato_factura_sin_remision)
                worksheet_resumen.write(row, 1, resumen[reconciliation.TIPO_FACTURA_SIN_REMISION], formato_factura_sin_remision)
                
                row += 1
                worksheet_resumen.write(row, 0, 'Valor diferente:', formato_valor_diferente)
                worksheet_resumen.write(row, 1, resumen[reconciliation.TIPO_VALOR_DIFERENTE], formato_valor_diferente)
            
            # Ajustar anchos
            worksheet_resumen.set_column('A:A', 30)
            worksheet_resumen.set_column('B:B', 25)
            
            # ================================================================
            # HOJA 2: DISCREPANCIAS DETALLADAS
            # ================================================================
            
            if resultado['discrepancias']:
                discrepancias_data = []
                
                for disc in resultado['discrepancias']:
                    tipo = disc['tipo']
                    detalle = disc['detalle']
                    
                    if tipo == reconciliation.TIPO_PEDIDOS_SIN_FACTURAR:
                        # Pedidos sin facturar
                        for orden in detalle['ordenes']:
                            display_id = orden.get('pack_id') if orden.get('pack_id') else orden['order_id']
                            
                            # Convertir fecha a hora Colombia
                            fecha_str = ''
                            if orden.get('fecha_orden'):
                                fecha_utc = datetime.fromisoformat(orden['fecha_orden'].replace('Z', '+00:00'))
                                fecha_colombia = fecha_utc.astimezone(COLOMBIA_TZ)
                                fecha_str = fecha_colombia.strftime('%Y-%m-%d')
                            
                            # Productos
                            productos_str = ''
                            if orden.get('productos'):
                                try:
                                    import json
                                    prods = json.loads(orden['productos']) if isinstance(orden['productos'], str) else orden['productos']
                                    productos_str = ', '.join([p.get('title', 'N/A') for p in prods])
                                except:
                                    productos_str = ''
                            
                            discrepancias_data.append({
                                'Tipo': 'Pedidos sin facturar',
                                'Remisión': 'N/A',
                                'Order ID': display_id,
                                'Fecha': fecha_str,
                                'Total ML': orden.get('total', 0),
                                'Total TBC': '',
                                'Diferencia': '',
                                'Productos': productos_str
                            })
                    
                    elif tipo == reconciliation.TIPO_REMISION_SIN_FACTURA:
                        # Remisión sin factura en TBC
                        for orden in detalle['ordenes_ml']:
                            display_id = orden.get('pack_id') if orden.get('pack_id') else orden['order_id']
                            
                            # Productos
                            productos_str = ''
                            if orden.get('productos'):
                                try:
                                    import json
                                    prods = json.loads(orden['productos']) if isinstance(orden['productos'], str) else orden['productos']
                                    productos_str = ', '.join([p.get('title', 'N/A') for p in prods])
                                except:
                                    productos_str = ''
                            
                            discrepancias_data.append({
                                'Tipo': 'Remisión sin factura en TBC',
                                'Remisión': disc['remision'],
                                'Order ID': display_id,
                                'Fecha': orden.get('fecha_remision', ''),
                                'Total ML': orden.get('total', 0),
                                'Total TBC': '',
                                'Diferencia': '',
                                'Productos': productos_str
                            })
                    
                    elif tipo == reconciliation.TIPO_FACTURA_SIN_REMISION:
                        # Factura sin remisión en ML
                        productos_str = ''
                        if detalle.get('facturas_tbc'):
                            productos_str = ', '.join([f.get('producto_nombre', 'N/A') for f in detalle['facturas_tbc']])
                        
                        discrepancias_data.append({
                            'Tipo': 'Factura sin remisión en ML',
                            'Remisión': disc['remision'],
                            'Order ID': '',
                            'Fecha': detalle.get('fecha_tbc', ''),
                            'Total ML': '',
                            'Total TBC': detalle.get('total_tbc', 0),
                            'Diferencia': '',
                            'Productos': productos_str
                        })
                    
                    elif tipo == reconciliation.TIPO_VALOR_DIFERENTE:
                        # Valor diferente
                        discrepancias_data.append({
                            'Tipo': 'Valor diferente',
                            'Remisión': disc['remision'],
                            'Order ID': '',
                            'Fecha': detalle.get('fecha_ml', ''),
                            'Total ML': detalle.get('total_ml', 0),
                            'Total TBC': detalle.get('total_tbc', 0),
                            'Diferencia': detalle.get('diferencia', 0),
                            'Productos': ''
                        })
                
                # Crear DataFrame
                df_discrepancias = pd.DataFrame(discrepancias_data)
                df_discrepancias.to_excel(writer, sheet_name='Discrepancias', index=False, startrow=1, header=False)
                
                # Obtener worksheet
                worksheet_disc = writer.sheets['Discrepancias']
                
                # Escribir encabezados
                for col_num, value in enumerate(df_discrepancias.columns.values):
                    worksheet_disc.write(0, col_num, value, header_format)
                
                # Aplicar formato por tipo
                for row_num, row_data in enumerate(discrepancias_data, start=1):
                    tipo = row_data['Tipo']
                    
                    if 'sin facturar' in tipo:
                        formato = formato_sin_facturar
                    elif 'sin factura en TBC' in tipo:
                        formato = formato_remision_sin_factura
                    elif 'sin remisión' in tipo:
                        formato = formato_factura_sin_remision
                    elif 'diferente' in tipo:
                        formato = formato_valor_diferente
                    else:
                        formato = formato_normal
                    
                    for col_num in range(len(df_discrepancias.columns)):
                        worksheet_disc.write(row_num, col_num, df_discrepancias.iloc[row_num-1, col_num], formato)
                
                # Ajustar anchos
                worksheet_disc.set_column('A:A', 30)  # Tipo
                worksheet_disc.set_column('B:B', 12)  # Remisión
                worksheet_disc.set_column('C:C', 20)  # Order ID
                worksheet_disc.set_column('D:D', 12)  # Fecha
                worksheet_disc.set_column('E:E', 12)  # Total ML
                worksheet_disc.set_column('F:F', 12)  # Total TBC
                worksheet_disc.set_column('G:G', 12)  # Diferencia
                worksheet_disc.set_column('H:H', 50)  # Productos
        
        # Preparar descarga
        output.seek(0)
        
        timestamp = datetime.now(COLOMBIA_TZ).strftime("%Y%m%d_%H%M%S")
        filename = f"Discrepancias_Reconciliacion_{timestamp}.xlsx"
        
        st.download_button(
            label="💾 Descargar Reporte de Discrepancias",
            data=output,
            file_name=filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.caption("🏪 Didácticos Jugando y Educando © 2026 | Sistema de Reconciliación ML-TBC")
