"""
Script para exportar productos a CSV para revisión manual de precios.
Incluye validación automática de costos de transporte.
"""
import os
import django
import csv
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()

from inventario.models import Producto

print("\n" + "="*80)
print("EXPORTACION: PRODUCTOS PARA REVISION DE PRECIOS")
print("="*80)

# Obtener productos de VB y SV
productos = Producto.objects.select_related('proveedor').all()

# Filtrar solo VB y SV
vb_sdv_productos = []
for p in productos:
    proveedor_nombre = p.proveedor.nombre.lower()
    if any(keyword in proveedor_nombre for keyword in ['vieja bodega', 'secretos de la vid', 'secretos']):
        vb_sdv_productos.append(p)

print(f"\nProductos encontrados:")
print(f"  - Total productos en BD: {productos.count()}")
print(f"  - Vieja Bodega + Secretos de la Vid: {len(vb_sdv_productos)}")

# Crear CSV
csv_filename = "productos_revision.csv"
print(f"\nGenerando: {csv_filename}")
print("-"*80)

with open(csv_filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
    fieldnames = [
        'id',
        'nombre',
        'precio_actual',
        'costo_transporte',
        'precio_sugerido',
        'costo_transporte_calculado',
        'proveedor',
        'requiere_correccion'
    ]
    
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    
    requieren_correccion = 0
    ok_count = 0
    
    # Ordenar: primero los que requieren corrección
    productos_sorted = sorted(vb_sdv_productos, key=lambda p: (
        # Primero los que requieren corrección (True < False en Python)
        not (abs((p.precio_compra or 0) - ((p.precio_compra or 0) - (p.costo_transporte or 0))) == (p.costo_transporte or 0)),
        p.proveedor.nombre,
        p.nombre
    ))
    
    for p in productos_sorted:
        precio_actual = p.precio_compra or Decimal("0.00")
        costo_transporte = p.costo_transporte or Decimal("0.00")
        precio_sugerido = precio_actual - costo_transporte
        costo_transporte_calculado = precio_actual - precio_sugerido  # Siempre igual a costo_transporte en este caso
        
        # Validar si requiere corrección (más sofisticado)
        # Un producto requiere corrección si el costo_transporte_calculado no coincide
        # Pero como precio_sugerido = precio_actual - costo_transporte,
        # entonces costo_transporte_calculado siempre será igual a costo_transporte
        # 
        # La verdadera validación es: si el precio ya incluía transporte,
        # entonces al restarle el transporte debería dar un precio "razonable"
        # Pero esto es subjetivo, así que mejor validamos con tolerancia
        
        # Estrategia: Si el precio_sugerido es negativo o muy pequeño, algo está mal
        requiere_correccion_bool = False
        if precio_sugerido < 0:
            requiere_correccion_bool = True
        
        # También: si el costo de transporte es 0 pero el proveedor tiene costo
        if costo_transporte == 0 and p.proveedor.costo_transporte_unitario > 0:
            requiere_correccion_bool = True
        
        if requiere_correccion_bool:
            requieren_correccion += 1
        else:
            ok_count += 1
        
        writer.writerow({
            'id': p.id,
            'nombre': p.nombre,
            'precio_actual': float(precio_actual),
            'costo_transporte': float(costo_transporte),
            'precio_sugerido': float(precio_sugerido),
            'costo_transporte_calculado': float(costo_transporte_calculado),
            'proveedor': p.proveedor.nombre,
            'requiere_correccion': 'TRUE' if requiere_correccion_bool else 'FALSE'
        })

print(f"\n[OK] CSV generado: {csv_filename}")
print("-"*80)
print(f"  Total productos: {len(vb_sdv_productos)}")
print(f"  Requieren revision: {requieren_correccion}")
print(f"  Parecen correctos: {ok_count}")

print("\n" + "="*80)
print("INSTRUCCIONES")
print("="*80)
print("""
1. Abre el archivo 'productos_revision.csv' en Excel

2. Filtra por 'requiere_correccion = TRUE' para ver solo los problematicos

3. Para cada producto:
   - Si 'precio_actual' ya incluye transporte duplicado:
     * Resta el transporte: nuevo_precio = precio_actual - costo_transporte
     * Actualiza 'precio_actual' con el nuevo valor
   
   - Si 'precio_actual' NO incluye transporte:
     * Dejalo como esta

4. Guarda el archivo como: 'productos_revision_corregido.csv'

5. Ejecuta: python importar_productos_corregidos.py

NOTA: La columna 'precio_sugerido' es solo referencia.
      La columna 'costo_transporte_calculado' = precio_actual - precio_sugerido
      
      Si corriges 'precio_actual', al importar se recalculara todo.
""")
print("="*80 + "\n")
