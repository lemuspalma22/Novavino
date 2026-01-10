"""Limpiar flags de compras que ya fueron marcadas como revisadas"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()

from compras.models import Compra, CompraProducto

print("\n" + "="*70)
print("LIMPIAR FLAGS DE COMPRAS YA REVISADAS")
print("="*70)

# Buscar compras revisadas (OK o con cambios)
compras_revisadas = Compra.objects.filter(
    estado_revision__in=["revisado_ok", "revisado_con_cambios"]
)

print(f"\nCompras revisadas encontradas: {compras_revisadas.count()}")

total_lineas_limpiadas = 0
for compra in compras_revisadas:
    # Contar líneas con flags
    lineas_con_flags = CompraProducto.objects.filter(
        compra=compra,
        requiere_revision_manual=True
    ).count()
    
    if lineas_con_flags > 0:
        print(f"\nCompra {compra.folio} ({compra.estado_revision}):")
        print(f"  Lineas con flags: {lineas_con_flags}")
        print(f"  [LIMPIANDO]...")
        
        # Limpiar flags
        CompraProducto.objects.filter(compra=compra).update(
            requiere_revision_manual=False,
            motivo_revision=""
        )
        
        # También limpiar flag de la compra
        compra.requiere_revision_manual = False
        compra.save(update_fields=["requiere_revision_manual"])
        
        total_lineas_limpiadas += lineas_con_flags
        print(f"  [OK] Flags limpiados")

print(f"\n" + "="*70)
print(f"RESUMEN:")
print(f"  Compras procesadas: {compras_revisadas.count()}")
print(f"  Lineas limpiadas: {total_lineas_limpiadas}")
print("="*70 + "\n")
