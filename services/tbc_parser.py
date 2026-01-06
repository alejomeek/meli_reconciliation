"""
Parser para archivos RESUXDOC.XLS del sistema TBC
Extrae información de facturas de Mercado Libre Flex
"""

import pandas as pd
from typing import List, Dict, Any
from datetime import datetime
import re

# ============================================================================
# PARSER DEL ARCHIVO TBC
# ============================================================================

def parse_resuxdoc_xls(file_path: str, evento_filtro: str = "S66") -> List[Dict[str, Any]]:
    """
    Parsea el archivo RESUXDOC.XLS y extrae las facturas
    
    Estructura del archivo RESUXDOC.XLS:
    - col_0: EVENTO (S66)
    - col_2: PRODUC (código producto)
    - col_3: DDMMAA (fecha DD-Mmm-AA)
    - col_4: DETALL (nombre producto)
    - col_5: UNIMED (unidad)
    - col_6: CANTID (cantidad)
    - col_7: VALUNI (valor unitario)
    - col_8: VALTOT (valor total) ⭐ USAR ESTE
    - col_12: CONSEC (remisión - número) ⭐ USAR ESTE
    - col_14: NROFAC (remisión con "RM")
    
    Args:
        file_path: Ruta al archivo RESUXDOC.XLS
        evento_filtro: Tipo de evento a filtrar (default: S66 - Mercado Libre Flex)
    
    Returns:
        Lista de diccionarios con información de cada línea de factura
    """
    
    facturas = []
    
    try:
        # Leer archivo Excel con pandas
        df = pd.read_excel(file_path, sheet_name=0, header=None, engine='xlrd')
        
        print(f"[INFO] Archivo leido: {len(df)} filas, {len(df.columns)} columnas")
        
        # La primera fila (índice 0) contiene los encabezados, empezar desde la fila 1
        for idx in range(1, len(df)):
            row = df.iloc[idx]
            
            # Verificar que sea una fila con evento S66
            evento = str(row[0]).strip() if pd.notna(row[0]) else ''
            if evento != evento_filtro:
                continue
            
            try:
                # Extraer datos usando las columnas específicas
                
                # col_12: CONSEC - Remisión (número de 4 o 5 dígitos)
                remision = None
                if pd.notna(row[12]):
                    remision_str = str(row[12]).strip()
                    # Limpiar espacios y extraer solo dígitos
                    remision = ''.join(filter(str.isdigit, remision_str))
                    if len(remision) not in [4, 5]:
                        # Intentar con col_14 (NROFAC)
                        if pd.notna(row[14]):
                            nrofac = str(row[14]).strip()
                            match = re.search(r'(\d{4,5})', nrofac)
                            if match:
                                remision = match.group(1)
                
                if not remision or len(remision) not in [4, 5]:
                    print(f"[WARN] Fila {idx}: No se pudo extraer remision valida")
                    continue
                
                # col_3: DDMMAA - Fecha
                fecha = None
                if pd.notna(row[3]):
                    fecha_str = str(row[3]).strip()
                    fecha = parse_tbc_fecha(fecha_str)
                
                # col_2: PRODUC - Código de producto
                producto_codigo = str(row[2]).strip() if pd.notna(row[2]) else 'UNKNOWN'
                
                # col_4: DETALL - Nombre de producto
                producto_nombre = str(row[4]).strip() if pd.notna(row[4]) else 'Producto sin nombre'
                
                # col_5: UNIMED - Unidad
                unidad = str(row[5]).strip() if pd.notna(row[5]) else 'UN'
                
                # col_6: CANTID - Cantidad
                cantidad = 1
                if pd.notna(row[6]):
                    try:
                        cantidad = float(str(row[6]).strip())
                    except:
                        cantidad = 1
                
                # col_7: VALUNI - Valor unitario
                valor_unitario = 0
                if pd.notna(row[7]):
                    try:
                        valor_unitario = float(str(row[7]).strip())
                    except:
                        valor_unitario = 0
                
                # col_8: VALTOT - Valor total ⭐ USAR ESTE DIRECTAMENTE
                valor_total = 0
                if pd.notna(row[8]):
                    try:
                        valor_total = float(str(row[8]).strip())
                    except:
                        # Si falla, calcular manualmente
                        valor_total = cantidad * valor_unitario
                
                # Crear registro de factura
                factura = {
                    'evento': evento,
                    'nombre_evento': str(row[1]).strip() if pd.notna(row[1]) else 'Remision Mercancia A',
                    'remision': remision,
                    'fecha': fecha,
                    'producto_codigo': producto_codigo,
                    'producto_nombre': producto_nombre,
                    'unidad': unidad,
                    'cantidad': cantidad,
                    'valor_unitario': valor_unitario,
                    'valor_total': valor_total
                }
                
                facturas.append(factura)
                
            except Exception as e:
                print(f"[WARN] Error parseando fila {idx}: {e}")
                continue
        
        print(f"\n[OK] Total facturas parseadas: {len(facturas)}")
        return facturas
        
    except Exception as e:
        print(f"[ERROR] Error parseando archivo: {e}")
        import traceback
        traceback.print_exc()
        return []


