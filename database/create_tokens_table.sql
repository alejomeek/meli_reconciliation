-- Tabla para guardar tokens de Mercado Libre
-- Ejecuta este SQL en Supabase SQL Editor

CREATE TABLE IF NOT EXISTS ml_tokens (
    id SERIAL PRIMARY KEY,
    access_token TEXT NOT NULL,
    refresh_token TEXT NOT NULL,
    user_id BIGINT NOT NULL,
    nickname TEXT,
    expires_in INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índice para búsqueda rápida por user_id
CREATE INDEX IF NOT EXISTS idx_ml_tokens_user_id ON ml_tokens(user_id);

-- Solo queremos un registro (el más reciente)
-- Podemos usar una función para asegurar esto
CREATE OR REPLACE FUNCTION update_ml_token(
    p_access_token TEXT,
    p_refresh_token TEXT,
    p_user_id BIGINT,
    p_nickname TEXT,
    p_expires_in INTEGER
) RETURNS void AS $$
BEGIN
    -- Eliminar tokens antiguos
    DELETE FROM ml_tokens;
    
    -- Insertar el nuevo token
    INSERT INTO ml_tokens (access_token, refresh_token, user_id, nickname, expires_in)
    VALUES (p_access_token, p_refresh_token, p_user_id, p_nickname, p_expires_in);
END;
$$ LANGUAGE plpgsql;

-- Comentarios
COMMENT ON TABLE ml_tokens IS 'Almacena los tokens de autenticación de Mercado Libre';
COMMENT ON COLUMN ml_tokens.access_token IS 'Token de acceso actual';
COMMENT ON COLUMN ml_tokens.refresh_token IS 'Token para renovar el access_token';
COMMENT ON COLUMN ml_tokens.user_id IS 'ID del usuario/vendedor en Mercado Libre';
