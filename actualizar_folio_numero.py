# actualizar_folio_numero.py
"""
Script para actualizar el campo folio_numero en todas las facturas existentes.
"""
import os
import django
import re

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()

from ventas.models import Factura


def actualizar_folios():
    """Actualiza el campo folio_numero para todas las facturas."""
    print("Actualizando campo folio_numero para todas las facturas...")
    
    facturas = Factura.objects.all()
    total = facturas.count()
    actualizadas = 0
    
    for factura in facturas:
        if factura.folio_factura:
            # Extraer números del folio
            numeros = re.findall(r'\d+', factura.folio_factura)
            if numeros:
                # Tomar el último número encontrado
                factura.folio_numero = int(numeros[-1])
                factura.save(update_fields=['folio_numero'])
                actualizadas += 1
    
    print(f"[OK] Actualizadas {actualizadas} de {total} facturas")
    
    # Mostrar algunos ejemplos
    print("\nEjemplos de folios actualizados:")
    ejemplos = Factura.objects.filter(folio_numero__isnull=False).order_by('-folio_numero')[:10]
    for f in ejemplos:
        print(f"  {f.folio_factura} -> folio_numero: {f.folio_numero}")


if __name__ == "__main__":
    actualizar_folios()
