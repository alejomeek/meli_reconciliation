# 🚀 Guía de Configuración Inicial

## Resumen del Problema

El error **"❌ No se encontró el token de ML"** ocurre porque faltan dos cosas:

1. **Archivo `.env`** con las credenciales de configuración
2. **Archivo `meli_tokens.json`** con el token de autenticación de Mercado Libre

## Solución Paso a Paso

### 📋 Paso 1: Crear el archivo `.env`

1. Copia el archivo de ejemplo:
   ```bash
   cp .env.example .env
   ```

2. Abre el archivo `.env` y completa los valores:

   ```env
   # SUPABASE (tu base de datos)
   SUPABASE_URL=https://tu-proyecto.supabase.co
   SUPABASE_KEY=tu_clave_de_supabase
   
   # MERCADO LIBRE
   ML_APP_ID=1234567890123456
   ML_CLIENT_SECRET=AbCdEfGhIjKlMnOpQrStUvWxYz
   ML_REDIRECT_URI=https://www.google.com
   ML_SITE_ID=MCO
   ```

   > **¿Dónde obtengo estos valores?**
   > - **Supabase:** Ve a tu proyecto en [supabase.com](https://supabase.com) → Settings → API
   > - **Mercado Libre:** Crea una app en [developers.mercadolibre.com.co](https://developers.mercadolibre.com.co/)

### 🔐 Paso 2: Autenticarse con Mercado Libre

Una vez que tengas el archivo `.env` configurado, ejecuta:

```bash
python meli_auth.py
```

Este script:
1. Abrirá tu navegador para que autorices la aplicación
2. Te pedirá que copies la URL de redirección
3. Generará el archivo `meli_tokens.json` automáticamente

**Sigue las instrucciones en pantalla** y consulta [AUTENTICACION_ML.md](./AUTENTICACION_ML.md) para más detalles.

### ✅ Paso 3: Verificar la instalación

Ejecuta la aplicación:

```bash
streamlit run app.py
```

Ahora el botón **"📥 Sincronizar Órdenes ML"** debería funcionar correctamente.

## 📚 Documentación Adicional

- [AUTENTICACION_ML.md](./AUTENTICACION_ML.md) - Guía detallada de autenticación
- [README.md](./README.md) - Documentación general del proyecto
- [DEPLOYMENT.md](./DEPLOYMENT.md) - Guía de despliegue

## ❓ Preguntas Frecuentes

### ¿Necesito crear una aplicación en Mercado Libre?

Sí, si aún no tienes una. Ve a [developers.mercadolibre.com.co](https://developers.mercadolibre.com.co/) y:

1. Inicia sesión con tu cuenta de vendedor
2. Ve a "Mis aplicaciones" → "Crear nueva aplicación"
3. Completa el formulario:
   - **Nombre:** Reconciliación ML-TBC (o el que prefieras)
   - **Descripción:** Sistema de reconciliación de órdenes
   - **Redirect URI:** `https://www.google.com`
   - **Scopes:** Selecciona `read` y `write` para órdenes
4. Guarda el `App ID` y `Client Secret` en tu `.env`

### ¿Cada cuánto debo autenticarme?

El token se renueva automáticamente. Solo necesitas ejecutar `meli_auth.py` una vez, a menos que:
- Elimines el archivo `meli_tokens.json`
- Pases 6 meses sin usar la aplicación
- Revokes el acceso desde tu cuenta de Mercado Libre

### ¿Qué hago si el token expira?

La aplicación lo renovará automáticamente. Si por alguna razón no funciona, simplemente ejecuta `python meli_auth.py` de nuevo.

## 🆘 Soporte

Si sigues teniendo problemas:

1. Verifica que todos los valores en `.env` sean correctos
2. Asegúrate de que tu cuenta de Mercado Libre tenga permisos de vendedor
3. Revisa que la `ML_REDIRECT_URI` en `.env` coincida con la configurada en tu app de ML
4. Consulta los logs de error para más detalles
