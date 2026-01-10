"""
Test de FASE 3: Reportes y Dashboards
Verifica que todos los dashboards funcionan correctamente.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()

from django.test import Client
from django.urls import reverse

print("="*80)
print(" TEST: FASE 3 - REPORTES Y DASHBOARDS")
print("="*80)
print()

# Crear cliente de prueba
client = Client()

# Lista de URLs a probar
urls_a_probar = [
    ('Dashboard Principal', 'reportes:dashboard'),
    ('Cuentas por Cobrar', 'reportes:cuentas_por_cobrar'),
    ('Cuentas por Pagar', 'reportes:cuentas_por_pagar'),
    ('Flujo de Caja', 'reportes:flujo_caja'),
    ('Distribucion de Fondos', 'reportes:distribucion_fondos'),
]

print("PROBANDO ACCESO A DASHBOARDS:")
print("-" * 80)
print()

resultados = []

for nombre, url_name in urls_a_probar:
    try:
        url = reverse(url_name)
        response = client.get(url)
        
        status = "OK" if response.status_code == 200 else f"ERROR {response.status_code}"
        resultados.append((nombre, status, response.status_code))
        
        print(f"[{status}] {nombre}")
        print(f"    URL: {url}")
        print(f"    Status Code: {response.status_code}")
        
        if response.status_code == 200:
            # Verificar que el contenido tiene algo
            content_length = len(response.content)
            print(f"    Content Length: {content_length} bytes")
            
            # Verificar que el template se renderizó
            if hasattr(response, 'template_name'):
                print(f"    Template: {response.template_name}")
        
        print()
        
    except Exception as e:
        print(f"[ERROR] {nombre}")
        print(f"    Error: {str(e)}")
        print()
        resultados.append((nombre, "ERROR", 0))

print("="*80)
print(" RESUMEN")
print("="*80)
print()

exitosos = sum(1 for _, status, _ in resultados if status == "OK")
total = len(resultados)

print(f"Dashboards exitosos: {exitosos}/{total}")
print()

for nombre, status, code in resultados:
    simbolo = "[OK]" if status == "OK" else "[FALLO]"
    print(f"{simbolo} {nombre}: {status}")

print()

if exitosos == total:
    print("[EXITO] Todos los dashboards están funcionando correctamente!")
    print()
    print("INSTRUCCIONES PARA VER LOS DASHBOARDS:")
    print("-" * 80)
    print()
    print("1. Iniciar el servidor:")
    print("   python manage.py runserver")
    print()
    print("2. Abrir en el navegador:")
    print("   http://localhost:8000/reportes/")
    print()
    print("3. Navegar entre los dashboards usando el menú superior")
    print()
else:
    print("[FALLO] Algunos dashboards tienen problemas")
    print()
    print("Revisar los errores anteriores")

print("="*80)
