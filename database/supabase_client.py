"""
Cliente de Supabase para interactuar con la base de datos
"""

from supabase import create_client, Client
from typing import Optional, List, Dict, Any
from datetime import datetime
import json
import config

# ============================================================================
# CLIENTES SUPABASE
# ============================================================================

def get_supabase_client() -> Client:
    """Obtiene el cliente de Supabase de meli_reconciliation (discrepancias, tbc_facturas)"""
    return create_client(config.SUPABASE_URL, config.SUPABASE_KEY)

supabase: Client = get_supabase_client()

# Cliente OMS (fuente de verdad de órdenes ML)
_oms_client: Optional[Client] = None

def _get_oms_client() -> Client:
    """Obtiene (o crea) el cliente Supabase del OMS de forma lazy."""
    global _oms_client
    if _oms_client is None:
        if not config.OMS_SUPABASE_URL or not config.OMS_SUPABASE_KEY:
            raise ValueError(
                "OMS_SUPABASE_URL y OMS_SUPABASE_KEY deben estar configurados "
                "para acceder a las órdenes de Mercado Libre."
            )
        _oms_client = create_client(config.OMS_SUPABASE_URL, config.OMS_SUPABASE_KEY)
    return _oms_client


def _map_oms_order(row: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convierte una fila de `orders` del OMS al formato que espera
    el motor de reconciliación (mismo esquema que ml_orders).
    """
    customer = row.get('customer') or {}
    shipping = row.get('shipping_address') or {}
    items = row.get('items') or []

    productos = [
        {
            'sku': item.get('sku', ''),
            'title': item.get('title', ''),
            'quantity': item.get('quantity', 0),
            'unit_price': item.get('unitPrice', 0),
        }
        for item in items
    ]

    return {
        'order_id': row.get('order_id'),
        'pack_id': row.get('pack_id'),
        'shipping_id': row.get('shipping_id'),
        'fecha_orden': row.get('order_date'),
        'total': row.get('total_amount', 0),
        'productos': json.dumps(productos),
        'buyer_name': shipping.get('receiverName'),
        'buyer_nickname': customer.get('nickname'),
        'remision': row.get('remision_tbc'),
        'fecha_remision': row.get('fecha_remision_tbc'),
        'usuario': None,
    }

# ============================================================================
# FUNCIONES PARA ML_ORDERS
# ============================================================================

def insert_ml_order(order_data: Dict[str, Any]) -> Dict[str, Any]:
    """Inserta una orden de Mercado Libre en la base de datos"""
    try:
        response = supabase.table("ml_orders").insert(order_data).execute()
        return {"success": True, "data": response.data}
    except Exception as e:
        return {"success": False, "error": str(e)}


def update_ml_order_remision(order_id: str, remision: str, fecha_remision: str) -> Dict[str, Any]:
    """Actualiza la remisión de una orden de ML"""
    try:
        response = supabase.table("ml_orders").update({
            "remision": remision,
            "fecha_remision": fecha_remision,
            "usuario": "Sistema"  # Valor por defecto
        }).eq("order_id", order_id).execute()
        
        return {"success": True, "data": response.data}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_ml_orders(
    fecha_desde: Optional[str] = None,
    fecha_hasta: Optional[str] = None,
    con_remision: Optional[bool] = None,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """
    Obtiene órdenes ML desde el OMS (fuente de verdad).
    Devuelve los datos mapeados al formato histórico de ml_orders para
    mantener compatibilidad con el motor de reconciliación.
    """
    try:
        oms = _get_oms_client()
        query = oms.table("orders").select("*").eq("channel", "mercadolibre")

        if fecha_desde:
            query = query.gte("order_date", fecha_desde)

        if fecha_hasta:
            query = query.lte("order_date", fecha_hasta)

        if con_remision is True:
            query = query.not_.is_("remision_tbc", "null")
        elif con_remision is False:
            query = query.is_("remision_tbc", "null")

        query = query.order("order_date", desc=True).limit(limit)

        response = query.execute()

        # Excluir pedidos de Medellín (no hacen parte del control TBC-Flex)
        def _es_medellin(row: Dict[str, Any]) -> bool:
            city = ((row.get('shipping_address') or {}).get('city') or '').lower().strip()
            return 'medell' in city

        data_filtrada = [row for row in (response.data or []) if not _es_medellin(row)]
        return [_map_oms_order(row) for row in data_filtrada]

    except Exception as e:
        print(f"Error obteniendo órdenes desde OMS: {e}")
        return []


def get_ml_order_by_id(order_id: str) -> Optional[Dict[str, Any]]:
    """Obtiene una orden específica por su order_id"""
    try:
        response = supabase.table("ml_orders").select("*").eq("order_id", order_id).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"Error obteniendo orden {order_id}: {e}")
        return None


def check_order_exists(order_id: str) -> bool:
    """Verifica si una orden ya existe en la base de datos"""
    try:
        response = supabase.table("ml_orders").select("id").eq("order_id", order_id).execute()
        return len(response.data) > 0
    except Exception as e:
        print(f"Error verificando orden: {e}")
        return False


# ============================================================================
# FUNCIONES PARA TBC_FACTURAS
# ============================================================================

def insert_tbc_facturas(facturas: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Inserta múltiples facturas del archivo TBC"""
    try:
        response = supabase.table("tbc_facturas").insert(facturas).execute()
        return {"success": True, "count": len(response.data)}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_tbc_facturas_by_remision(remision: str) -> List[Dict[str, Any]]:
    """Obtiene todas las líneas de factura para una remisión específica"""
    try:
        response = supabase.table("tbc_facturas").select("*").eq("remision", remision).execute()
        return response.data
    except Exception as e:
        print(f"Error obteniendo facturas para remisión {remision}: {e}")
        return []


def delete_tbc_facturas_by_archivo(archivo_nombre: str) -> Dict[str, Any]:
    """Elimina todas las facturas de un archivo específico"""
    try:
        response = supabase.table("tbc_facturas").delete().eq("archivo_nombre", archivo_nombre).execute()
        return {"success": True, "count": len(response.data)}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============================================================================
# FUNCIONES PARA DISCREPANCIAS
# ============================================================================

def insert_discrepancia(discrepancia_data: Dict[str, Any]) -> Dict[str, Any]:
    """Registra una discrepancia encontrada"""
    try:
        response = supabase.table("discrepancias").insert(discrepancia_data).execute()
        return {"success": True, "data": response.data}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_discrepancias(resuelto: Optional[bool] = None) -> List[Dict[str, Any]]:
    """Obtiene discrepancias con filtro opcional de resuelto"""
    try:
        query = supabase.table("discrepancias").select("*")
        
        if resuelto is not None:
            query = query.eq("resuelto", resuelto)
        
        query = query.order("fecha_deteccion", desc=True)
        
        response = query.execute()
        return response.data
        
    except Exception as e:
        print(f"Error obteniendo discrepancias: {e}")
        return []


def marcar_discrepancia_resuelta(discrepancia_id: int, notas: str = "") -> Dict[str, Any]:
    """Marca una discrepancia como resuelta"""
    try:
        response = supabase.table("discrepancias").update({
            "resuelto": True,
            "fecha_resolucion": datetime.now().isoformat(),
            "notas_resolucion": notas
        }).eq("id", discrepancia_id).execute()
        
        return {"success": True, "data": response.data}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============================================================================
# FUNCIONES DE ESTADÍSTICAS
# ============================================================================

def get_estadisticas_generales() -> Dict[str, Any]:
    """Obtiene estadísticas generales del sistema"""
    try:
        # Total de órdenes
        total_orders = supabase.table("ml_orders").select("id", count="exact").execute()
        
        # Órdenes con remisión
        orders_with_remision = supabase.table("ml_orders").select("id", count="exact").not_.is_("remision", "null").execute()
        
        # Discrepancias pendientes
        discrepancias_pendientes = supabase.table("discrepancias").select("id", count="exact").eq("resuelto", False).execute()
        
        return {
            "total_ordenes": total_orders.count,
            "ordenes_con_remision": orders_with_remision.count,
            "ordenes_sin_remision": total_orders.count - orders_with_remision.count,
            "discrepancias_pendientes": discrepancias_pendientes.count
        }
    except Exception as e:
        print(f"Error obteniendo estadísticas: {e}")
        return {
            "total_ordenes": 0,
            "ordenes_con_remision": 0,
            "ordenes_sin_remision": 0,
            "discrepancias_pendientes": 0
        }
