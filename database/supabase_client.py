"""
Cliente de Supabase para interactuar con la base de datos
"""

from supabase import create_client, Client
from typing import Optional, List, Dict, Any
from datetime import datetime
import config

# ============================================================================
# CLIENTE SUPABASE
# ============================================================================

def get_supabase_client() -> Client:
    """Obtiene el cliente de Supabase"""
    return create_client(config.SUPABASE_URL, config.SUPABASE_KEY)

supabase: Client = get_supabase_client()

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
    """Obtiene órdenes de ML con filtros opcionales"""
    try:
        query = supabase.table("ml_orders").select("*")
        
        if fecha_desde:
            query = query.gte("fecha_orden", fecha_desde)
        
        if fecha_hasta:
            query = query.lte("fecha_orden", fecha_hasta)
        
        if con_remision is True:
            query = query.not_.is_("remision", "null")
        elif con_remision is False:
            query = query.is_("remision", "null")
        
        query = query.order("fecha_orden", desc=True).limit(limit)
        
        response = query.execute()
        return response.data
        
    except Exception as e:
        print(f"Error obteniendo órdenes: {e}")
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
