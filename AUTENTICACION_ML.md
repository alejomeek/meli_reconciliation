# 🔐 Guía de Autenticación con Mercado Libre

## Problema
Si ves el error: **"❌ No se encontró el token de ML. Ejecuta primero meli_auth_test.py"**, significa que falta el archivo `meli_tokens.json` con tus credenciales de autenticación.

## Solución

### Paso 1: Verificar configuración

Asegúrate de que tu archivo `.env` tenga las siguientes variables configuradas:

```env
ML_APP_ID=tu_app_id
ML_CLIENT_SECRET=tu_client_secret
ML_REDIRECT_URI=https://www.google.com
ML_SITE_ID=MCO
```

> **Nota:** Si no tienes estos valores, debes crear una aplicación en el [Portal de Desarrolladores de Mercado Libre](https://developers.mercadolibre.com.co/).

### Paso 2: Ejecutar el script de autenticación

Ejecuta el siguiente comando en tu terminal:

```bash
python meli_auth.py
```

### Paso 3: Seguir las instrucciones

El script te guiará a través de los siguientes pasos:

1. **Se abrirá tu navegador** con la página de autorización de Mercado Libre
2. **Inicia sesión** con tu cuenta de Mercado Libre (la cuenta del vendedor)
3. **Autoriza la aplicación** haciendo clic en "Permitir"
4. **Copia la URL completa** de la página a la que fuiste redirigido (generalmente Google)
5. **Pega la URL** en la terminal cuando se te solicite

### Paso 4: Verificar

Si todo salió bien, verás un mensaje como:

```
✅ AUTENTICACIÓN COMPLETADA
```

Y se habrá creado el archivo `meli_tokens.json` en tu proyecto.

### Paso 5: Usar la aplicación

Ahora puedes ejecutar tu aplicación de Streamlit normalmente:

```bash
streamlit run app.py
```

Y el botón **"📥 Sincronizar Órdenes ML"** funcionará correctamente.

## Renovación automática del token

El token de acceso expira cada 6 horas, pero la aplicación lo renovará automáticamente usando el `refresh_token`. No necesitas volver a ejecutar el script de autenticación a menos que:

- Elimines el archivo `meli_tokens.json`
- El `refresh_token` expire (esto ocurre después de 6 meses de inactividad)
- Revokes el acceso desde tu cuenta de Mercado Libre

## Problemas comunes

### Error: "No se encontró el código en la URL"
- Asegúrate de copiar la URL **completa** de la barra de direcciones
- La URL debe contener `?code=TG-...`

### Error: "Error obteniendo token"
- Verifica que tu `ML_APP_ID` y `ML_CLIENT_SECRET` sean correctos
- Asegúrate de que la `ML_REDIRECT_URI` en tu `.env` coincida con la configurada en tu aplicación de Mercado Libre

### Error: "Faltan las siguientes variables de entorno"
- Verifica que tu archivo `.env` esté en la raíz del proyecto
- Asegúrate de que todas las variables estén configuradas correctamente

## Seguridad

⚠️ **IMPORTANTE:** El archivo `meli_tokens.json` contiene información sensible. 

- **NO** lo compartas con nadie
- **NO** lo subas a GitHub (ya está en `.gitignore`)
- Si crees que tu token fue comprometido, revoca el acceso desde tu cuenta de Mercado Libre y genera uno nuevo
