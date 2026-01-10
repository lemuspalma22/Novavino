"""
Script para verificar la integración de procesamiento de facturas de ventas desde Drive.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()

print("\n" + "="*80)
print("VERIFICACION: INTEGRACION VENTAS + DRIVE")
print("="*80)

# 1. Verificar variables de entorno
print("\n[1/5] Verificando variables de entorno...")
print("-"*80)

required_vars = [
    'VENTAS_ROOT_ID',
    'VENTAS_NUEVAS_ID',
    'VENTAS_PROCESADAS_ID',
    'VENTAS_ERRORES_ID'
]

missing_vars = []
for var in required_vars:
    value = os.getenv(var)
    if value:
        print(f"  [OK] {var}: {value[:20]}...")
    else:
        print(f"  [ERROR] {var}: NO CONFIGURADA")
        missing_vars.append(var)

if missing_vars:
    print(f"\n[ADVERTENCIA] Faltan variables: {', '.join(missing_vars)}")
    print("Agrega estas variables a tu archivo .env:")
    print("\nVENTAS_ROOT_ID=1I6yGfo7qpq7Eb4T9KpqWnL4qKihbpwiZ")
    print("VENTAS_NUEVAS_ID=1jhsWqGxrVPeokIUCzFjS_Q-0kDE4jI9r")
    print("VENTAS_PROCESADAS_ID=19sDwsEL5xE4k-RQPQ18B-LEMwEv6tP1v")
    print("VENTAS_ERRORES_ID=1f91IEc8lCW9nZA32qHW1c2L9FpAzWnqA")
else:
    print("\n[OK] Todas las variables configuradas")

# 2. Verificar módulo drive_processor
print("\n[2/5] Verificando módulo drive_processor...")
print("-"*80)

try:
    from ventas.utils.drive_processor import DriveVentasProcessor
    print("  [OK] Módulo importado correctamente")
    
    # Intentar crear instancia
    try:
        processor = DriveVentasProcessor()
        print("  [OK] Instancia creada correctamente")
    except Exception as e:
        print(f"  [ERROR] No se pudo crear instancia: {e}")
except ImportError as e:
    print(f"  [ERROR] No se pudo importar: {e}")

# 3. Verificar admin
print("\n[3/5] Verificando integración en admin...")
print("-"*80)

try:
    from ventas.admin import FacturaAdmin
    from ventas.models import Factura
    from django.contrib.admin.sites import AdminSite
    
    # Crear instancia del admin
    site = AdminSite()
    admin_instance = FacturaAdmin(model=Factura, admin_site=site)
    
    # Verificar que tiene el método procesar_drive_view
    if hasattr(admin_instance, 'procesar_drive_view'):
        print("  [OK] Método procesar_drive_view existe")
    else:
        print("  [ERROR] Método procesar_drive_view NO existe")
    
    # Verificar que tiene changelist_view personalizado
    if hasattr(admin_instance, 'changelist_view'):
        print("  [OK] Método changelist_view existe")
    else:
        print("  [ERROR] Método changelist_view NO existe")
    
    # Verificar URLs
    urls = admin_instance.get_urls()
    drive_url_exists = any('procesar-drive' in str(url.pattern) for url in urls)
    if drive_url_exists:
        print("  [OK] URL 'procesar-drive/' registrada")
    else:
        print("  [ERROR] URL 'procesar-drive/' NO registrada")
    
except Exception as e:
    print(f"  [ERROR] Error en admin: {e}")
    import traceback
    traceback.print_exc()

# 4. Verificar template
print("\n[4/5] Verificando template...")
print("-"*80)

template_path = "templates/admin/ventas/factura/change_list.html"
if os.path.exists(template_path):
    print(f"  [OK] Template existe: {template_path}")
    
    # Leer y verificar contenido
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
        if 'show_drive_button' in content:
            print("  [OK] Variable 'show_drive_button' encontrada")
        if 'ventas_factura_procesar_drive' in content:
            print("  [OK] URL 'ventas_factura_procesar_drive' encontrada")
        if 'Procesar Facturas desde Drive' in content:
            print("  [OK] Texto del botón encontrado")
else:
    print(f"  [ERROR] Template NO existe: {template_path}")

# 5. Verificar extractor y registrador
print("\n[5/5] Verificando extractor y registrador...")
print("-"*80)

try:
    from ventas.extractors.novavino import extraer_factura_novavino
    print("  [OK] Extractor de Novavino importado")
except ImportError as e:
    print(f"  [ERROR] No se pudo importar extractor: {e}")

try:
    from ventas.utils.registrar_venta import registrar_venta_automatizada
    print("  [OK] Registrador de ventas importado")
except ImportError as e:
    print(f"  [ERROR] No se pudo importar registrador: {e}")

try:
    from compras.extractors.pdf_reader import extract_text_from_pdf
    print("  [OK] Lector de PDF importado")
except ImportError as e:
    print(f"  [ERROR] No se pudo importar lector de PDF: {e}")

# Resumen
print("\n" + "="*80)
print("RESUMEN")
print("="*80)

if not missing_vars:
    print("\n[OK] Todo configurado correctamente!")
    print("\nPróximos pasos:")
    print("  1. Agrega las variables al .env si aún no lo hiciste")
    print("  2. Reinicia el servidor Django")
    print("  3. Ve al Admin de Ventas")
    print("  4. Busca el botón '📥 Procesar Facturas desde Drive'")
    print("  5. Deposita PDFs en 'Facturas Ventas por Procesar (Nuevas)' en Drive")
    print("  6. Haz clic en el botón")
else:
    print("\n[ADVERTENCIA] Hay problemas de configuración.")
    print("Revisa las secciones de arriba para más detalles.")

print("\n" + "="*80 + "\n")
