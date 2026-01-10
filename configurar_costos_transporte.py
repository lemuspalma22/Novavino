"""Configurar costos de transporte por proveedor"""
import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()

from compras.models import Proveedor

# Configurar Vieja Bodega
vb_provs = Proveedor.objects.filter(nombre__icontains="vieja bodega")
for vb in vb_provs:
    vb.costo_transporte_unitario = Decimal("28.00")
    vb.save()
    print(f"[OK] {vb.nombre}: ${vb.costo_transporte_unitario} por unidad")

# Configurar Secretos de la Vid
sv_provs = Proveedor.objects.filter(nombre__icontains="secretos")
for sv in sv_provs:
    sv.costo_transporte_unitario = Decimal("15.00")
    sv.save()
    print(f"[OK] {sv.nombre}: ${sv.costo_transporte_unitario} por unidad")

# Mostrar todos los proveedores y sus costos
print("\n" + "="*60)
print("COSTOS DE TRANSPORTE POR PROVEEDOR:")
print("="*60)
for prov in Proveedor.objects.all():
    print(f"{prov.nombre:40} - ${prov.costo_transporte_unitario}")
print("="*60)
