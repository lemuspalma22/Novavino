# importar_inventario.py
"""
Script para importar el inventario físico actualizado desde CSV.
Lee el archivo CSV con el conteo físico y actualiza el stock en la BD.
"""
import os
import django
import csv
import sys
from datetime import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()

from inventario.models import Producto
from django.db import transaction


def importar_inventario_desde_csv(filename):
    """
    Importa el inventario físico desde CSV y actualiza el stock.
    
    Args:
        filename: Ruta al archivo CSV con el inventario actualizado
    
    Returns:
        dict con estadísticas de la importación
    """
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
        
        # Verificar columnas requeridas
        required_columns = ['ID', 'Stock Físico']
        if not all(col in reader.fieldnames for col in required_columns):
            print(f"[ERROR] El CSV debe tener las columnas: {', '.join(required_columns)}")
            print(f"[ERROR] Columnas encontradas: {', '.join(reader.fieldnames)}")
            return None
        
        print(f"[INFO] Procesando productos...")
        
        with transaction.atomic():
            for row_num, row in enumerate(reader, start=2):  # start=2 porque row 1 es header
                try:
                    producto_id = row['ID'].strip()
                    stock_fisico_str = row['Stock Físico'].strip()
                    
                    # Saltar si no hay ID
                    if not producto_id:
                        continue
                    
                    # Saltar si no hay stock físico (no se actualizó)
                    if not stock_fisico_str:
                        sin_cambios += 1
                        continue
                    
                    # Convertir a entero
                    try:
                        producto_id = int(producto_id)
                        stock_fisico = int(stock_fisico_str)
                    except ValueError:
                        errores.append({
                            'fila': row_num,
                            'producto': row.get('Nombre', 'Desconocido'),
                            'error': f"ID o Stock Físico inválido: ID='{producto_id}', Stock='{stock_fisico_str}'"
                        })
                        continue
                    
                    # Buscar producto
                    try:
                        producto = Producto.objects.get(id=producto_id)
                    except Producto.DoesNotExist:
                        errores.append({
                            'fila': row_num,
                            'producto': row.get('Nombre', 'Desconocido'),
                            'error': f"Producto con ID {producto_id} no existe en la BD"
                        })
                        continue
                    
                    # Guardar stock anterior
                    stock_anterior = producto.stock
                    
                    # Actualizar stock
                    producto.stock = stock_fisico
                    producto.save(update_fields=['stock'])
                    
                    actualizados += 1
                    
                    # Guardar detalle
                    diferencia = stock_fisico - stock_anterior
                    detalles.append({
                        'id': producto.id,
                        'nombre': producto.nombre,
                        'stock_anterior': stock_anterior,
                        'stock_nuevo': stock_fisico,
                        'diferencia': diferencia,
                        'notas': row.get('Notas', '').strip()
                    })
                    
                except Exception as e:
                    errores.append({
                        'fila': row_num,
                        'producto': row.get('Nombre', 'Desconocido'),
                        'error': str(e)
                    })
    
    return {
        'actualizados': actualizados,
        'sin_cambios': sin_cambios,
        'errores': errores,
        'detalles': detalles
    }


