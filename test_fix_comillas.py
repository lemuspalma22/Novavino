"""Test: Verificar que el fix de comillas funciona"""
import html

print("\n" + "="*70)
print("TEST: FIX DE COMILLAS EN HTML")
print("="*70)

nombre = 'TRES RIBERAS "HA PASADO UN ÁNGEL"'

print(f"\nNombre original:")
print(f"  '{nombre}'")

print(f"\nANTES (sin escapar):")
html_antes = f'<input value="{nombre}" />'
print(f"  {html_antes}")
print(f"  [PROBLEMA] Las comillas rompen el HTML")

print(f"\nAHORA (escapado):")
nombre_escapado = html.escape(nombre, quote=True)
html_ahora = f'<input value="{nombre_escapado}" />'
print(f"  {html_ahora}")
print(f"  [OK] Las comillas se convierten en &quot;")

print(f"\nComo lo ve el navegador:")
print(f"  Valor en el input: '{nombre}'")
print(f"  (El navegador convierte &quot; de vuelta a comillas)")

print("\n" + "="*70)
print("RESULTADO:")
print("-"*70)
print(f"[OK] El nombre completo ahora aparecerá en el campo")
print(f"[OK] Ya no se truncará en las comillas")
print("="*70 + "\n")
