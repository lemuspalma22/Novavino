"""
Script para importar productos corregidos desde CSV y actualizar la BD.
Incluye preview de cambios y confirmación antes de actualizar.
"""
import os
import django
import csv
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()

from inventario.models import Producto

print("\n" + "="*80)
print("IMPORTACION: PRODUCTOS CORREGIDOS")
print("="*80)

# Verificar que existe el archivo
csv_filename = "productos_revision_corregido.csv"
if not os.path.exists(csv_filename):
    print(f"\n[ERROR] No se encontro el archivo: {csv_filename}")
    print("\nAsegurate de:")
    print("  1. Haber editado el archivo 'productos_revision.csv'")
    print("  2. Haberlo guardado como 'productos_revision_corregido.csv'")
    print("  3. Que este en la misma carpeta que este script")
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
    print("\n[ADVERTENCIA] Hay errores en el CSV. Corrigelos antes de continuar.")

# Mostrar preview de cambios
if cambios:
    print("\n" + "="*80)
    print("PREVIEW DE CAMBIOS")
    print("="*80)
    
    for i, c in enumerate(cambios[:20], 1):
        diferencia = c['precio_nuevo'] - c['precio_actual']
        simbolo = "+" if diferencia > 0 else ""
        
        print(f"\n{i}. {c['nombre']} ({c['proveedor']})")
        print(f"   Precio:      ${c['precio_actual']:.2f} -> ${c['precio_nuevo']:.2f} ({simbolo}{diferencia:.2f})")
        print(f"   Transporte:  ${c['costo_transporte']:.2f}")
        print(f"   Base (nuevo): ${c['precio_sugerido_nuevo']:.2f}")
        print(f"   Validacion:  {c['costo_calculado_nuevo']:.2f} == {c['costo_transporte']:.2f} -> {'OK' if c['costo_calculado_nuevo'] == c['costo_transporte'] else 'ERROR'}")
    
    if len(cambios) > 20:
        print(f"\n... y {len(cambios) - 20} cambios mas")
    
    print("\n" + "="*80)
    print("RESUMEN")
    print("="*80)
    print(f"  Total cambios a aplicar: {len(cambios)}")
    
    # Calcular estadísticas
    incrementos = sum(1 for c in cambios if c['precio_nuevo'] > c['precio_actual'])
    decrementos = sum(1 for c in cambios if c['precio_nuevo'] < c['precio_actual'])
    
    print(f"  Incrementos de precio: {incrementos}")
    print(f"  Decrementos de precio: {decrementos}")
    
    # Validar que todos los cálculos sean correctos
    validaciones_ok = sum(1 for c in cambios if c['costo_calculado_nuevo'] == c['costo_transporte'])
    print(f"  Validaciones correctas: {validaciones_ok}/{len(cambios)}")
    
    if validaciones_ok < len(cambios):
        print("\n[ADVERTENCIA] Algunos productos tienen validaciones incorrectas.")
        print("Esto podria indicar un error en los datos del CSV.")
    
    # Pedir confirmación
    print("\n" + "="*80)
    respuesta = input("\nProceder con la actualizacion? (s/n): ").strip().lower()
    
    if respuesta == 's':
        print("\n[INFO] Actualizando productos...")
        print("-"*80)
        
        actualizados = 0
        errores_actualizacion = []
        
        for c in cambios:
            try:
                producto = c['producto']
                producto.precio_compra = c['precio_nuevo']
                producto.save()
                actualizados += 1
                print(f"  [OK] {producto.nombre} actualizado")
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
                logfile.write("\n")
        
        print(f"\n[OK] Log generado: {log_filename}")
        print("\n" + "="*80)
        print("COMPLETADO")
        print("="*80)
        print(f"\nSe actualizaron {actualizados} productos correctamente.")
        print("Los costos ahora son correctos para nuevas facturas.")
        print("\n" + "="*80 + "\n")
    
    else:
        print("\n[INFO] Actualizacion cancelada por el usuario.")
        print("No se realizaron cambios en la base de datos.")
        print("\n" + "="*80 + "\n")

else:
    print("\n[INFO] No hay cambios que aplicar.")
    print("Todos los precios en el CSV son iguales a los de la BD.")
    print("\n" + "="*80 + "\n")
