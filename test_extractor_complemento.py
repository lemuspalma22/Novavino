# test_extractor_complemento.py
"""
Script de prueba para el extractor de Complementos de Pago.
Prueba con el PDF de ejemplo: LEPR970522CD0_Complemento de Pagos_1047_*.pdf
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()

from ventas.extractors.complemento_pago import extract_complemento_from_pdf
from ventas.utils.procesar_complemento import procesar_complemento_pdf
from ventas.models import Factura, ComplementoPago, DocumentoRelacionado
import json


def test_extraccion_basica():
    """Test 1: Extracción básica de datos del PDF."""
    print("=" * 80)
    print("TEST 1: Extracción básica de datos del PDF")
    print("=" * 80)
    
    pdf_path = "LEPR970522CD0_Complemento de Pagos_1047_41EC4C96-9B4B-40AD-9363-A46E307662DB.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"[ERROR] No se encontro el archivo {pdf_path}")
        return False
    
    print(f"[INFO] Procesando: {pdf_path}\n")
    
    try:
        data = extract_complemento_from_pdf(pdf_path)
        
        print("[OK] Datos extraidos correctamente:\n")
        print(f"   Folio: {data['folio']}")
        print(f"   UUID: {data['uuid']}")
        print(f"   Fecha emisión: {data['fecha_emision']}")
        print(f"   Fecha pago: {data['fecha_pago']}")
        print(f"   Monto: ${data['monto']}")
        print(f"   Forma de pago: {data['forma_pago']}")
        print(f"   Cliente: {data['cliente']}")
        print(f"   RFC Cliente: {data['rfc_cliente']}")
        print(f"\n   Documentos relacionados: {len(data['documentos_relacionados'])}")
        
        for i, doc in enumerate(data['documentos_relacionados'], 1):
            print(f"\n   Documento {i}:")
            print(f"      UUID Factura: {doc['uuid_factura']}")
            print(f"      Folio Factura: {doc['folio_factura']}")
            print(f"      Parcialidad: {doc['num_parcialidad']}")
            print(f"      Saldo anterior: ${doc['saldo_anterior']}")
            print(f"      Importe pagado: ${doc['importe_pagado']}")
            print(f"      Saldo insoluto: ${doc['saldo_insoluto']}")
            print(f"      IVA: ${doc.get('iva', 'N/A')}")
            print(f"      IEPS: ${doc.get('ieps', 'N/A')}")
        
        return True
    
    except Exception as e:
        print(f"[ERROR] Error en extraccion: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_factura_existe():
    """Test 2: Verificar si la factura relacionada existe en BD."""
    print("\n" + "=" * 80)
    print("TEST 2: Verificacion de factura relacionada en BD")
    print("=" * 80)
    
    pdf_path = "LEPR970522CD0_Complemento de Pagos_1047_41EC4C96-9B4B-40AD-9363-A46E307662DB.pdf"
    data = extract_complemento_from_pdf(pdf_path)
    
    if not data['documentos_relacionados']:
        print("[ERROR] No hay documentos relacionados para verificar")
        return False
    
    doc = data['documentos_relacionados'][0]
    uuid_factura = doc['uuid_factura']
    folio_factura = doc['folio_factura']
    
    print(f"[SEARCH] Buscando factura:")
    print(f"   Folio: {folio_factura}")
    print(f"   UUID: {uuid_factura}\n")
    
    # Buscar por UUID
    factura = Factura.objects.filter(uuid_factura=uuid_factura).first()
    
    if factura:
        print(f"[OK] Factura encontrada en BD:")
        print(f"   ID: {factura.id}")
        print(f"   Folio: {factura.folio_factura}")
        print(f"   Cliente: {factura.cliente}")
        print(f"   Total: ${factura.total}")
        print(f"   Metodo de pago: {factura.metodo_pago}")
        return True
    else:
        print(f"[WARNING] Factura NO encontrada en BD")
        print(f"   El guardian detectara esto y marcara para revision")
        
        # Buscar si existe alguna factura con ese folio
        factura_por_folio = Factura.objects.filter(folio_factura=folio_factura).first()
        if factura_por_folio:
            print(f"\n   [INFO] Existe factura con folio {folio_factura} pero UUID diferente:")
            print(f"      UUID en BD: {factura_por_folio.uuid_factura}")
            print(f"      UUID en complemento: {uuid_factura}")
        else:
            print(f"\n   [INFO] No existe ninguna factura con folio {folio_factura}")
        
        return False


def test_procesamiento_completo():
    """Test 3: Procesamiento completo con vinculación automática."""
    print("\n" + "=" * 80)
    print("TEST 3: Procesamiento completo (SIMULACIÓN)")
    print("=" * 80)
    
    pdf_path = "LEPR970522CD0_Complemento de Pagos_1047_41EC4C96-9B4B-40AD-9363-A46E307662DB.pdf"
    
    print("[NOTE] Este test es una simulacion. Para ejecutar realmente,")
    print("   necesitas que la factura 1032 exista en tu BD.\n")
    
    # Verificar si ya existe este complemento
    data = extract_complemento_from_pdf(pdf_path)
    existe = ComplementoPago.objects.filter(uuid_complemento=data['uuid']).exists()
    
    if existe:
        print(f"[INFO] El complemento {data['folio']} ya existe en BD")
        comp = ComplementoPago.objects.get(uuid_complemento=data['uuid'])
        print(f"\n[INFO] Informacion del complemento existente:")
        print(f"   ID: {comp.id}")
        print(f"   Folio: {comp.folio_complemento}")
        print(f"   Cliente: {comp.cliente}")
        print(f"   Monto: ${comp.monto_total}")
        print(f"   Requiere revision: {comp.requiere_revision}")
        if comp.motivo_revision:
            print(f"   Motivo: {comp.motivo_revision}")
        
        # Mostrar documentos relacionados
        docs = comp.documentos_relacionados.all()
        print(f"\n   Documentos relacionados: {docs.count()}")
        for doc in docs:
            print(f"      - Factura {doc.factura.folio_factura}")
            print(f"        Importe pagado: ${doc.importe_pagado}")
            if doc.pago_factura:
                print(f"        [OK] Vinculado con PagoFactura #{doc.pago_factura.pk}")
            else:
                print(f"        [WARNING] Sin vincular")
        
        return True
    
    print("[INFO] Pasos del procesamiento completo:")
    print("   1. Extraer datos del PDF [OK]")
    print("   2. Aplicar guardians (validar factura existe)")
    print("   3. Crear ComplementoPago")
    print("   4. Crear DocumentoRelacionado")
    print("   5. Vincular con PagoFactura existente (automatico)")
    print("   6. Guardar archivo PDF")
    
    print("\n[TIP] Para ejecutar realmente:")
    print("   from ventas.utils.procesar_complemento import procesar_complemento_pdf")
    print("   resultado = procesar_complemento_pdf('archivo.pdf')")
    
    return True


def main():
    print("\n")
    print("=" * 80)
    print(" " * 20 + "TEST EXTRACTOR COMPLEMENTOS DE PAGO")
    print("=" * 80)
    print()
    
    resultados = []
    
    # Test 1
    resultados.append(("Extracción básica", test_extraccion_basica()))
    
    # Test 2
    resultados.append(("Verificación de factura", test_factura_existe()))
    
    # Test 3
    resultados.append(("Procesamiento completo", test_procesamiento_completo()))
    
    # Resumen
    print("\n" + "=" * 80)
    print("RESUMEN DE TESTS")
    print("=" * 80)
    
    for nombre, resultado in resultados:
        status = "[OK]" if resultado else "[FAIL]"
        print(f"   {status} {nombre}")
    
    exitosos = sum(1 for _, r in resultados if r)
    total = len(resultados)
    
    print(f"\n[RESULT] {exitosos}/{total} tests exitosos")
    
    if exitosos == total:
        print("\n[SUCCESS] Todos los tests pasaron correctamente!")
    else:
        print("\n[WARNING] Algunos tests fallaron. Revisa los detalles arriba.")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
