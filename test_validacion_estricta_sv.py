"""Test para verificar la validación estricta de precios en Secretos de la Vid"""
import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()

from compras.utils.validation import evaluar_concepto_para_revision
from compras.models import Proveedor
from inventario.models import Producto

# Crear proveedor de prueba
proveedor_sv, _ = Proveedor.objects.get_or_create(nombre="Secretos de la Vid S de RL de CV")

# Crear producto de prueba
producto_test, _ = Producto.objects.get_or_create(
    nombre="Producto Test SV",
    defaults={"precio_compra": Decimal("244.00"), "stock": 0}
)

print("\n" + "="*70)
print("TEST: Validación Estricta para Secretos de la Vid")
print("="*70)

# Escenarios de prueba
escenarios = [
    {
        "nombre": "Precio OK (dentro de ±$1)",
        "precio_extraido": 243.20,
        "precio_bd": 244.00,
        "esperado": "OK"
    },
    {
        "nombre": "Precio 3% más bajo (OK - dentro de tolerancia <5%)",
        "precio_extraido": 236.72,  # 3% menos
        "precio_bd": 244.00,
        "esperado": "OK"
    },
    {
        "nombre": "Precio 6% más bajo (ALERTA - sospechoso)",
        "precio_extraido": 229.36,  # 6% menos
        "precio_bd": 244.00,
        "esperado": "ALERTA"
    },
    {
        "nombre": "Precio 10% más bajo (ALERTA - muy sospechoso)",
        "precio_extraido": 219.60,  # 10% menos
        "precio_bd": 244.00,
        "esperado": "ALERTA"
    },
    {
        "nombre": "Precio 2% más alto (OK - dentro de tolerancia <3%)",
        "precio_extraido": 248.88,  # 2% más
        "precio_bd": 244.00,
        "esperado": "OK"
    },
    {
        "nombre": "Precio 5% más alto (ALERTA - posible licor/error)",
        "precio_extraido": 256.20,  # 5% más
        "precio_bd": 244.00,
        "esperado": "ALERTA"
    },
    {
        "nombre": "Precio 12% más alto (ALERTA - incremento significativo)",
        "precio_extraido": 273.28,  # 12% más
        "precio_bd": 244.00,
        "esperado": "ALERTA"
    }
]

datos_factura = {
    "proveedor": proveedor_sv
}

for i, escenario in enumerate(escenarios, 1):
    concepto = {
        "descripcion": "Producto Test",
        "precio_unitario": escenario["precio_extraido"],
        "cantidad": 10
    }
    
    motivos = evaluar_concepto_para_revision(
        concepto,
        producto_mapeado=producto_test,
        datos_factura=datos_factura
    )
    
    tiene_alerta = len(motivos) > 0
    resultado = "ALERTA" if tiene_alerta else "OK"
    
    print(f"\n{i}. {escenario['nombre']}")
    print(f"   Precio extraído: ${escenario['precio_extraido']:.2f}")
    print(f"   Precio BD:       ${escenario['precio_bd']:.2f}")
    print(f"   Resultado:       {resultado}")
    if motivos:
        print(f"   Motivos:         {', '.join(motivos)}")
    
    if resultado == escenario["esperado"]:
        print(f"   Estado:          [OK] Correcto")
    else:
        print(f"   Estado:          [ERROR] Esperaba {escenario['esperado']}")

print("\n" + "="*70)
print("Resumen Secretos de la Vid:")
print("  - Más bajo 0-5%:       OK (dentro de tolerancia)")
print("  - Más bajo >5%:        ALERTA (sospechoso)")
print("  - Más alto 0-3%:       OK (dentro de tolerancia)")
print("  - Más alto >3%:        ALERTA (licor, error, falta descuento)")
print("\nVieja Bodega (sin cambios):")
print("  - Más caro >2%:        ALERTA")
print("  - Más barato >10%:     ALERTA")
print("="*70 + "\n")
