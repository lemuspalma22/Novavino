"""Verificar el HTML que se genera para el campo de nombre"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()

from inventario.models import ProductoNoReconocido

print("\n" + "="*70)
print("VERIFICAR HTML GENERADO PARA CAMPO NOMBRE")
print("="*70)

pnr = ProductoNoReconocido.objects.filter(
    nombre_detectado__icontains="TRES RIBERAS",
    procesado=False
).first()

if pnr:
    print(f"\nPNR ID: {pnr.id}")
    print(f"Nombre detectado: '{pnr.nombre_detectado}'")
    print(f"Longitud: {len(pnr.nombre_detectado)} caracteres")
    
    # Simular el HTML generado
    pnr_id_val = pnr.id
    nombre_html = f'<input type="text" id="nombre_{pnr_id_val}" value="{pnr.nombre_detectado or ""}" />'
    
    print(f"\nHTML generado:")
    print(nombre_html)
    
    # Verificar si el valor está completo
    print(f"\nValor en el atributo value: '{pnr.nombre_detectado}'")
    
    # Verificar problemas de encoding
    print(f"\nBytes del nombre:")
    try:
        print(pnr.nombre_detectado.encode('utf-8'))
    except Exception as e:
        print(f"  Error: {e}")
    
    # Verificar si hay comillas que causen problemas
    if '"' in pnr.nombre_detectado or "'" in pnr.nombre_detectado:
        print(f"\n[ALERTA] El nombre contiene comillas!")
        print(f"  Esto puede causar problemas en el HTML")
        print(f"  El navegador puede truncar el valor en la primera comilla")
        print(f"\n  SOLUCION:")
        print(f"    Escapar las comillas en el HTML usando html.escape()")
    
    print("\n" + "="*70 + "\n")
else:
    print("\n[INFO] No se encontro PNR de TRES RIBERAS")
    print("="*70 + "\n")
