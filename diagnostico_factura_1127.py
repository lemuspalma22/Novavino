"""
Script de diagnóstico para la factura 1127 que no detectó productos no reconocidos.
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'novavino.settings')
django.setup()

from ventas.extractors.novavino import ExtractorNovavino
from ventas.models import Factura, DetalleFactura
from inventario.models import ProductoNoReconocido, Producto
from inventario.utils import encontrar_producto_unico

def main():
    pdf_path = "LEPR970522CD0_Factura_1127_E9DA14FE-E047-465F-A7B0-314647B8D87C.pdf"
    
    print("="*80)
    print("DIAGNÓSTICO FACTURA 1127")
    print("="*80)
    
    # 1. Extraer datos del PDF
    print("\n1. EXTRAYENDO DATOS DEL PDF...")
    extractor = ExtractorNovavino()
    try:
        datos = extractor.extract(pdf_path)
        print(f"✓ UUID: {datos.get('uuid', 'N/A')}")
        print(f"✓ Folio: {datos.get('folio', 'N/A')}")
        print(f"✓ Cliente: {datos.get('cliente', 'N/A')}")
        print(f"✓ Total: ${datos.get('total', 0):,.2f}")
        print(f"✓ Método pago: {datos.get('metodo_pago', 'N/A')}")
        
        productos = datos.get('productos', []) or datos.get('items', [])
        print(f"\n✓ Productos detectados en PDF: {len(productos)}")
        
        for idx, prod in enumerate(productos, 1):
            nombre = prod.get('nombre') or prod.get('producto', '')
            cantidad = prod.get('cantidad', 0)
            precio_u = prod.get('precio_unitario', 0)
            print(f"  {idx}. {nombre}")
            print(f"     - Cantidad: {cantidad}")
            print(f"     - Precio unitario: ${precio_u:,.2f}")
            
            # Verificar si existe en BD
            producto_bd, error = encontrar_producto_unico(nombre)
            if error == "not_found":
                print(f"     ⚠️ NO ENCONTRADO EN BD")
            elif error == "ambiguous":
                print(f"     ⚠️ AMBIGUO (múltiples coincidencias)")
            else:
                print(f"     ✓ Encontrado: {producto_bd.nombre} (ID: {producto_bd.id}, Stock: {producto_bd.stock})")
        
    except Exception as e:
        print(f"✗ Error extrayendo PDF: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 2. Verificar si la factura existe en BD
    print("\n" + "="*80)
    print("2. VERIFICANDO FACTURA EN BASE DE DATOS...")
    print("="*80)
    
    try:
        factura = Factura.objects.get(folio_factura='1127')
        print(f"✓ Factura encontrada:")
        print(f"  - ID: {factura.id}")
        print(f"  - Cliente: {factura.cliente}")
        print(f"  - Total: ${factura.total:,.2f}")
        print(f"  - UUID: {factura.uuid_factura or 'N/A'}")
        print(f"  - Requiere revisión manual: {factura.requiere_revision_manual}")
        print(f"  - Estado revisión: {factura.estado_revision}")
        print(f"  - Método pago: {factura.metodo_pago}")
        
        # Verificar detalles
        detalles = factura.detalles.all()
        print(f"\n✓ Detalles de factura en BD: {detalles.count()}")
        for idx, det in enumerate(detalles, 1):
            print(f"  {idx}. {det.producto.nombre}")
            print(f"     - Cantidad: {det.cantidad}")
            print(f"     - Precio unitario: ${det.precio_unitario:,.2f}")
        
    except Factura.DoesNotExist:
        print("✗ Factura NO encontrada en BD")
        factura = None
    
    # 3. Verificar PNRs
    print("\n" + "="*80)
    print("3. VERIFICANDO PRODUCTOS NO RECONOCIDOS (PNR)...")
    print("="*80)
    
    uuid_cfdi = datos.get('uuid', '')
    pnrs = ProductoNoReconocido.objects.filter(
        uuid_factura=uuid_cfdi,
        origen='venta'
    )
    
    print(f"UUID buscado: {uuid_cfdi}")
    print(f"PNRs encontrados: {pnrs.count()}")
    
    if pnrs.exists():
        for idx, pnr in enumerate(pnrs, 1):
            print(f"\n  PNR #{idx}:")
            print(f"  - Nombre detectado: {pnr.nombre_detectado}")
            print(f"  - Cantidad: {pnr.cantidad}")
            print(f"  - Precio unitario: ${pnr.precio_unitario or 0:,.2f}")
            print(f"  - Procesado: {pnr.procesado}")
            print(f"  - Fecha: {pnr.fecha_detectado}")
            if pnr.producto:
                print(f"  - Asignado a: {pnr.producto.nombre}")
    else:
        print("⚠️ NO se crearon PNRs para esta factura")
    
    # 4. Análisis del problema
    print("\n" + "="*80)
    print("4. ANÁLISIS DEL PROBLEMA")
    print("="*80)
    
    if factura:
        productos_pdf = datos.get('productos', []) or datos.get('items', [])
        detalles_bd = factura.detalles.count()
        
        print(f"\nProductos en PDF: {len(productos_pdf)}")
        print(f"Detalles en BD: {detalles_bd}")
        print(f"PNRs creados: {pnrs.count()}")
        
        diferencia = len(productos_pdf) - detalles_bd
        
        if diferencia > 0:
            print(f"\n⚠️ PROBLEMA DETECTADO:")
            print(f"  Faltan {diferencia} producto(s) en la factura")
            print(f"  Estos productos NO se registraron ni como PNR")
            
            # Identificar cuáles faltan
            productos_bd_nombres = {d.producto.nombre for d in factura.detalles.all()}
            print(f"\n  Productos que deberían estar como PNR:")
            for prod in productos_pdf:
                nombre = prod.get('nombre') or prod.get('producto', '')
                if nombre and nombre not in productos_bd_nombres:
                    cantidad = prod.get('cantidad', 0)
                    print(f"    - {nombre} (cantidad: {cantidad})")
                    
                    # Verificar por qué no se creó
                    producto_bd, error = encontrar_producto_unico(nombre)
                    if cantidad <= 0:
                        print(f"      CAUSA: Cantidad <= 0 ({cantidad})")
                    elif not nombre.strip():
                        print(f"      CAUSA: Nombre vacío")
                    elif error == "not_found":
                        print(f"      CAUSA: Producto no existe en BD")
                    elif error == "ambiguous":
                        print(f"      CAUSA: Producto ambiguo")
        else:
            print(f"\n✓ Todos los productos del PDF están en la BD")
    
    # 5. Recomendaciones
    print("\n" + "="*80)
    print("5. RECOMENDACIONES")
    print("="*80)
    
    print("""
Si el problema es que hay productos con cantidad <= 0 o nombres vacíos:
  → BUG en línea 91-98 de registrar_venta.py
  → No incrementa 'productos_no_reconocidos' cuando nombre o cantidad inválidos
  → SOLUCIÓN: Agregar productos_no_reconocidos += 1 en línea 97

Si el problema es que los productos SÍ existen pero no se detectaron:
  → Verificar la función encontrar_producto_unico()
  → Puede haber problema con alias o normalización de nombres
  
Si el problema es que el UUID no coincide:
  → Verificar que uuid_factura se guarde correctamente en la factura
  → Verificar que los PNR se creen con el mismo UUID
""")
    
    print("\n" + "="*80)
    print("FIN DEL DIAGNÓSTICO")
    print("="*80)

if __name__ == "__main__":
    main()
