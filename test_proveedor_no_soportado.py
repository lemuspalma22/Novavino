"""
Script de prueba para verificar que el mensaje de error es claro
cuando se intenta procesar una factura de un proveedor no soportado.
"""
import os
import django
import tempfile

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()

from factura_parser import extract_invoice_data

print("="*80)
print(" TEST: MENSAJE DE ERROR PARA PROVEEDOR NO SOPORTADO")
print("="*80)
print()

# Crear un PDF de prueba con contenido que NO coincida con ningún proveedor
test_content = """
FACTURA

RFC: XXX999999XXX
Proveedor de Prueba S.A. de C.V.
Folio: TEST-001
Fecha: 22/12/2025

Producto: Vino Genérico
Cantidad: 10
Precio: $100.00
Total: $1,000.00

UUID: 12345678-1234-1234-1234-123456789012
"""

print("[*] Creando PDF de prueba con proveedor no soportado...")
print()

# Crear archivo temporal con el contenido
with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
    temp_path = f.name
    f.write(test_content)

print(f"   Archivo temporal: {temp_path}")
print()

print("[*] Intentando extraer datos de la factura...")
print()

try:
    # Esto debería fallar con mensaje claro
    data = extract_invoice_data(temp_path)
    print("[ERROR] No se esperaba éxito!")
    
except ValueError as e:
    error_msg = str(e)
    print("[OK] Error capturado correctamente")
    print()
    print("="*80)
    print(" MENSAJE DE ERROR RECIBIDO")
    print("="*80)
    print()
    print(error_msg)
    print()
    print("="*80)
    print()
    
    # Verificar que el mensaje es claro
    checks = [
        ("Menciona que no es soportado", "no pertenece" in error_msg.lower() or "no soportado" in error_msg.lower()),
        ("Lista proveedores soportados", "Secretos de la Vid" in error_msg),
        ("Indica registro manual", "manualmente" in error_msg.lower()),
        ("Menciona admin de Compras", "admin" in error_msg.lower()),
    ]
    
    print("[VERIFICACION]")
    print()
    all_pass = True
    for check_name, check_result in checks:
        status = "[OK]" if check_result else "[FALLO]"
        print(f"  {status} {check_name}")
        if not check_result:
            all_pass = False
    
    print()
    if all_pass:
        print("[EXITO] Todos los checks pasaron")
        print()
        print("El mensaje de error es claro e informativo")
    else:
        print("[FALLO] Algunos checks no pasaron")

except Exception as e:
    print(f"[ERROR INESPERADO] {type(e).__name__}: {e}")

finally:
    # Limpiar archivo temporal
    try:
        os.unlink(temp_path)
        print()
        print("[*] Archivo temporal eliminado")
    except:
        pass

print()
print("="*80)
print(" COMO SE VERIA EN LA INTERFAZ")
print("="*80)
print()
print("Cuando un usuario procese una factura de un proveedor no soportado,")
print("vera un mensaje como:")
print()
print("  [X] Error en archivo.pdf: Esta factura no pertenece a ningun")
print("      proveedor con extractor automatico. Proveedores soportados:")
print("      Secretos de la Vid, Vieja Bodega, Distribuidora Secocha,")
print("      Oli Corp. Por favor, registra esta factura manualmente")
print("      desde el admin de Compras.")
print()
print("En lugar del anterior mensaje generico:")
print("  [X] Error en archivo.pdf: Proveedor no soportado o no detectado")
print()
print("="*80)
print()
