"""Actualizar mensaje de revision en factura 2335 con mensaje mas claro"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()

from compras.models import CompraProducto

print("\n" + "="*70)
print("ACTUALIZAR MENSAJE DE REVISION - FACTURA 2335")
print("="*70)

# Actualizar mensaje viejo al nuevo
updated = CompraProducto.objects.filter(
    motivo_revision="factura_contiene_licor_ieps_especial"
).update(
    motivo_revision="toda_factura_requiere_revision_por_contener_licor_ieps_30pct_o_53pct"
)

print(f"\nLineas actualizadas: {updated}")
print("\nMensaje viejo: 'factura_contiene_licor_ieps_especial'")
print("Mensaje nuevo: 'toda_factura_requiere_revision_por_contener_licor_ieps_30pct_o_53pct'")
print("\nEste mensaje es mas claro para el administrador.")
print("="*70 + "\n")