def parse_tbc_fecha(fecha_str: str) -> str:
    """
    Parsea fecha del formato TBC (DD-Mmm-AA) a YYYY-MM-DD
    Ejemplo: "04-Ene-26" -> "2026-01-04"
    """
    
    if not fecha_str:
        return None
    
    try:
        # Mapeo de meses en español
        meses = {
            'Ene': '01', 'Feb': '02', 'Mar': '03', 'Abr': '04',
            'May': '05', 'Jun': '06', 'Jul': '07', 'Ago': '08',
            'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dic': '12'
        }
        
        # Separar componentes
        partes = fecha_str.split('-')
        if len(partes) != 3:
            return None
        
        dia = partes[0].zfill(2)
        mes_texto = partes[1]
        año = partes[2]
        
        # Convertir mes
        mes = meses.get(mes_texto, None)
        if not mes:
            return None
        
        # Convertir año (asumiendo 20XX)
        año_completo = f"20{año}"
        
        return f"{año_completo}-{mes}-{dia}"
        
    except Exception:
        return None


def parse_tbc_numero(numero_str: str) -> float:
    """
    Parsea números del formato TBC
    Maneja bytes especiales y formatos numéricos
    """
    
    if not numero_str:
        return None
    
    try:
        # Remover caracteres especiales y convertir
        # TBC usa algunos bytes especiales para números
        numero_limpio = numero_str.replace('\\x', '').replace('?', '').strip()
        
        # Si es un número simple, convertirlo
        if numero_limpio.replace('.', '').replace(',', '').isdigit():
            return float(numero_limpio.replace(',', ''))
        
        # Si contiene bytes hex, intentar decodificar
        # Por ahora retornar None para casos complejos
        return None
        
    except Exception:
        return None


# ============================================================================
# AGRUPAR FACTURAS POR REMISIÓN
# ============================================================================

def agrupar_por_remision(facturas: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Agrupa las líneas de factura por número de remisión
    
    Returns:
        Diccionario {remision: [lista de productos]}
    """
    
    agrupadas = {}
    
    for factura in facturas:
        remision = factura['remision']
        
        if remision not in agrupadas:
            agrupadas[remision] = []
        
        agrupadas[remision].append(factura)
    
    return agrupadas


def calcular_total_remision(facturas_remision: List[Dict[str, Any]]) -> float:
    """
    Calcula el total de una remisión sumando todos sus productos
    """
    
    total = 0
    
    for factura in facturas_remision:
        if factura.get('valor_total'):
            total += factura['valor_total']
    
    return total


# ============================================================================
# FUNCIÓN PRINCIPAL DE PARSEO
# ============================================================================

def procesar_archivo_tbc(file_path: str) -> Dict[str, Any]:
    """
    Procesa el archivo RESUXDOC.XLS completo y retorna datos estructurados
    
    Returns:
        {
            'facturas': Lista de todas las facturas,
            'agrupadas': Diccionario agrupado por remisión,
            'total_lineas': Cantidad total de líneas,
            'remisiones_unicas': Set de remisiones únicas
        }
    """
    
    facturas = parse_resuxdoc_xls(file_path)
    agrupadas = agrupar_por_remision(facturas)
    
    return {
        'facturas': facturas,
        'agrupadas': agrupadas,
        'total_lineas': len(facturas),
        'remisiones_unicas': set([f['remision'] for f in facturas])
    }
