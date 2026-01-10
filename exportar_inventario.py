# exportar_inventario.py
"""
Script para exportar el inventario actual a CSV para actualización física.
Genera un archivo CSV con todos los productos activos para que puedas
actualizarlo con tu conteo físico en Excel.
"""
import os
import django
import csv
from datetime import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()

from inventario.models import Producto


def exportar_inventario_a_csv(filename=None):
    """
    Exporta todos los productos activos a un CSV.
    
    Columnas:
    - ID: ID del producto en la BD (NO MODIFICAR)
    - Nombre: Nombre del producto
    - Proveedor: Nombre del proveedor
    - Stock Actual: Stock actual en sistema
    - Stock Físico: (VACÍO - para que lo llenes)
    - Precio Compra: Precio de compra unitario
    - Precio Venta: Precio de venta unitario
    - Tipo: Tinto/Blanco/Rosado
    - Uva: Tipo de uva
    """
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"inventario_export_{timestamp}.csv"
    
    # Obtener productos activos ordenados por nombre
    productos = Producto.activos.select_related('proveedor').order_by('nombre')
    
    print(f"[INFO] Exportando {productos.count()} productos activos...")
    
    with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
        writer = csv.writer(csvfile)
        
        # Encabezados
        writer.writerow([
            'ID',
            'Nombre',
            'Proveedor',
            'Stock Actual',
            'Stock Físico',
            'Precio Compra',
            'Precio Venta',
            'Tipo',
            'Uva',
            'Notas'
        ])
        
        # Datos
        for producto in productos:
            writer.writerow([
                producto.id,
                producto.nombre,
                producto.proveedor.nombre if producto.proveedor else 'Sin proveedor',
                producto.stock,
                '',  # Stock físico - para llenar manualmente
                f"{producto.precio_compra:.2f}",
                f"{producto.precio_venta:.2f}",
                producto.tipo or '',
                producto.uva or '',
                ''  # Notas - para observaciones
            ])
    
    print(f"[OK] Archivo exportado: {filename}")
    print(f"[OK] Total de productos: {productos.count()}")
    print(f"\n[INSTRUCCIONES]")
    print(f"1. Abre el archivo en Excel: {filename}")
    print(f"2. Llena la columna 'Stock Físico' con tu conteo real")
    print(f"3. NO MODIFIQUES la columna 'ID' (es necesaria para la importación)")
    print(f"4. Puedes agregar notas en la columna 'Notas' si lo deseas")
    print(f"5. Guarda el archivo como CSV (mantén el mismo formato)")
    print(f"6. Ejecuta: python importar_inventario.py {filename}")
    
    return filename


def main():
    print("="*80)
    print(" "*25 + "EXPORTAR INVENTARIO FÍSICO")
    print("="*80)
    print()
    
    filename = exportar_inventario_a_csv()
    
    print("\n" + "="*80)
    print("[LISTO] Puedes abrir el archivo en Excel y actualizarlo")
    print("="*80)


if __name__ == "__main__":
    main()
