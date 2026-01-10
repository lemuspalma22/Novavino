"""
Script de pruebas local para el extractor de Secretos de la Vid.
Permite probar múltiples PDFs sin necesidad de procesarlos desde Drive.
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()

from extractors.secretos_delavid import ExtractorSecretosDeLaVid
from compras.extractors.pdf_reader import extract_text_from_pdf
from decimal import Decimal
import json

def format_resultado(datos):
    """Formatea los resultados de forma legible."""
    print("\n" + "="*80)
    print("RESULTADOS DE LA EXTRACCIÓN")
    print("="*80)
    
    print(f"\nINFORMACION GENERAL:")
    print(f"  Proveedor: {datos.get('proveedor', 'N/A')}")
    print(f"  Folio: {datos.get('folio', 'N/A')}")
    print(f"  Fecha: {datos.get('fecha', 'N/A')}")
    print(f"  UUID: {datos.get('uuid', 'N/A')}")
    print(f"  Total: ${datos.get('total', 'N/A')}")
    
    productos = datos.get('productos', [])
    print(f"\nPRODUCTOS DETECTADOS: {len(productos)}")
    
    if productos:
        print("\n  #  | Cantidad | Precio Unit. | Nombre")
        print("  " + "-"*76)
        total_calculado = Decimal('0')
        for i, prod in enumerate(productos, 1):
            nombre = prod.get('nombre_detectado', 'N/A')
            cantidad = prod.get('cantidad', 0)
            precio = prod.get('precio_unitario', 0)
            subtotal = Decimal(str(cantidad)) * Decimal(str(precio))
            total_calculado += subtotal
            
            # Truncar nombre si es muy largo
            if len(nombre) > 45:
                nombre = nombre[:42] + "..."
            
            print(f"  {i:2d} | {cantidad:8.2f} | ${precio:10.2f} | {nombre}")
        
        print("  " + "-"*76)
        print(f"  Total calculado: ${total_calculado:.2f}")
        
        # Comparar con el total de la factura
        total_factura = datos.get('total')
        if total_factura:
            try:
                total_factura_decimal = Decimal(str(total_factura))
                diferencia = abs(total_calculado - total_factura_decimal)
                if diferencia > Decimal('0.01'):
                    print(f"  ADVERTENCIA - DIFERENCIA: ${diferencia:.2f}")
                else:
                    print(f"  OK - Total coincide")
            except:
                pass
    else:
        print("  ADVERTENCIA - No se detectaron productos")
    
    print("\n" + "="*80)


def probar_pdf(ruta_pdf, mostrar_texto_raw=False):
    """Prueba la extracción de un PDF."""
    print(f"\n{'#'*80}")
    print(f"PROBANDO: {os.path.basename(ruta_pdf)}")
    print(f"{'#'*80}")
    
    if not os.path.exists(ruta_pdf):
        print(f"ERROR: El archivo no existe: {ruta_pdf}")
        return None
    
    try:
        # Extraer texto del PDF
        print("\n[1/2] Extrayendo texto del PDF...")
        texto = extract_text_from_pdf(ruta_pdf)
        
        if mostrar_texto_raw:
            print("\n" + "="*80)
            print("TEXTO EXTRAÍDO (primeros 2000 caracteres):")
            print("="*80)
            print(texto[:2000])
            print("="*80)
        
        # Crear extractor y parsear
        print("\n[2/2] Parseando con ExtractorSecretosDeLaVid...")
        extractor = ExtractorSecretosDeLaVid(texto, ruta_pdf)
        datos = extractor.parse()
        
        # Mostrar resultados
        format_resultado(datos)
        
        return datos
        
    except Exception as e:
        print(f"\nERROR durante la extraccion:")
        print(f"   Tipo: {type(e).__name__}")
        print(f"   Mensaje: {str(e)}")
        import traceback
        print("\nTRACEBACK COMPLETO:")
        print(traceback.format_exc())
        return None


def probar_todos_pdfs():
    """Prueba todos los PDFs del directorio actual que parezcan de Secretos de la Vid."""
    directorio = os.path.dirname(os.path.abspath(__file__))
    
    # Buscar PDFs que empiecen con SVI (RFC de Secretos de la Vid)
    pdfs_svi = [
        os.path.join(directorio, f) 
        for f in os.listdir(directorio) 
        if f.endswith('.pdf') and f.startswith('SVI')
    ]
    
    if not pdfs_svi:
        print("ADVERTENCIA: No se encontraron PDFs de Secretos de la Vid (SVI*.pdf) en el directorio actual")
        print(f"   Directorio: {directorio}")
        return
    
    print(f"\nEncontrados {len(pdfs_svi)} PDFs de Secretos de la Vid")
    
    resultados = []
    for pdf in pdfs_svi:
        resultado = probar_pdf(pdf)
        resultados.append({
            'archivo': os.path.basename(pdf),
            'exito': resultado is not None,
            'datos': resultado
        })
    
    # Resumen final
    print("\n\n" + "="*80)
    print("RESUMEN DE PRUEBAS")
    print("="*80)
    
    exitosas = sum(1 for r in resultados if r['exito'])
    print(f"\nExitosas: {exitosas}/{len(resultados)}")
    
    if exitosas < len(resultados):
        print(f"Fallidas: {len(resultados) - exitosas}/{len(resultados)}")
        print("\nArchivos con errores:")
        for r in resultados:
            if not r['exito']:
                print(f"  - {r['archivo']}")
    
    print("\n" + "="*80)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Probar extractor de Secretos de la Vid')
    parser.add_argument('pdf', nargs='?', help='Ruta al PDF a probar (opcional)')
    parser.add_argument('--mostrar-texto', action='store_true', help='Mostrar texto extraído del PDF')
    parser.add_argument('--todos', action='store_true', help='Probar todos los PDFs de SVI en el directorio')
    
    args = parser.parse_args()
    
    if args.todos:
        probar_todos_pdfs()
    elif args.pdf:
        probar_pdf(args.pdf, args.mostrar_texto)
    else:
        # Por defecto, probar todos
        print("Uso:")
        print("  python test_secretos_vid.py archivo.pdf           # Probar un PDF específico")
        print("  python test_secretos_vid.py --todos               # Probar todos los PDFs de SVI")
        print("  python test_secretos_vid.py archivo.pdf --mostrar-texto  # Ver texto extraído")
        print("\nProbando todos los PDFs por defecto...\n")
        probar_todos_pdfs()
