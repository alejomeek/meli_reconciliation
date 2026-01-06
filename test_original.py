# -*- coding: utf-8 -*-
"""
Script para testear el parser con RESUXDOC.XLS (archivo original)
"""

import sys
sys.path.append('.')

from services import tbc_parser

# Procesar archivo original
print("\n" + "="*60)
print("Procesando RESUXDOC.XLS (archivo original)")
print("="*60)

resultado = tbc_parser.procesar_archivo_tbc("RESUXDOC.XLS")

print(f"\n[RESULTADO]")
print(f"  Total lineas: {resultado['total_lineas']}")
print(f"  Remisiones unicas: {len(resultado['remisiones_unicas'])}")
print(f"  Facturas parseadas: {len(resultado['facturas'])}")

if resultado['facturas']:
    print(f"\n[PRIMERAS 5 FACTURAS]")
    for i, factura in enumerate(resultado['facturas'][:5], 1):
        print(f"  {i}. Remision: {factura['remision']}, Total: {factura['valor_total']}, Producto: {factura['producto_nombre']}")
else:
    print("\n[ERROR] No se parsearon facturas!")
