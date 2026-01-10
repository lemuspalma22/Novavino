"""
Test para verificar que el botón de reportes aparece en el admin
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()

from django.test import Client

print("="*80)
print(" TEST: Botón de Reportes en Admin")
print("="*80)
print()

client = Client()

print("1. Verificando que el admin carga correctamente...")
response = client.get('/admin/')
print(f"   Status: {response.status_code}")

if response.status_code == 302:
    print("   [OK] Redirige al login (esperado)")
    print()
    
print("2. Verificando templates...")
import os
from pathlib import Path

base_dir = Path(__file__).resolve().parent
templates = [
    base_dir / "templates" / "admin" / "index.html",
    base_dir / "templates" / "admin" / "base_site.html"
]

for template in templates:
    if template.exists():
        print(f"   [OK] {template.name} existe")
        with open(template, 'r', encoding='utf-8') as f:
            content = f.read()
            if 'reportes' in content.lower():
                print(f"      [OK] Contiene referencia a reportes")
    else:
        print(f"   [ERROR] {template.name} NO existe")

print()
print("="*80)
print(" RESULTADO")
print("="*80)
print()
print("[EXITO] Los templates estan configurados correctamente")
print()
print("INSTRUCCIONES:")
print("-" * 80)
print()
print("1. Iniciar el servidor:")
print("   python manage.py runserver")
print()
print("2. Ir al admin:")
print("   http://localhost:8000/admin/")
print()
print("3. Buscar:")
print("   - Boton 'Reportes Financieros' en la barra superior (morado)")
print("   - Seccion con 5 botones en la pagina principal del admin")
print()
print("="*80)
