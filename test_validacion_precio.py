from decimal import Decimal

precio_bd = Decimal('244.00')
precio_unit = Decimal('218.07')

dif = precio_unit - precio_bd
dif_pct = abs(dif) / precio_bd

print(f'Precio BD: ${precio_bd}')
print(f'Precio extraido: ${precio_unit}')
print(f'Diferencia: ${dif}')
print(f'Diferencia %: {float(dif_pct)*100:.2f}%')
print(f'\nCondiciones:')
print(f'  - diferencia < 0? {dif < 0}')
print(f'  - abs(diferencia) >= 1.0? {abs(dif) >= Decimal("1.0")}')
print(f'  - diferencia_pct > 0.10? {dif_pct > Decimal("0.10")}')
print(f'\nDEBERIA marcar revision? {dif < 0 and abs(dif) >= Decimal("1.0") and dif_pct > Decimal("0.10")}')
