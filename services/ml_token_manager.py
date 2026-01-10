"""
Funciones para gestión de tokens de Mercado Libre en Supabase
"""

from typing import Dict, Any, Optional
from datetime import datetime
import requests
import json
import config


def load_ml_token_from_supabase() -> Optional[Dict[str, Any]]:
    """Carga el token desde Supabase"""
    try:
        from database.supabase_client import supabase
        
        result = supabase.table('ml_tokens').select('*').order('created_at', desc=True).limit(1).execute()
        
        if result.data and len(result.data) > 0:
            return result.data[0]
        return None
    except Exception as e:
        print(f"Error cargando token desde Supabase: {e}")
        return None


def save_ml_token_to_supabase(token_data: Dict[str, Any]) -> bool:
    """Guarda el token en Supabase"""
    try:
        from database.supabase_client import supabase
        
        # Eliminar tokens antiguos e insertar el nuevo
        supabase.table('ml_tokens').delete().neq('id', 0).execute()
        
        supabase.table('ml_tokens').insert({
            'access_token': token_data['access_token'],
            'refresh_token': token_data['refresh_token'],
            'user_id': token_data.get('user_id'),
            'nickname': token_data.get('nickname'),
            'expires_in': token_data.get('expires_in')
        }).execute()
        
        print("✅ Token guardado en Supabase")
        return True
    except Exception as e:
        print(f"Error guardando token en Supabase: {e}")
        return False


def refresh_ml_token_in_supabase() -> Optional[str]:
    """
    Refresca el access token usando el refresh token
    Guarda el nuevo token en Supabase
    Retorna el nuevo access token o None si falla
    """
    try:
        # Obtener el refresh token desde Supabase
        token_data = load_ml_token_from_supabase()
        
        if not token_data or not token_data.get('refresh_token'):
            print("❌ No se encontró refresh_token en Supabase")
            return None
        
        refresh_token = token_data['refresh_token']
        user_id = token_data.get('user_id')
        nickname = token_data.get('nickname')
        
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
        
        # Preparar datos completos del token
        token_info = {
            'access_token': new_token_data['access_token'],
            'refresh_token': new_token_data['refresh_token'],
            'expires_in': new_token_data.get('expires_in'),
            'user_id': user_id,
            'nickname': nickname
        }
        
        # Guardar en Supabase
        save_ml_token_to_supabase(token_info)
        
        print("✅ Token refrescado exitosamente en Supabase")
        return new_token_data['access_token']
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error refrescando token: {e}")
        return None
    except Exception as e:
        print(f"❌ Error inesperado refrescando token: {e}")
        return None
