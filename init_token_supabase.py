"""
Script para inicializar el token de Mercado Libre en Supabase
Ejecuta este script UNA VEZ después de crear la tabla ml_tokens
"""

import json
from services.ml_token_manager import save_ml_token_to_supabase

def init_token_in_supabase():
    """Carga el token desde meli_tokens.json y lo guarda en Supabase"""
    try:
        # Leer el token local
        with open('meli_tokens.json', 'r') as f:
            token_data = json.load(f)
        
        print("📋 Token encontrado en meli_tokens.json:")
        print(f"  - User ID: {token_data.get('user_id')}")
        print(f"  - Nickname: {token_data.get('nickname')}")
        print(f"  - Creado: {token_data.get('created_at')}")
        print(f"  - Actualizado: {token_data.get('updated_at', 'N/A')}")
        print()
        
        # Guardar en Supabase
        print("💾 Guardando token en Supabase...")
        success = save_ml_token_to_supabase(token_data)
        
        if success:
            print("✅ Token guardado exitosamente en Supabase")
            print()
            print("🎉 ¡Listo! Ahora la aplicación usará Supabase para gestionar los tokens.")
            print("   Los tokens se refrescarán automáticamente cuando expiren.")
        else:
            print("❌ Error guardando el token en Supabase")
            print("   Verifica que:")
            print("   1. La tabla 'ml_tokens' exista en Supabase")
            print("   2. Las credenciales de Supabase sean correctas en .env")
            
    except FileNotFoundError:
        print("❌ No se encontró el archivo meli_tokens.json")
        print("   Ejecuta primero: python3 meli_auth.py")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("🔐 INICIALIZAR TOKEN EN SUPABASE")
    print("=" * 60)
    print()
    init_token_in_supabase()
