# verificar_actualizacion_inventario.py
"""
Script para verificar el estado actual del inventario después de la actualización.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()

from inventario.models import Producto


def verificar_productos_borrados():
    """Verifica que los productos especificados fueron borrados."""
    print("\n" + "="*80)
    print("VERIFICACION: PRODUCTOS BORRADOS")
    print("="*80)
    
    ids_esperados_borrados = [428, 427, 361, 483, 471]
    
    for prod_id in ids_esperados_borrados:
        existe = Producto.objects.filter(id=prod_id).exists()
        if existe:
            producto = Producto.objects.get(id=prod_id)
            print(f"[WARNING] ID {prod_id} AUN EXISTE: {producto.nombre}")
        else:
            print(f"[OK] ID {prod_id} - Borrado correctamente")


def verificar_productos_nuevos():
    """Verifica que los productos nuevos fueron agregados."""
    print("\n" + "="*80)
    print("VERIFICACION: PRODUCTOS NUEVOS")
    print("="*80)
    
    nombres_esperados = [
        'Reserva Familiar Montes Toscanini Syrah',
        'SAN GEORGINO ONOR V VALDOBBIADENE PROSECCO SUPERIOR DOCG EXTRA DRY BLANCO',
        'V.B Pinche Pez',
        'ROCCA DOLCETTO SACCO',
        'Anécdota Azul',
        'Elite Cabernet',
        'Ivan Dolak',
        'Dika',
        'Casa Blanca Chardonnay',
        'Oladia Whitwe Zinfandel',
        'Cerveza Bohemia Botella La Sagra',
        'Cerveza Doble Malta La Sagra',
        'Cerveza Limon La Sagra',
        'Cerveza Sin Gluten',
        'Cerveza Bohemia Lata La Sagra',
    ]
    
    for nombre in nombres_esperados:
        producto = Producto.objects.filter(nombre__iexact=nombre).first()
        if producto:
            print(f"[OK] ID {producto.id} - {producto.nombre} (Stock: {producto.stock})")
        else:
            print(f"[WARNING] NO ENCONTRADO: {nombre}")


def mostrar_estadisticas_generales():
    """Muestra estadísticas generales del inventario."""
    print("\n" + "="*80)
    print("ESTADISTICAS GENERALES DEL INVENTARIO")
    print("="*80)
    
    total_productos = Producto.activos.count()
    total_con_stock = Producto.activos.filter(stock__gt=0).count()
    total_sin_stock = Producto.activos.filter(stock=0).count()
    
    print(f"Total de productos activos: {total_productos}")
    print(f"Productos con stock: {total_con_stock}")
    print(f"Productos sin stock: {total_sin_stock}")
    
    # Productos con más stock
    print(f"\nProductos con mas stock:")
    productos_top = Producto.activos.order_by('-stock')[:10]
    for p in productos_top:
        print(f"  - {p.nombre}: {p.stock} unidades")
    
    # Productos recién agregados (últimos 20 IDs)
    print(f"\nProductos recien agregados (ultimos 20):")
    productos_recientes = Producto.activos.order_by('-id')[:20]
    for p in productos_recientes:
        print(f"  - ID {p.id}: {p.nombre} (Stock: {p.stock})")


def main():
    print("\n")
    print("="*80)
    print(" "*20 + "VERIFICACION DE ACTUALIZACION DE INVENTARIO")
    print("="*80)
    
    verificar_productos_borrados()
    verificar_productos_nuevos()
    mostrar_estadisticas_generales()
    
    print("\n" + "="*80)
    print("[COMPLETADO] Verificacion finalizada")
    print("="*80)


if __name__ == "__main__":
    main()
