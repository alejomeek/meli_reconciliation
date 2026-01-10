# 🔄 Solución a Largo Plazo: Tokens Automáticos en Supabase

## 📋 Resumen

Esta solución guarda los tokens de Mercado Libre en **Supabase** en lugar de solo en Streamlit Secrets, permitiendo que se **refresquen automáticamente** sin intervención manual.

## ✅ Ventajas

- ✅ **Renovación automática**: Los tokens se refrescan automáticamente cuando expiran
- ✅ **Sin mantenimiento manual**: No necesitas actualizar Streamlit Secrets cada 6 horas
- ✅ **Persistencia**: Los tokens se guardan en la base de datos
- ✅ **Fallback inteligente**: Si Supabase falla, usa Streamlit Secrets o archivo local

## 🚀 Pasos de Implementación

### Paso 1: Crear la tabla en Supabase

1. Ve a tu proyecto en [supabase.com](https://supabase.com)
2. Ve a **SQL Editor**
3. Crea un **New query**
4. Copia y pega el contenido de `database/create_tokens_table.sql`
5. Haz clic en **Run**

Deberías ver el mensaje: "Success. No rows returned"

### Paso 2: Inicializar el token en Supabase (Local)

Ejecuta este comando en tu terminal **local**:

```bash
python3 init_token_supabase.py
```

Esto copiará tu token actual de `meli_tokens.json` a Supabase.

Deberías ver:

```
✅ Token guardado exitosamente en Supabase
🎉 ¡Listo! Ahora la aplicación usará Supabase para gestionar los tokens.
```

### Paso 3: Hacer commit y push

```bash
git add .
git commit -m "Implementar gestión automática de tokens en Supabase"
git push origin main
```

### Paso 4: Verificar en Streamlit Cloud

1. Espera 1-2 minutos a que Streamlit Cloud se actualice
2. Ve a tu app: https://controlmeli.streamlit.app
3. Haz clic en "📥 Sincronizar Órdenes ML"
4. Debería funcionar normalmente

## 🔍 Cómo Funciona

### Flujo de carga de tokens:

```
1. Intenta cargar desde Supabase (tabla ml_tokens)
   ↓ (si falla)
2. Intenta cargar desde Streamlit Secrets
   ↓ (si falla)
3. Intenta cargar desde archivo local (meli_tokens.json)
```

### Flujo de renovación automática:

```
1. Token expira (cada 6 horas)
   ↓
2. La app detecta el error 401
   ↓
3. Llama a refresh_access_token()
   ↓
4. Obtiene nuevo token de Mercado Libre
   ↓
5. Guarda el nuevo token en Supabase
   ↓
6. Reintenta la operación original
   ↓
7. ✅ Funciona sin intervención manual
```

## 📊 Verificar que funciona

### En Supabase:

1. Ve a **Table Editor** → **ml_tokens**
2. Deberías ver un registro con:
   - `access_token`: Tu token actual
   - `refresh_token`: Tu refresh token
   - `user_id`: 132688207
   - `nickname`: JUGANDOYEDUCANDO.COM

### En la aplicación:

1. Espera a que el token expire (6 horas)
2. Haz clic en "📥 Sincronizar Órdenes ML"
3. Debería funcionar automáticamente
4. Verifica en Supabase que el `updated_at` cambió

## 🛠️ Solución de Problemas

### Error: "No se encontró el token de ML"

**Causa:** La tabla no existe o está vacía

**Solución:**
1. Verifica que ejecutaste el SQL en Supabase
2. Ejecuta `python3 init_token_supabase.py` localmente

### Error: "Error cargando token desde Supabase"

**Causa:** Credenciales de Supabase incorrectas

**Solución:**
1. Verifica tu `.env` local
2. Verifica tus Streamlit Secrets en la nube

### El token no se refresca automáticamente

**Causa:** La función `refresh_access_token()` no se está llamando

**Solución:**
- Esto es normal, la renovación solo ocurre cuando hay un error 401
- La renovación automática está implementada en `get_orders()` (línea 133 de ml_api.py)

## 📝 Archivos Creados

- `services/ml_token_manager.py` - Gestión de tokens en Supabase
- `database/create_tokens_table.sql` - Script SQL para crear la tabla
- `init_token_supabase.py` - Script para inicializar el token
- `SOLUCION_TOKENS.md` - Esta guía

## 🔐 Seguridad

- ✅ Los tokens en Supabase están protegidos por RLS (Row Level Security)
- ✅ Solo tu aplicación puede acceder a ellos
- ✅ No se exponen en el código fuente
- ✅ No se suben a GitHub

## 🎯 Próximos Pasos

1. ✅ Ejecutar el SQL en Supabase
2. ✅ Ejecutar `python3 init_token_supabase.py`
3. ✅ Hacer commit y push
4. ✅ Verificar que funciona en Streamlit Cloud
5. ✅ ¡Olvidarte de actualizar tokens manualmente!

---

**¿Necesitas ayuda?** Consulta la sección de solución de problemas o revisa los logs de Streamlit Cloud.
