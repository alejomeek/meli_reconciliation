-- ============================================================================
-- SCHEMA: Sistema de Reconciliación Mercado Libre
-- Base de datos: Supabase (PostgreSQL)
-- ============================================================================

-- Tabla: ml_orders (Órdenes de Mercado Libre con remisión asignada)
CREATE TABLE IF NOT EXISTS ml_orders (
    id BIGSERIAL PRIMARY KEY,
    order_id TEXT NOT NULL UNIQUE,
    pack_id TEXT,
    shipping_id TEXT,
    fecha_orden TIMESTAMPTZ,
    total NUMERIC(10,2),
    productos JSONB,                         -- Array de productos en formato JSON
    buyer_name TEXT,                         -- Nombre del comprador
    buyer_nickname TEXT,                     -- Nickname del comprador
    remision TEXT,                           -- REMISIÓN asignada manualmente
    fecha_remision DATE,                     -- Fecha de asignación de remisión
    usuario TEXT,                            -- Usuario que asignó la remisión
    observaciones TEXT,                      -- Notas adicionales
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabla: tbc_facturas (Facturas del archivo TBC - RESUXDOC.XLS)
CREATE TABLE IF NOT EXISTS tbc_facturas (
    id BIGSERIAL PRIMARY KEY,
    evento TEXT,                             -- S66 (Remisión Mercancia A)
    remision TEXT NOT NULL,                  -- Número de remisión (ej: 12050)
    fecha DATE,                              -- Fecha de factura
    producto_codigo TEXT,                    -- SKU del producto
    producto_nombre TEXT,                    -- Descripción del producto
    valor_unitario NUMERIC(10,2),           -- VALUNI
    cantidad INTEGER,                        -- CANTID
    archivo_nombre TEXT,                     -- Nombre del archivo cargado
    fecha_carga TIMESTAMPTZ DEFAULT NOW()
);

-- Tabla: discrepancias (Log de errores encontrados en reconciliación)
CREATE TABLE IF NOT EXISTS discrepancias (
    id BIGSERIAL PRIMARY KEY,
    remision TEXT,
    order_id TEXT,
    tipo_error TEXT,                         -- valor_diferente, producto_faltante, cantidad_incorrecta, etc.
    detalle JSONB,                           -- Información detallada del error
    fecha_deteccion TIMESTAMPTZ DEFAULT NOW(),
    resuelto BOOLEAN DEFAULT FALSE,
    fecha_resolucion TIMESTAMPTZ,
    notas_resolucion TEXT
);

-- ============================================================================
-- ÍNDICES para mejorar performance de queries
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_ml_orders_remision ON ml_orders(remision);
CREATE INDEX IF NOT EXISTS idx_ml_orders_fecha ON ml_orders(fecha_orden);
CREATE INDEX IF NOT EXISTS idx_ml_orders_order_id ON ml_orders(order_id);

CREATE INDEX IF NOT EXISTS idx_tbc_facturas_remision ON tbc_facturas(remision);
CREATE INDEX IF NOT EXISTS idx_tbc_facturas_fecha ON tbc_facturas(fecha);

CREATE INDEX IF NOT EXISTS idx_discrepancias_remision ON discrepancias(remision);
CREATE INDEX IF NOT EXISTS idx_discrepancias_resuelto ON discrepancias(resuelto);

-- ============================================================================
-- TRIGGER: Actualizar updated_at automáticamente
-- ============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_ml_orders_updated_at 
    BEFORE UPDATE ON ml_orders
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- COMENTARIOS en las tablas (documentación)
-- ============================================================================

COMMENT ON TABLE ml_orders IS 'Órdenes de Mercado Libre Flex con remisiones asignadas';
COMMENT ON TABLE tbc_facturas IS 'Facturas del sistema TBC importadas desde RESUXDOC.XLS';
COMMENT ON TABLE discrepancias IS 'Registro de discrepancias encontradas durante reconciliación';

COMMENT ON COLUMN ml_orders.order_id IS 'ID único de la orden en Mercado Libre';
COMMENT ON COLUMN ml_orders.remision IS 'Número de remisión del sistema TBC';
COMMENT ON COLUMN ml_orders.productos IS 'Array JSON con detalles de productos';

-- ============================================================================
-- FIN DEL SCHEMA
-- ============================================================================
