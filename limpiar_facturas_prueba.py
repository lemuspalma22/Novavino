# limpiar_facturas_prueba.py
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()

from ventas.models import Factura

# Eliminar facturas de prueba
facturas_prueba = Factura.objects.filter(cliente__icontains="prueba")
count = facturas_prueba.count()
facturas_prueba.delete()

print(f"[OK] Eliminadas {count} facturas de prueba")
