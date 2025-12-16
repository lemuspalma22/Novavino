"""
Script para verificar que el botón de Drive está correctamente configurado.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()

print("\n" + "="*70)
print("VERIFICACION: BOTON PROCESAR FACTURAS DRIVE")
print("="*70)

# Test 1: Verificar que la URL está registrada
print("\n[1/4] Verificando URL registrada...")
try:
    from django.urls import reverse
    url = reverse('admin:compras_compra_procesar_drive')
    print(f"  [OK] URL registrada: {url}")
except Exception as e:
    print(f"  [ERROR] URL no registrada: {e}")
    exit(1)

# Test 2: Verificar que el template existe
print("\n[2/4] Verificando template...")
import os.path
template_path = "templates/admin/compras/compra/change_list.html"
if os.path.exists(template_path):
    print(f"  [OK] Template existe: {template_path}")
else:
    print(f"  [ERROR] Template no encontrado: {template_path}")
    exit(1)

# Test 3: Verificar que la vista existe
print("\n[3/4] Verificando vista...")
try:
    from compras.admin import CompraAdmin
    from compras.models import Compra
    from django.contrib.admin.sites import site
    
    admin_instance = CompraAdmin(model=Compra, admin_site=site)
    
    if hasattr(admin_instance, 'procesar_drive_view'):
        print("  [OK] Vista procesar_drive_view existe")
    else:
        print("  [ERROR] Vista no encontrada")
        exit(1)
except Exception as e:
    print(f"  [ERROR] Error al verificar vista: {e}")
    exit(1)

# Test 4: Verificar que no hay facturas 2470 en BD
print("\n[4/4] Verificando factura 2470 en BD...")
from compras.models import Compra
compra = Compra.objects.filter(folio="2470").first()
if compra:
    print(f"  [ADVERTENCIA] Factura 2470 YA existe en BD!")
    print(f"    ID: {compra.id}")
    print(f"    Si la procesaste antes, borrala para poder reprocesar")
else:
    print("  [OK] Factura 2470 NO existe en BD")
    print("  [INFO] Lista para ser procesada desde Drive")

print("\n" + "="*70)
print("RESULTADO: TODO CONFIGURADO CORRECTAMENTE")
print("="*70)
print("\nPROXIMOS PASOS:")
print("1. Inicia el servidor Django: python manage.py runserver")
print("2. Ve a: http://localhost:8000/admin/compras/compra/")
print("3. Veras un boton azul: '📥 Procesar Facturas desde Drive'")
print("4. Haz clic en el boton")
print("5. Espera 1-3 minutos")
print("6. Veras mensajes de exito/error en la parte superior")
print("\nNOTA: La factura 2470 de Drive se procesara automaticamente")
print("="*70 + "\n")