def generar_reporte(resultado, filename_base):
    """Genera un reporte detallado de la importación."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    reporte_filename = f"reporte_importacion_{timestamp}.txt"
    
    with open(reporte_filename, 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write(" "*20 + "REPORTE DE ACTUALIZACIÓN DE INVENTARIO\n")
        f.write("="*80 + "\n\n")
        
        f.write(f"Archivo importado: {filename_base}\n")
        f.write(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write(f"RESUMEN:\n")
        f.write(f"  - Productos actualizados: {resultado['actualizados']}\n")
        f.write(f"  - Productos sin cambios: {resultado['sin_cambios']}\n")
        f.write(f"  - Errores: {len(resultado['errores'])}\n\n")
        
        if resultado['detalles']:
            f.write("="*80 + "\n")
            f.write("DETALLE DE CAMBIOS:\n")
            f.write("="*80 + "\n\n")
            
            for detalle in resultado['detalles']:
                f.write(f"ID: {detalle['id']} - {detalle['nombre']}\n")
                f.write(f"  Stock anterior: {detalle['stock_anterior']}\n")
                f.write(f"  Stock nuevo:    {detalle['stock_nuevo']}\n")
                f.write(f"  Diferencia:     {detalle['diferencia']:+d}\n")
                if detalle['notas']:
                    f.write(f"  Notas: {detalle['notas']}\n")
                f.write("\n")
        
        if resultado['errores']:
            f.write("="*80 + "\n")
            f.write("ERRORES:\n")
            f.write("="*80 + "\n\n")
            
            for error in resultado['errores']:
                f.write(f"Fila {error['fila']}: {error['producto']}\n")
                f.write(f"  Error: {error['error']}\n\n")
    
    return reporte_filename


def main():
    print("="*80)
    print(" "*25 + "IMPORTAR INVENTARIO FÍSICO")
    print("="*80)
    print()
    
    # Obtener nombre del archivo
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    else:
        # Buscar el archivo más reciente
        import glob
        archivos = glob.glob("inventario_export_*.csv")
        if not archivos:
            print("[ERROR] No se encontró ningún archivo de inventario.")
            print("[TIP] Usa: python importar_inventario.py nombre_archivo.csv")
            return
        
        # Ordenar por fecha de modificación (más reciente primero)
        archivos.sort(key=os.path.getmtime, reverse=True)
        filename = archivos[0]
        print(f"[INFO] Usando archivo más reciente: {filename}")
    
    # Confirmar antes de proceder
    print(f"\n[WARNING] Esto actualizará el stock de los productos en la base de datos.")
    print(f"[WARNING] Archivo a importar: {filename}")
    respuesta = input("\n¿Continuar? (s/n): ")
    
    if respuesta.lower() != 's':
        print("[CANCELADO] Importación cancelada por el usuario")
        return
    
    # Importar
    resultado = importar_inventario_desde_csv(filename)
    
    if resultado is None:
        print("\n[ERROR] La importación falló. Revisa los mensajes de error arriba.")
        return
    
    # Mostrar resumen
    print("\n" + "="*80)
    print("RESUMEN DE IMPORTACIÓN")
    print("="*80)
    print(f"  Productos actualizados: {resultado['actualizados']}")
    print(f"  Productos sin cambios:  {resultado['sin_cambios']}")
    print(f"  Errores:                {len(resultado['errores'])}")
    
    # Mostrar errores si los hay
    if resultado['errores']:
        print("\n[WARNING] Se encontraron errores:")
        for error in resultado['errores'][:5]:  # Mostrar máximo 5
            print(f"  - Fila {error['fila']}: {error['error']}")
        
        if len(resultado['errores']) > 5:
            print(f"  ... y {len(resultado['errores']) - 5} errores más")
    
    # Generar reporte
    reporte_file = generar_reporte(resultado, filename)
    print(f"\n[OK] Reporte detallado guardado en: {reporte_file}")
    
    # Mostrar algunos cambios significativos
    if resultado['detalles']:
        print("\n[INFO] Cambios más significativos:")
        cambios_ordenados = sorted(
            resultado['detalles'],
            key=lambda x: abs(x['diferencia']),
            reverse=True
        )
        
        for detalle in cambios_ordenados[:10]:
            signo = "+" if detalle['diferencia'] > 0 else ""
            print(f"  - {detalle['nombre']}: {detalle['stock_anterior']} → {detalle['stock_nuevo']} ({signo}{detalle['diferencia']})")
    
    print("\n" + "="*80)
    print("[COMPLETADO] Inventario actualizado exitosamente")
    print("="*80)


if __name__ == "__main__":
    main()
