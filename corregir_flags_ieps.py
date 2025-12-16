"""Corregir flags de compras con IEPS que se procesaron antes del cambio"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()

from compras.models import Compra, CompraProducto

print("\n" + "="*70)
print("CORREGIR FLAGS DE COMPRAS CON IEPS ESPECIAL")
print("="*70)

# Buscar compras de Secretos de la Vid marcadas para revisión
# pero cuyas líneas NO están marcadas
compras_sv = Compra.objects.filter(
    proveedor__nombre__icontains="secretos",
    requiere_revision_manual=True
)

print(f"\nCompras de Secretos de la Vid marcadas para revision: {compras_sv.count()}")

corregidas = 0
for compra in compras_sv:
    # Verificar si tiene líneas sin marcar
    lineas_totales = CompraProducto.objects.filter(compra=compra).count()
    lineas_marcadas = CompraProducto.objects.filter(
        compra=compra,
        requiere_revision_manual=True
    ).count()
    
    if lineas_totales > 0 and lineas_marcadas == 0:
        print(f"\n  Compra {compra.folio}:")
        print(f"    Lineas totales: {lineas_totales}")
        print(f"    Lineas marcadas: {lineas_marcadas}")
        print(f"    [CORRIGIENDO] Marcando todas las lineas...")
        
        # Marcar todas las líneas
        CompraProducto.objects.filter(compra=compra).update(
            requiere_revision_manual=True,
            motivo_revision="factura_contiene_licor_ieps_especial"
        )
        
        corregidas += 1
        print(f"    [OK] {lineas_totales} lineas marcadas")

print(f"\n" + "="*70)
print(f"RESUMEN:")
print(f"  Compras corregidas: {corregidas}")
print("="*70 + "\n")
