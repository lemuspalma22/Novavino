# actualizar_inventario_completo.py
"""
Script completo para actualizar inventario:
1. Importar stock desde CSV
2. Borrar productos especificados
3. Agregar productos nuevos
"""
import os
import django
import csv
from datetime import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()

from inventario.models import Producto
from compras.models import Proveedor
from django.db import transaction
from decimal import Decimal


def importar_stock_desde_csv(filename):
    """Importa el stock físico desde CSV."""
    print("\n" + "="*80)
    print("PASO 1: IMPORTAR STOCK DESDE CSV")
    print("="*80)
    
    if not os.path.exists(filename):
        print(f"[ERROR] No se encontró el archivo: {filename}")
        return None
    
    print(f"[INFO] Leyendo archivo: {filename}")
    
    actualizados = 0
    sin_cambios = 0
    errores = []
    detalles = []
    
    with open(filename, 'r', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile)
        
        with transaction.atomic():
            for row_num, row in enumerate(reader, start=2):
                try:
                    producto_id = row['ID'].strip()
                    stock_fisico_str = row['Stock Físico'].strip()
                    
                    if not producto_id or not stock_fisico_str:
                        sin_cambios += 1
                        continue
                    
                    producto_id = int(producto_id)
                    stock_fisico = int(stock_fisico_str)
                    
                    try:
                        producto = Producto.objects.get(id=producto_id)
                    except Producto.DoesNotExist:
                        errores.append(f"Fila {row_num}: Producto ID {producto_id} no existe")
                        continue
                    
                    stock_anterior = producto.stock
                    producto.stock = stock_fisico
                    producto.save(update_fields=['stock'])
                    
                    actualizados += 1
                    diferencia = stock_fisico - stock_anterior
                    
                    detalles.append({
                        'id': producto.id,
                        'nombre': producto.nombre,
                        'stock_anterior': stock_anterior,
                        'stock_nuevo': stock_fisico,
                        'diferencia': diferencia
                    })
                    
                except Exception as e:
                    errores.append(f"Fila {row_num}: {str(e)}")
    
    print(f"[OK] Productos actualizados: {actualizados}")
    print(f"[INFO] Productos sin cambios: {sin_cambios}")
    if errores:
        print(f"[WARNING] Errores: {len(errores)}")
        for error in errores[:5]:
            print(f"  - {error}")
    
    # Mostrar cambios significativos
    if detalles:
        print(f"\n[INFO] Cambios mas significativos:")
        cambios_ordenados = sorted(detalles, key=lambda x: abs(x['diferencia']), reverse=True)
        for detalle in cambios_ordenados[:10]:
            signo = "+" if detalle['diferencia'] > 0 else ""
            print(f"  - {detalle['nombre']}: {detalle['stock_anterior']} -> {detalle['stock_nuevo']} ({signo}{detalle['diferencia']})")
    
    return {
        'actualizados': actualizados,
        'sin_cambios': sin_cambios,
        'errores': errores,
        'detalles': detalles
    }


def borrar_productos(ids_a_borrar):
    """Borra productos especificados."""
    print("\n" + "="*80)
    print("PASO 2: BORRAR PRODUCTOS ESPECIFICADOS")
    print("="*80)
    
    borrados = []
    no_encontrados = []
    
    with transaction.atomic():
        for producto_id in ids_a_borrar:
            try:
                producto = Producto.objects.get(id=producto_id)
                nombre = producto.nombre
                producto.delete()
                borrados.append((producto_id, nombre))
                print(f"[OK] Borrado: ID {producto_id} - {nombre}")
            except Producto.DoesNotExist:
                no_encontrados.append(producto_id)
                print(f"[WARNING] No encontrado: ID {producto_id}")
    
    print(f"\n[RESUMEN] Productos borrados: {len(borrados)}")
    if no_encontrados:
        print(f"[WARNING] No encontrados: {len(no_encontrados)}")
    
    return {'borrados': borrados, 'no_encontrados': no_encontrados}


def agregar_productos_nuevos(productos_info):
    """Agrega productos nuevos al sistema."""
    print("\n" + "="*80)
    print("PASO 3: AGREGAR PRODUCTOS NUEVOS")
    print("="*80)
    
    # Obtener proveedor por defecto (el primero disponible)
    proveedor_default = Proveedor.objects.first()
    
    if not proveedor_default:
        print("[ERROR] No hay proveedores en el sistema. Crea uno primero.")
        return {'agregados': [], 'errores': []}
    
    print(f"[INFO] Usando proveedor por defecto: {proveedor_default.nombre}")
    print("[INFO] Puedes cambiar el proveedor después en el admin")
    
    agregados = []
    errores = []
    
    with transaction.atomic():
        for info in productos_info:
            try:
                nombre = info['nombre']
                
                # Verificar si ya existe
                if Producto.objects.filter(nombre__iexact=nombre).exists():
                    print(f"[SKIP] Ya existe: {nombre}")
                    continue
                
                producto = Producto.objects.create(
                    nombre=nombre,
                    proveedor=proveedor_default,
                    precio_compra=info.get('precio_compra', Decimal('100.00')),
                    precio_venta=info.get('precio_venta', Decimal('150.00')),
                    stock=info.get('stock', 0),
                    tipo=info.get('tipo', None),
                    uva=info.get('uva', None),
                    descripcion=info.get('descripcion', '')
                )
                
                agregados.append((producto.id, nombre))
                print(f"[OK] Agregado: ID {producto.id} - {nombre}")
                
            except Exception as e:
                errores.append(f"Error con '{info['nombre']}': {str(e)}")
                print(f"[ERROR] {info['nombre']}: {str(e)}")
    
    print(f"\n[RESUMEN] Productos agregados: {len(agregados)}")
    if errores:
        print(f"[WARNING] Errores: {len(errores)}")
    
    return {'agregados': agregados, 'errores': errores}


