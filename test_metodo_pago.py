"""
Script para probar la extracción del método de pago (PUE/PPD) en facturas de ventas.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()

from ventas.extractors.novavino import extraer_factura_novavino

print("\n" + "="*80)
print("PRUEBA: EXTRACCION DE METODO DE PAGO")
print("="*80)

# Texto de prueba con método de pago PUE
texto_pue = """
Factura 12345
FECHA Y HORA DE EMISIÓN DE CFDI
15-12-2025 10:30:00

CLIENTE
PRUEBA S.A. DE C.V.

Método de pago: PUE

CONCEPTOS
Cantidad Unidad Producto
2.00 BOT Vino Tinto 750ml
Precio Unitario $500.00

TOTAL
$1,000.00
"""

# Texto de prueba con método de pago PPD
texto_ppd = """
Factura 67890
FECHA Y HORA DE EMISIÓN DE CFDI
15-12-2025 11:00:00

CLIENTE
COMERCIAL XYZ

Método de pago: PPD

CONCEPTOS
Cantidad Unidad Producto
3.00 PZA Vino Blanco
Precio Unitario $400.00

TOTAL
$1,200.00
"""

print("\n[1/2] Probando extracción con método PUE...")
print("-"*80)
data_pue = extraer_factura_novavino(texto_pue)
print(f"  Folio: {data_pue['folio']}")
print(f"  Cliente: {data_pue['cliente']}")
print(f"  Método de pago: {data_pue['metodo_pago']}")
print(f"  Total: ${data_pue['total']}")

if data_pue['metodo_pago'] == 'PUE':
    print("  [OK] Método de pago PUE detectado correctamente")
else:
    print(f"  [ERROR] Se esperaba 'PUE', se obtuvo: {data_pue['metodo_pago']}")

print("\n[2/2] Probando extracción con método PPD...")
print("-"*80)
data_ppd = extraer_factura_novavino(texto_ppd)
print(f"  Folio: {data_ppd['folio']}")
print(f"  Cliente: {data_ppd['cliente']}")
print(f"  Método de pago: {data_ppd['metodo_pago']}")
print(f"  Total: ${data_ppd['total']}")

if data_ppd['metodo_pago'] == 'PPD':
    print("  [OK] Método de pago PPD detectado correctamente")
else:
    print(f"  [ERROR] Se esperaba 'PPD', se obtuvo: {data_ppd['metodo_pago']}")

print("\n" + "="*80)
print("INTERPRETACION")
print("="*80)
print("\n PUE (Pago en una sola exhibición):")
print("  - Se paga en el momento de la facturación")
print("  - Afecta el flujo de caja del mes actual")
print("  - Contablemente se registra como ingreso inmediato")

print("\n PPD (Pago en parcialidades o diferido):")
print("  - Se paga después, en una o varias parcialidades")
print("  - Puede afectar flujo de caja de meses futuros")
print("  - Contablemente se registra como cuenta por cobrar")

print("\n" + "="*80)
print("CAMBIOS EN EL SISTEMA")
print("="*80)
print("\n1. Modelo Factura:")
print("   - Nuevo campo: metodo_pago (PUE/PPD)")
print("   - Migración aplicada: 0007_factura_metodo_pago")

print("\n2. Extractor (ventas/extractors/novavino.py):")
print("   - Detecta 'Método de pago: PUE' o 'PPD' en el PDF")
print("   - Incluye en data['metodo_pago']")

print("\n3. Registrar Venta (ventas/utils/registrar_venta.py):")
print("   - Guarda metodo_pago al crear/actualizar factura")

print("\n4. Admin de Facturas:")
print("   - Nueva columna 'Método de Pago' en la lista")
print("   - Filtro por método de pago")
print("   - Botón 'Ver Corte Semanal' movido arriba junto a Drive")
print("   - Campo 'Método de Pago' en el formulario de edición")

print("\n" + "="*80)
print("COMPLETADO")
print("="*80 + "\n")
