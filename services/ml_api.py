"""
Servicio para interactuar con la API de Mercado Libre
"""

import requests
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import config

# ============================================================================
# AUTENTICACIÓN (usa el token guardado)
# ============================================================================

def load_ml_token() -> Optional[str]:
    """Carga el token de ML desde meli_tokens.json"""
    try:
        with open('meli_tokens.json', 'r') as f:
            token_data = json.load(f)
            return token_data.get('access_token')
    except FileNotFoundError:
        return None


def get_user_id() -> Optional[int]:
    """Obtiene el user_id desde el token guardado"""
    try:
        with open('meli_tokens.json', 'r') as f:
            token_data = json.load(f)
            return token_data.get('user_id')
    except FileNotFoundError:
        return None


def refresh_access_token() -> Optional[str]:
    """
    Refresca el access token usando el refresh token
    Retorna el nuevo access token o None si falla
    """
    try:
        # Cargar el refresh token
        with open('meli_tokens.json', 'r') as f:
            token_data = json.load(f)
            refresh_token = token_data.get('refresh_token')
        
        if not refresh_token:
            print("❌ No se encontró refresh_token en meli_tokens.json")
            return None
        
        # Hacer request para refrescar el token
        url = "https://api.mercadolibre.com/oauth/token"
        
        data = {
            'grant_type': 'refresh_token',
            'client_id': config.ML_APP_ID,
            'client_secret': config.ML_CLIENT_SECRET,
            'refresh_token': refresh_token
        }
        
        response = requests.post(url, data=data)
        response.raise_for_status()
        
        new_token_data = response.json()
        
        # Actualizar el archivo con los nuevos tokens
        token_data.update({
            'access_token': new_token_data['access_token'],
            'refresh_token': new_token_data['refresh_token'],
            'expires_in': new_token_data.get('expires_in'),
            'updated_at': datetime.now().isoformat()
        })
        
        with open('meli_tokens.json', 'w') as f:
            json.dump(token_data, f, indent=2)
        
        print("✅ Token refrescado exitosamente")
        return new_token_data['access_token']
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error refrescando token: {e}")
        return None
    except Exception as e:
        print(f"❌ Error inesperado refrescando token: {e}")
        return None


# ============================================================================
# OBTENER ÓRDENES
# ============================================================================

def get_orders(
    access_token: str,
    seller_id: int,
    limit: int = 50,
    offset: int = 0,
    retry_on_401: bool = True
) -> List[Dict[str, Any]]:
    """Obtiene órdenes de Mercado Libre"""
    
    url = "https://api.mercadolibre.com/orders/search"
    
    params = {
        'seller': seller_id,
        'sort': 'date_desc',
        'limit': limit,
        'offset': offset
    }
    
    headers = {'Authorization': f'Bearer {access_token}'}
    
    try:
        response = requests.get(url, params=params, headers=headers)
        
        # Si es 401 (Unauthorized), intentar refrescar el token
        if response.status_code == 401 and retry_on_401:
            print("⚠️ Token expirado, intentando refrescar...")
            new_token = refresh_access_token()
            
            if new_token:
                # Reintentar con el nuevo token
                return get_orders(new_token, seller_id, limit, offset, retry_on_401=False)
            else:
                print("❌ No se pudo refrescar el token")
                return []
        
        response.raise_for_status()
        
        data = response.json()
        return data.get('results', [])
        
    except requests.exceptions.RequestException as e:
        print(f"Error obteniendo órdenes: {e}")
        return []


def get_order_detail(access_token: str, order_id: str) -> Optional[Dict[str, Any]]:
    """Obtiene el detalle completo de una orden"""
    
    url = f"https://api.mercadolibre.com/orders/{order_id}"
    headers = {'Authorization': f'Bearer {access_token}'}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
        
    except requests.exceptions.RequestException as e:
        print(f"Error obteniendo detalle de orden {order_id}: {e}")
        return None


# ============================================================================
# TRANSFORMAR DATOS PARA GUARDAR EN BD
# ============================================================================

def transform_order_for_db(order: Dict[str, Any]) -> Dict[str, Any]:
    """Transforma una orden de ML al formato de la base de datos"""
    
    # Extraer productos
    productos = []
    for item in order.get('order_items', []):
        item_data = item.get('item', {})
        productos.append({
            'id': item_data.get('id'),
            'title': item_data.get('title'),
            'sku': item_data.get('seller_sku'),
            'quantity': item.get('quantity'),
            'unit_price': item.get('unit_price')
        })
    
    # Extraer buyer info
    buyer = order.get('buyer', {})
    
    # Extraer shipping
    shipping = order.get('shipping', {})
    
    return {
        'order_id': str(order.get('id')),
        'pack_id': str(order.get('pack_id')) if order.get('pack_id') else None,
        'shipping_id': str(shipping.get('id')) if shipping.get('id') else None,
        'fecha_orden': order.get('date_created'),
        'total': float(order.get('total_amount', 0)),
        'productos': json.dumps(productos),
        'buyer_name': f"{buyer.get('first_name', '')} {buyer.get('last_name', '')}".strip(),
        'buyer_nickname': buyer.get('nickname'),
        'remision': None,
        'fecha_remision': None,
        'usuario': None,
        'observaciones': None
    }


# ============================================================================
# SINCRONIZAR ÓRDENES
# ============================================================================

def sync_orders_to_db(
    access_token: str,
    seller_id: int,
    limit: int = 50
) -> Dict[str, Any]:
    """Sincroniza órdenes de ML a la base de datos"""
    
    from database.supabase_client import insert_ml_order, check_order_exists
    
    orders = get_orders(access_token, seller_id, limit=limit)
    
    nuevas = 0
    existentes = 0
    errores = 0
    
    for order in orders:
        order_id = str(order.get('id'))
        
        # Verificar si ya existe
        if check_order_exists(order_id):
            existentes += 1
            continue
        
        # Transformar y guardar
        order_data = transform_order_for_db(order)
        result = insert_ml_order(order_data)
        
        if result.get('success'):
            nuevas += 1
        else:
            errores += 1
            print(f"Error guardando orden {order_id}: {result.get('error')}")
    
    return {
        'total_procesadas': len(orders),
        'nuevas': nuevas,
        'existentes': existentes,
        'errores': errores
    }