def main():
    print("\n")
    print("="*80)
    print(" "*20 + "ACTUALIZACIÓN COMPLETA DE INVENTARIO")
    print("="*80)
    
    # PASO 1: Importar stock desde CSV
    resultado_import = importar_stock_desde_csv("inventario_export_20260104_221422.csv")
    
    # PASO 2: Borrar productos especificados
    ids_a_borrar = [428, 427, 361, 483, 471]
    resultado_borrado = borrar_productos(ids_a_borrar)
    
    # PASO 3: Agregar productos nuevos
    productos_nuevos = [
        {'nombre': 'Reserva Familiar Montes Toscanini Syrah', 'tipo': 'tinto', 'stock': 0},
        {'nombre': 'SAN GEORGINO ONOR V VALDOBBIADENE PROSECCO SUPERIOR DOCG EXTRA DRY BLANCO', 'tipo': 'blanco', 'stock': 0},
        {'nombre': 'V.B Pinche Pez', 'stock': 0},
        {'nombre': 'ROCCA DOLCETTO SACCO', 'tipo': 'tinto', 'stock': 0},
        {'nombre': 'Anécdota Azul', 'stock': 0},
        {'nombre': 'Elite Cabernet', 'tipo': 'tinto', 'uva': 'Cabernet', 'stock': 0},
        {'nombre': 'Ivan Dolak', 'stock': 0},
        {'nombre': 'Dika', 'stock': 0},
        {'nombre': 'Casa Blanca Chardonnay', 'tipo': 'blanco', 'uva': 'Chardonnay', 'stock': 0},
        {'nombre': 'Oladia Whitwe Zinfandel', 'tipo': 'blanco', 'uva': 'Zinfandel', 'stock': 0},
        {'nombre': 'Cerveza Bohemia Botella La Sagra', 'stock': 0},
        {'nombre': 'Cerveza Doble Malta La Sagra', 'stock': 0},
        {'nombre': 'Cerveza Limon La Sagra', 'stock': 0},
        {'nombre': 'Cerveza Sin Gluten', 'stock': 0},
        {'nombre': 'Cerveza Bohemia Lata La Sagra', 'stock': 0},
    ]
    
    resultado_nuevos = agregar_productos_nuevos(productos_nuevos)
    
    # RESUMEN FINAL
    print("\n" + "="*80)
    print("RESUMEN FINAL")
    print("="*80)
    
    if resultado_import:
        print(f"[OK] Stock actualizado: {resultado_import['actualizados']} productos")
    
    print(f"[OK] Productos borrados: {len(resultado_borrado['borrados'])}")
    for prod_id, nombre in resultado_borrado['borrados']:
        print(f"  - ID {prod_id}: {nombre}")
    
    print(f"[OK] Productos agregados: {len(resultado_nuevos['agregados'])}")
    for prod_id, nombre in resultado_nuevos['agregados']:
        print(f"  - ID {prod_id}: {nombre}")
    
    print("\n" + "="*80)
    print("[COMPLETADO] Inventario actualizado exitosamente")
    print("="*80)
    
    # Generar reporte
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    reporte_file = f"reporte_actualizacion_inventario_{timestamp}.txt"
    
    with open(reporte_file, 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write("REPORTE DE ACTUALIZACIÓN COMPLETA DE INVENTARIO\n")
        f.write("="*80 + "\n\n")
        f.write(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("RESUMEN:\n")
        if resultado_import:
            f.write(f"  - Stock actualizado: {resultado_import['actualizados']} productos\n")
        f.write(f"  - Productos borrados: {len(resultado_borrado['borrados'])}\n")
        f.write(f"  - Productos agregados: {len(resultado_nuevos['agregados'])}\n\n")
        
        f.write("PRODUCTOS BORRADOS:\n")
        for prod_id, nombre in resultado_borrado['borrados']:
            f.write(f"  - ID {prod_id}: {nombre}\n")
        
        f.write("\nPRODUCTOS AGREGADOS:\n")
        for prod_id, nombre in resultado_nuevos['agregados']:
            f.write(f"  - ID {prod_id}: {nombre}\n")
        
        if resultado_import and resultado_import['detalles']:
            f.write("\n" + "="*80 + "\n")
            f.write("CAMBIOS DE STOCK DETALLADOS:\n")
            f.write("="*80 + "\n\n")
            for detalle in resultado_import['detalles']:
                f.write(f"{detalle['nombre']}\n")
                f.write(f"  Stock anterior: {detalle['stock_anterior']}\n")
                f.write(f"  Stock nuevo:    {detalle['stock_nuevo']}\n")
                f.write(f"  Diferencia:     {detalle['diferencia']:+d}\n\n")
    
    print(f"\n[INFO] Reporte detallado guardado en: {reporte_file}")


if __name__ == "__main__":
    main()
