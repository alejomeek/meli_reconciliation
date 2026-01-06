"""
Motor de Reconciliación - Comparar órdenes ML con facturas TBC
"""

from typing import List, Dict, Any
from datetime import datetime
import json

# ============================================================================
# TIPOS DE DISCREPANCIAS
# ============================================================================

TIPO_VALOR_DIFERENTE = "valor_diferente"
TIPO_PRODUCTOS_DIFERENTES = "productos_diferentes"
TIPO_REMISION_SIN_FACTURA = "remision_sin_factura"
TIPO_FACTURA_SIN_REMISION = "factura_sin_remision"
TIPO_FECHA_DIFERENTE = "fecha_diferente"
TIPO_PEDIDOS_SIN_FACTURAR = "pedidos_sin_facturar"  # Nuevo: pedidos antiguos sin remisión

# ============================================================================
# RECONCILIACIÓN
# ============================================================================

def reconciliar_ml_tbc(
    ordenes_ml: List[Dict[str, Any]],
    facturas_tbc: Dict[str, List[Dict[str, Any]]],
    fecha_minima_tbc: str = None,
    ordenes_sin_remision: List[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Compara órdenes de ML con facturas de TBC y encuentra discrepancias
    
    Args:
        ordenes_ml: Lista de órdenes de ML (desde Supabase)
        facturas_tbc: Diccionario de facturas agrupadas por remisión
        fecha_minima_tbc: Fecha mínima del archivo TBC para detectar pedidos sin facturar
        ordenes_sin_remision: Lista de órdenes sin remisión para detectar pedidos antiguos
    
    Returns:
        {
            'coincidencias': Lista de remisiones que coinciden,
            'discrepancias': Lista de discrepancias encontradas,
            'total_ordenes': Cantidad de órdenes ML,
            'total_facturas': Cantidad de remisiones TBC,
            'porcentaje_coincidencia': Porcentaje de coincidencias
        }
    """
    
    coincidencias = []
    discrepancias = []
    
    # Agrupar órdenes ML por remisión
    ordenes_por_remision = {}
    for orden in ordenes_ml:
        remision = orden.get('remision')
        if remision:
            if remision not in ordenes_por_remision:
                ordenes_por_remision[remision] = []
            ordenes_por_remision[remision].append(orden)
    
    # Comparar cada remisión de ML con TBC
    for remision, ordenes in ordenes_por_remision.items():
        facturas = facturas_tbc.get(remision)
        
        if not facturas:
            # Remisión en ML pero no en TBC
            discrepancias.append({
                'tipo': TIPO_REMISION_SIN_FACTURA,
                'remision': remision,
                'detalle': {
                    'ordenes_ml': ordenes,
                    'mensaje': f'Remisión {remision} asignada en ML pero no encontrada en TBC'
                }
            })
            continue
        
        # Calcular totales
        total_ml = sum(orden['total'] for orden in ordenes)
        total_tbc = sum(f.get('valor_total', 0) for f in facturas if f.get('valor_total'))
        
        # Comparar valores
        diferencia = abs(total_ml - total_tbc)
        
        if diferencia > 100:  # Tolerancia de $100
            discrepancias.append({
                'tipo': TIPO_VALOR_DIFERENTE,
                'remision': remision,
                'detalle': {
                    'total_ml': total_ml,
                    'total_tbc': total_tbc,
                    'diferencia': diferencia,
                    'ordenes_ml': ordenes,
                    'facturas_tbc': facturas
                }
            })
        else:
            # Comparar fechas
            fecha_ml = ordenes[0].get('fecha_remision')
            fecha_tbc = facturas[0].get('fecha')
            
            if fecha_ml and fecha_tbc and fecha_ml != fecha_tbc:
                discrepancias.append({
                    'tipo': TIPO_FECHA_DIFERENTE,
                    'remision': remision,
                    'detalle': {
                        'fecha_ml': fecha_ml,
                        'fecha_tbc': fecha_tbc,
                        'ordenes_ml': ordenes,
                        'facturas_tbc': facturas
                    }
                })
            else:
                # Todo coincide
                coincidencias.append({
                    'remision': remision,
                    'total': total_ml,
                    'fecha': fecha_ml,
                    'cantidad_ordenes': len(ordenes),
                    'cantidad_productos': len(facturas),
                    'ordenes_ml': ordenes,  # Incluir detalles completos de órdenes ML
                    'facturas_tbc': facturas  # Incluir detalles completos de facturas TBC
                })
    
    # Buscar facturas en TBC que no están en ML
    for remision, facturas in facturas_tbc.items():
        if remision not in ordenes_por_remision:
            total_tbc = sum(f.get('valor_total', 0) for f in facturas if f.get('valor_total'))
            
            discrepancias.append({
                'tipo': TIPO_FACTURA_SIN_REMISION,
                'remision': remision,
                'detalle': {
                    'total_tbc': total_tbc,
                    'facturas_tbc': facturas,
                    'mensaje': f'Factura {remision} en TBC pero no tiene remisión asignada en ML'
                }
            })
    
    # Buscar pedidos sin facturar (sin remisión) anteriores a la fecha TBC
    if fecha_minima_tbc and ordenes_sin_remision:
        import pytz
        COLOMBIA_TZ = pytz.timezone('America/Bogota')
        
        pedidos_antiguos_sin_facturar = []
        
        for orden in ordenes_sin_remision:
            if orden.get('fecha_orden'):
                # Convertir fecha_orden de UTC a hora de Colombia
                fecha_utc = datetime.fromisoformat(orden['fecha_orden'].replace('Z', '+00:00'))
                fecha_colombia = fecha_utc.astimezone(COLOMBIA_TZ)
                
                # Extraer solo la fecha (YYYY-MM-DD) en hora de Colombia
                fecha_orden_str = fecha_colombia.strftime('%Y-%m-%d')
                
                # Comparar fechas como strings (formato YYYY-MM-DD)
                if fecha_orden_str < fecha_minima_tbc:
                    pedidos_antiguos_sin_facturar.append(orden)
        
        if pedidos_antiguos_sin_facturar:
            discrepancias.append({
                'tipo': TIPO_PEDIDOS_SIN_FACTURAR,
                'remision': 'N/A',
                'detalle': {
                    'fecha_limite': fecha_minima_tbc,
                    'cantidad': len(pedidos_antiguos_sin_facturar),
                    'ordenes': pedidos_antiguos_sin_facturar,
                    'mensaje': f'Se encontraron {len(pedidos_antiguos_sin_facturar)} pedidos sin facturar anteriores a {fecha_minima_tbc}'
                }
            })
    
    # Calcular porcentaje de coincidencia
    total_comparaciones = len(ordenes_por_remision) + len([r for r in facturas_tbc.keys() if r not in ordenes_por_remision])
    porcentaje = (len(coincidencias) / total_comparaciones * 100) if total_comparaciones > 0 else 0
    
    return {
        'coincidencias': coincidencias,
        'discrepancias': discrepancias,
        'total_ordenes_ml': len(ordenes_por_remision),
        'total_facturas_tbc': len(facturas_tbc),
        'porcentaje_coincidencia': round(porcentaje, 2)
    }


# ============================================================================
# GENERAR REPORTE
# ============================================================================

def generar_resumen_discrepancias(resultado: Dict[str, Any]) -> Dict[str, int]:
    """
    Genera un resumen contando cada tipo de discrepancia
    """
    
    resumen = {
        TIPO_VALOR_DIFERENTE: 0,
        TIPO_PRODUCTOS_DIFERENTES: 0,
        TIPO_REMISION_SIN_FACTURA: 0,
        TIPO_FACTURA_SIN_REMISION: 0,
        TIPO_FECHA_DIFERENTE: 0,
        TIPO_PEDIDOS_SIN_FACTURAR: 0
    }
    
    for disc in resultado['discrepancias']:
        tipo = disc['tipo']
        if tipo in resumen:
            resumen[tipo] += 1
    
    return resumen
