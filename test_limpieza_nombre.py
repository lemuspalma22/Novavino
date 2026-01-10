"""Test: Verificar limpieza de nombres"""
import re

nombre_sucio = 'TRES RIBERAS "HA PASADO UN ÁNGEL" SEMIDU20.00'

print(f"Nombre original: '{nombre_sucio}'")

# Aplicar las regex del extractor
descripcion = nombre_sucio

# Regex 1
descripcion = re.sub(r'[A-Z]{2,}\d{1,2}\.\d{2}$', '', descripcion).strip()
print(f"Después regex 1: '{descripcion}'")

# Regex 2
descripcion = re.sub(r'\s+\d{1,2}\.\d{2}$', '', descripcion).strip()
print(f"Después regex 2: '{descripcion}'")

# Regex 3
descripcion = re.sub(r'\s+[A-Z]{2,10}$', '', descripcion).strip()
print(f"Después regex 3: '{descripcion}'")

print(f"\nResultado final: '{descripcion}'")

# Verificar si es válido
from utils.utils_validacion import es_producto_valido

if es_producto_valido(descripcion):
    print("[OK] Nombre es válido")
else:
    print("[ERROR] Nombre es inválido - será rechazado")
