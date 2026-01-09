"""
Script para obtener el token de autenticación de Mercado Libre
Ejecuta este script para generar el archivo meli_tokens.json
"""

import requests
import json
import webbrowser
from urllib.parse import urlparse, parse_qs, urlencode
import config
import hashlib
import base64
import secrets

def generate_code_verifier():
    """Genera un code_verifier aleatorio para PKCE"""
    code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8')
    # Remover caracteres de padding
    return code_verifier.replace('=', '').replace('+', '-').replace('/', '_')

def generate_code_challenge(code_verifier):
    """Genera el code_challenge a partir del code_verifier"""
    code_challenge = hashlib.sha256(code_verifier.encode('utf-8')).digest()
    code_challenge = base64.urlsafe_b64encode(code_challenge).decode('utf-8')
    # Remover caracteres de padding
    return code_challenge.replace('=', '').replace('+', '-').replace('/', '_')

def get_authorization_url(code_challenge):
    """Genera la URL de autorización de Mercado Libre con PKCE"""
    params = {
        'response_type': 'code',
        'client_id': config.ML_APP_ID,
        'redirect_uri': config.ML_REDIRECT_URI,
        'code_challenge': code_challenge,
        'code_challenge_method': 'S256'
    }
    auth_url = f"https://auth.mercadolibre.com.co/authorization?{urlencode(params)}"
    return auth_url

def exchange_code_for_token(code: str, code_verifier: str):
    """Intercambia el código de autorización por un access token usando PKCE"""
    url = "https://api.mercadolibre.com/oauth/token"
    
    data = {
        'grant_type': 'authorization_code',
        'client_id': config.ML_APP_ID,
        'client_secret': config.ML_CLIENT_SECRET,
        'code': code,
        'redirect_uri': config.ML_REDIRECT_URI,
        'code_verifier': code_verifier
    }
    
    try:
        response = requests.post(url, data=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Error obteniendo token: {e}")
        if hasattr(e.response, 'text'):
            print(f"Respuesta: {e.response.text}")
        return None

def get_user_info(access_token: str):
    """Obtiene información del usuario autenticado"""
    url = "https://api.mercadolibre.com/users/me"
    headers = {'Authorization': f'Bearer {access_token}'}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Error obteniendo info de usuario: {e}")
        return None

def save_tokens(token_data: dict, user_info: dict):
    """Guarda los tokens en un archivo JSON"""
    from datetime import datetime
    
    data_to_save = {
        'access_token': token_data['access_token'],
        'refresh_token': token_data['refresh_token'],
        'expires_in': token_data.get('expires_in'),
        'user_id': user_info.get('id'),
        'nickname': user_info.get('nickname'),
        'created_at': datetime.now().isoformat()
    }
    
    with open('meli_tokens.json', 'w') as f:
        json.dump(data_to_save, f, indent=2)
    
    print("✅ Tokens guardados en meli_tokens.json")

def main():
    """Proceso principal de autenticación"""
    print("=" * 60)
    print("🔐 AUTENTICACIÓN CON MERCADO LIBRE")
    print("=" * 60)
    print()
    
    # Validar configuración
    try:
        config.validate_config()
    except ValueError as e:
        print(f"❌ Error de configuración: {e}")
        print("Por favor, verifica que el archivo .env tenga todas las variables necesarias.")
        return
    
    # Generar code_verifier y code_challenge para PKCE
    code_verifier = generate_code_verifier()
    code_challenge = generate_code_challenge(code_verifier)
    
    # Paso 1: Generar URL de autorización
    auth_url = get_authorization_url(code_challenge)
    print("📋 PASO 1: Autorización")
    print("-" * 60)
    print("Se abrirá una ventana del navegador para autorizar la aplicación.")
    print("Si no se abre automáticamente, copia y pega esta URL en tu navegador:")
    print()
    print(auth_url)
    print()
    
    # Abrir navegador
    webbrowser.open(auth_url)
    
    # Paso 2: Obtener el código de autorización
    print("-" * 60)
    print("📋 PASO 2: Código de autorización")
    print("-" * 60)
    print("Después de autorizar, serás redirigido a una URL.")
    print("Copia la URL COMPLETA de la barra de direcciones y pégala aquí.")
    print()
    
    redirect_url = input("URL de redirección: ").strip()
    
    # Extraer el código de la URL
    try:
        parsed_url = urlparse(redirect_url)
        query_params = parse_qs(parsed_url.query)
        code = query_params.get('code', [None])[0]
        
        if not code:
            print("❌ No se encontró el código en la URL. Verifica que hayas copiado la URL completa.")
            return
        
        print(f"✅ Código obtenido: {code[:20]}...")
        
    except Exception as e:
        print(f"❌ Error procesando la URL: {e}")
        return
    
    # Paso 3: Intercambiar código por token (con code_verifier)
    print()
    print("-" * 60)
    print("📋 PASO 3: Obteniendo tokens...")
    print("-" * 60)
    
    token_data = exchange_code_for_token(code, code_verifier)
    
    if not token_data:
        print("❌ No se pudo obtener el token. Verifica tu configuración.")
        return
    
    print("✅ Token obtenido exitosamente")
    
    # Paso 4: Obtener información del usuario
    print()
    print("-" * 60)
    print("📋 PASO 4: Obteniendo información del usuario...")
    print("-" * 60)
    
    user_info = get_user_info(token_data['access_token'])
    
    if not user_info:
        print("❌ No se pudo obtener la información del usuario")
        return
    
    print(f"✅ Usuario: {user_info.get('nickname')} (ID: {user_info.get('id')})")
    
    # Paso 5: Guardar tokens
    print()
    print("-" * 60)
    print("📋 PASO 5: Guardando tokens...")
    print("-" * 60)
    
    save_tokens(token_data, user_info)
    
    # Resumen
    print()
    print("=" * 60)
    print("✅ AUTENTICACIÓN COMPLETADA")
    print("=" * 60)
    print()
    print("Ahora puedes usar la aplicación de Streamlit.")
    print("El token se refrescará automáticamente cuando expire.")
    print()

if __name__ == "__main__":
    main()
