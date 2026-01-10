"""Analizar PDF de factura 2445 para ver por que no detecto TRES RIBERAS"""
import os
import sys
import re

# Setup Django
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from compras.extractors.pdf_reader import extract_text_from_pdf

# Buscar el PDF
pdf_path = "SVI180726AHAFS2445.pdf"

if not os.path.exists(pdf_path):
    print(f"[ERROR] PDF no encontrado: {pdf_path}")
    print("\nBuscando en carpetas comunes...")
    
    posibles_rutas = [
        os.path.join("facturas", pdf_path),
        os.path.join("pdfs", pdf_path),
        os.path.join("documentos", pdf_path),
    ]
    
    for ruta in posibles_rutas:
        if os.path.exists(ruta):
            pdf_path = ruta
            print(f"[OK] Encontrado en: {ruta}")
            break
    else:
        print("[ERROR] No se encontro el PDF en ninguna ubicacion")
        exit(1)

print("\n" + "="*70)
print("ANALISIS DE PDF - FACTURA 2445")
print("="*70)

# Extraer texto completo
text = extract_text_from_pdf(pdf_path)

print(f"\n1. LONGITUD DEL TEXTO: {len(text)} caracteres")

# Buscar "TRES RIBERAS" en el texto
print("\n2. BUSCAR 'TRES RIBERAS' EN EL TEXTO:")
print("-"*70)

if "TRES RIBERAS" in text.upper():
    print("[OK] 'TRES RIBERAS' encontrado en el texto")
    
    # Encontrar contexto alrededor
    upper_text = text.upper()
    pos = upper_text.find("TRES RIBERAS")
    
    inicio = max(0, pos - 100)
    fin = min(len(text), pos + 150)
    
    contexto = text[inicio:fin]
    print(f"\nContexto (100 chars antes, 150 despues):")
    print("="*70)
    print(contexto)
    print("="*70)
    
else:
    print("[ERROR] 'TRES RIBERAS' NO encontrado en el texto extraido")
    print("\nBuscando variaciones:")
    
    variaciones = [
        "TRES RIBA",
        "3 RIBERAS",
        "RIBERAS",
        "HA PASADO",
        "ANGEL",
        "VIANA-RIBE",
    ]
    
    for var in variaciones:
        if var in text.upper():
            print(f"  [OK] Encontrado: '{var}'")
            pos = text.upper().find(var)
            inicio = max(0, pos - 50)
            fin = min(len(text), pos + 100)
            print(f"       Contexto: {text[inicio:fin]}")
        else:
            print(f"  [NO] No encontrado: '{var}'")

# Buscar la tabla de productos
print("\n3. BUSCAR TABLA DE PRODUCTOS:")
print("-"*70)

# Buscar patrones comunes en facturas de Secretos de la Vid
patrones_tabla = [
    r"Descripci[oó]n.*?Desc.*?P/U.*?Importe",
    r"Cantidad.*?Unidad.*?Clave.*?Descripci[oó]n",
    r"pz.*?FLUMEN",
    r"pz.*?SAN",
    r"pz.*?VIANA",
]

for patron in patrones_tabla:
    matches = re.finditer(patron, text, re.IGNORECASE | re.DOTALL)
    for match in matches:
        inicio = max(0, match.start() - 50)
        fin = min(len(text), match.end() + 200)
        print(f"\n[MATCH] Patron: {patron[:30]}...")
        print("="*70)
        print(text[inicio:fin])
        print("="*70)
        break

# Contar productos mencionados
print("\n4. PRODUCTOS MENCIONADOS EN EL TEXTO:")
print("-"*70)

productos_conocidos = [
    "FLUMEN",
    "SAN ANTONIO",
    "HIDA",
    "PLENO",
    "VIANA",
    "TRES RIBERAS",
]

for prod in productos_conocidos:
    if prod.upper() in text.upper():
        count = text.upper().count(prod.upper())
        print(f"  {prod:20} : {count} veces")
    else:
        print(f"  {prod:20} : NO encontrado")

# Mostrar lineas que contengan VIANA (puede ser VIANA-RIBE)
print("\n5. LINEAS QUE CONTIENEN 'VIANA':")
print("-"*70)

lineas = text.split('\n')
for i, linea in enumerate(lineas):
    if 'VIANA' in linea.upper():
        print(f"\nLinea {i}: {linea}")

print("\n" + "="*70)
print("FIN DEL ANALISIS")
print("="*70 + "\n")
