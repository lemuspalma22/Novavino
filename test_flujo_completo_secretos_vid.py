"""
Test del flujo completo para Secretos de la Vid:
PDF → Extractor → Registrar Compra → BD

Simula lo que hace process_drive_invoices.py pero localmente.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()

from factura_parser import extract_invoice_data
from compras.utils.registrar_compra import registrar_compra_automatizada
from compras.models import Compra
from inventario.models import ProductoNoReconocido
from decimal import Decimal

def probar_flujo_completo(pdf_path):
    """Prueba el flujo completo desde PDF hasta BD."""
    print("\n" + "="*80)
    print(f"PROBANDO FLUJO COMPLETO: {os.path.basename(pdf_path)}")
    print("="*80)
    
    try:
        # Paso 1: Extraer datos del PDF (como lo hace process_drive_invoices.py)
        print("\n[1/3] Extrayendo datos del PDF con factura_parser...")
        datos_extraidos = extract_invoice_data(pdf_path)
        
        print(f"\nDatos extraídos:")
        print(f"  Proveedor: {datos_extraidos.get('proveedor')}")
        print(f"  Folio: {datos_extraidos.get('folio')}")
        print(f"  UUID: {datos_extraidos.get('uuid')}")
        print(f"  Fecha: {datos_extraidos.get('fecha')}")
        print(f"  Total: ${datos_extraidos.get('total')}")
        print(f"  Productos: {len(datos_extraidos.get('productos', []))}")
        
        # Mostrar productos
        for i, prod in enumerate(datos_extraidos.get('productos', []), 1):
            print(f"    {i}. {prod.get('nombre_detectado', 'N/A')} - "
                  f"Cant: {prod.get('cantidad')} - "
                  f"P/U: ${prod.get('precio_unitario')}")
        
        # Paso 2: Verificar si ya existe en BD
        print("\n[2/3] Verificando duplicados...")
        uuid = datos_extraidos.get('uuid')
        if uuid and Compra.objects.filter(uuid=uuid).exists():
            print(f"ADVERTENCIA: La factura ya existe en BD (UUID: {uuid})")
            print("Saltando registro para evitar duplicado.")
            return None
        
        # Paso 3: Registrar en BD (como lo hace process_drive_invoices.py)
        print("\n[3/3] Registrando compra en BD...")
        compra = registrar_compra_automatizada(datos_extraidos)
        
        print(f"\nOK - Compra registrada:")
        print(f"  ID: {compra.id}")
        print(f"  Folio: {compra.folio}")
        print(f"  Total: ${compra.total}")
        print(f"  Proveedor: {compra.proveedor}")
        print(f"  Fecha: {compra.fecha}")
        
        # Verificar productos guardados
        productos_guardados = compra.productos.all()
        print(f"\nProductos guardados en CompraProducto: {productos_guardados.count()}")
        for prod in productos_guardados:
            print(f"  - {prod.producto.nombre}: {prod.cantidad} x ${prod.precio_unitario}")
        
        # Verificar PNRs
        pnrs = ProductoNoReconocido.objects.filter(uuid_factura=uuid, procesado=False)
        if pnrs.exists():
            print(f"\nPNRs pendientes de reconciliar: {pnrs.count()}")
            for pnr in pnrs:
                print(f"  - {pnr.nombre_detectado}: {pnr.cantidad} x ${pnr.precio_unitario}")
        else:
            print(f"\nNo hay PNRs pendientes - Todos los productos se reconocieron OK")
        
        print("\n" + "="*80)
        print("FLUJO COMPLETO: EXITOSO")
        print("="*80)
        
        return compra
        
    except Exception as e:
        print(f"\nERROR en el flujo:")
        print(f"  Tipo: {type(e).__name__}")
        print(f"  Mensaje: {str(e)}")
        import traceback
        print("\nTRACEBACK:")
        print(traceback.format_exc())
        print("\n" + "="*80)
        print("FLUJO COMPLETO: FALLIDO")
        print("="*80)
        return None


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # PDF específico
        pdf_path = sys.argv[1]
        probar_flujo_completo(pdf_path)
    else:
        # Probar con uno de los PDFs de prueba
        pdf_test = "SVI180726AHAFS2326.pdf"
        print(f"Uso: python test_flujo_completo_secretos_vid.py archivo.pdf")
        print(f"\nProbando con: {pdf_test}\n")
        
        if os.path.exists(pdf_test):
            probar_flujo_completo(pdf_test)
        else:
            print(f"ERROR: No se encontró {pdf_test}")
            print("Por favor especifica un PDF: python test_flujo_completo_secretos_vid.py archivo.pdf")
