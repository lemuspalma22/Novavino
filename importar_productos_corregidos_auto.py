"""
Script para importar productos corregidos desde CSV y actualizar la BD.
Versión con confirmación automática.
"""
import os
import django
import csv
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()

from inventario.models import Producto

print("\n" + "="*80)
print("IMPORTACION: PRODUCTOS CORREGIDOS (AUTO-CONFIRMACION)")
print("="*80)

# Verificar que existe el archivo
csv_filename = "productos_revision_corregido.csv"
if not os.path.exists(csv_filename):
    print(f"\n[ERROR] No se encontro el archivo: {csv_filename}")
    print("\n" + "="*80 + "\n")
    exit(1)

print(f"\n[OK] Archivo encontrado: {csv_filename}")
print("Leyendo datos...")
print("-"*80)

# Leer CSV
cambios = []
errores = []

with open(csv_filename, 'r', encoding='utf-8-sig') as csvfile:
    reader = csv.DictReader(csvfile)
    
    for row in reader:
        try:
            producto_id = int(row['id'])
            precio_nuevo = Decimal(str(row['precio_actual']))
            
            # Validar que el precio sea positivo
            if precio_nuevo < 0:
                errores.append({
                    'id': producto_id,
                    'nombre': row['nombre'],
                    'error': f'Precio negativo: {precio_nuevo}'
                })
                continue
            
            # Obtener producto de BD
            try:
                producto = Producto.objects.get(id=producto_id)
            except Producto.DoesNotExist:
                errores.append({
                    'id': producto_id,
                    'nombre': row['nombre'],
                    'error': 'Producto no existe en BD'
                })
                continue
            
            precio_actual = producto.precio_compra or Decimal("0.00")
            
            # Solo agregar si hay cambio
            if precio_actual != precio_nuevo:
                costo_transporte = producto.costo_transporte or Decimal("0.00")
                precio_sugerido_nuevo = precio_nuevo - costo_transporte
                costo_calculado_nuevo = precio_nuevo - precio_sugerido_nuevo
                
                cambios.append({
                    'id': producto_id,
                    'producto': producto,
                    'nombre': producto.nombre,
                    'proveedor': producto.proveedor.nombre,
                    'precio_actual': precio_actual,
                    'precio_nuevo': precio_nuevo,
                    'costo_transporte': costo_transporte,
                    'precio_sugerido_nuevo': precio_sugerido_nuevo,
                    'costo_calculado_nuevo': costo_calculado_nuevo
                })
        
        except (ValueError, KeyError) as e:
            errores.append({
                'id': row.get('id', 'N/A'),
                'nombre': row.get('nombre', 'N/A'),
                'error': f'Error al procesar fila: {str(e)}'
            })

print(f"\n[INFO] Datos procesados:")
print(f"  - Cambios detectados: {len(cambios)}")
print(f"  - Errores encontrados: {len(errores)}")

# Mostrar errores si existen
if errores:
    print("\n" + "="*80)
    print("ERRORES ENCONTRADOS")
    print("="*80)
    for e in errores[:10]:
        print(f"  ID {e['id']} - {e['nombre']}")
        print(f"    Error: {e['error']}")
    if len(errores) > 10:
        print(f"  ... y {len(errores) - 10} errores mas")

# Aplicar cambios
if cambios:
    print("\n" + "="*80)
    print("APLICANDO CAMBIOS")
    print("="*80)
    
    actualizados = 0
    errores_actualizacion = []
    
    for c in cambios:
        try:
            producto = c['producto']
            producto.precio_compra = c['precio_nuevo']
            producto.save()
            actualizados += 1
            
            diferencia = c['precio_nuevo'] - c['precio_actual']
            simbolo = "+" if diferencia > 0 else ""
            print(f"  [OK] {producto.nombre}: ${c['precio_actual']:.2f} -> ${c['precio_nuevo']:.2f} ({simbolo}{diferencia:.2f})")
        except Exception as e:
            errores_actualizacion.append({
                'nombre': c['nombre'],
                'error': str(e)
            })
            print(f"  [ERROR] {c['nombre']}: {str(e)}")
    
    print("\n" + "="*80)
    print("RESULTADOS")
    print("="*80)
    print(f"  Actualizados: {actualizados}")
    print(f"  Errores: {len(errores_actualizacion)}")
    
    if errores_actualizacion:
        print("\nErrores durante actualizacion:")
        for e in errores_actualizacion:
            print(f"  - {e['nombre']}: {e['error']}")
    
    # Generar log
    log_filename = "productos_actualizacion_log.txt"
    with open(log_filename, 'w', encoding='utf-8') as logfile:
        logfile.write("="*80 + "\n")
        logfile.write("LOG DE ACTUALIZACION DE PRODUCTOS\n")
        logfile.write("="*80 + "\n\n")
        
        for c in cambios:
            logfile.write(f"{c['nombre']} (ID: {c['id']})\n")
            logfile.write(f"  Proveedor: {c['proveedor']}\n")
            logfile.write(f"  Precio anterior: ${c['precio_actual']:.2f}\n")
            logfile.write(f"  Precio nuevo: ${c['precio_nuevo']:.2f}\n")
            logfile.write(f"  Diferencia: ${c['precio_nuevo'] - c['precio_actual']:.2f}\n")
            logfile.write(f"  Costo transporte: ${c['costo_transporte']:.2f}\n")
            logfile.write(f"  Costo total (precio + transporte): ${c['precio_nuevo'] + c['costo_transporte']:.2f}\n")
            logfile.write("\n")
    
    print(f"\n[OK] Log generado: {log_filename}")
    print("\n" + "="*80)
    print("COMPLETADO")
    print("="*80)
    print(f"\nSe actualizaron {actualizados} productos correctamente.")
    print("\nAhora:")
    print("  - Los precios base (sin transporte) estan corregidos")
    print("  - Al crear nuevas facturas, el sistema sumara:")
    print("    * Precio base (corregido)")
    print("    * + Costo transporte")
    print("    * = Costo total correcto")
    print("\n  - Las facturas anteriores NO se modifican (como esperado)")
    print("\n" + "="*80 + "\n")

else:
    print("\n[INFO] No hay cambios que aplicar.")
    print("Todos los precios en el CSV son iguales a los de la BD.")
    print("\n" + "="*80 + "\n")
