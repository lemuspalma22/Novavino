"""
Debug detallado del matching de P/U e Importes
"""
from decimal import Decimal
from pdfminer.high_level import extract_text
import re

def _D(x):
    try:
        return Decimal(str(x).replace(",", "").replace("$", "").strip())
    except:
        return None

pdf_path = "VBM041202DD1FB25078.pdf"

# Extraer tokens simulando el extractor
text = extract_text(pdf_path) or ""
raw_lines = text.splitlines()
lines = [re.sub(r"\s+", " ", l).strip() for l in raw_lines]
lines = [l for l in lines if l]

_RE_MONEY_SIMPLE = re.compile(r"^\d{1,4}\.\d{2}$")
_RE_MONEY_COMMA  = re.compile(r"^\d{1,3}(?:,\d{3})+\.\d{2}$")
_TAX_RATES = {Decimal("16.00"), Decimal("26.50")}

# Buscar región post-P/U (después de línea 54)
window = lines[54:83]
tokens = []
for st in ((l or "").strip() for l in window):
    if not st: 
        continue
    if _RE_MONEY_COMMA.match(st) or _RE_MONEY_SIMPLE.match(st):
        val = _D(st)
        if val is not None and val not in _TAX_RATES:
            tokens.append((val, bool(_RE_MONEY_COMMA.match(st))))

print("="*80)
print(" TOKENS ENCONTRADOS (valores monetarios)")
print("="*80)
print()

for i, (val, has_comma) in enumerate(tokens):
    comma_str = "con coma" if has_comma else "sin coma"
    print(f"{i:2d}: ${val:>10} ({comma_str})")

print()
print("="*80)
print(" ITEMS A PROCESAR")
print("="*80)
print()

items = [
    {"cantidad": Decimal("6.00"), "descripcion": "V.T. BIB TINTO 4 MESES 3 LT"},
    {"cantidad": Decimal("18.00"), "descripcion": "V.T. VALLE OCULTO MERLOT 4M 750 ML"},
    {"cantidad": Decimal("18.00"), "descripcion": "V.T. VALLE OCULTO MALBEC 4M 750ML"},
]

for i, it in enumerate(items, 1):
    print(f"{i}. {it['descripcion']}")
    print(f"   Cantidad: {it['cantidad']}")

print()
print("="*80)
print(" CANDIDATOS P/U e IMPORTE")
print("="*80)
print()

pu_cands   = [(i, v) for i, (v, hasc) in enumerate(tokens) if (not hasc) and v < Decimal("1000")]
imp_cands0 = [(i, v, hasc) for i, (v, hasc) in enumerate(tokens) if hasc or v >= Decimal("1000")]

print("Candidatos P/U (sin coma, < 1000):")
for i, v in pu_cands:
    print(f"  Token[{i}]: ${v}")

print()
print("Candidatos Importe (con coma O >= 1000):")
for i, v, hasc in imp_cands0:
    print(f"  Token[{i}]: ${v:>10} {'(con coma)' if hasc else ''}")

print()
print("="*80)
print(" PROCESO DE MATCHING")
print("="*80)
print()

pu_ptr = imp_ptr = 0

for idx, it in enumerate(items):
    q = it["cantidad"]
    print(f"\n--- Item {idx+1}: {it['descripcion'][:40]} ---")
    print(f"Cantidad: {q}")
    print(f"pu_ptr={pu_ptr}, imp_ptr={imp_ptr}")
    
    # Agregar candidatos extra para cantidades <= 20
    imp_cands = list(imp_cands0)
    if q <= Decimal("20"):
        extra = [(i, v, False) for i, (v, hasc) in enumerate(tokens) 
                 if (not hasc) and Decimal("100") <= v < Decimal("5000")]
        seen = {i for (i, _, _) in imp_cands}
        for i, v, hasc in extra:
            if i not in seen: 
                imp_cands.append((i, v, hasc))
                print(f"  + Agregado candidato extra: Token[{i}] = ${v}")
    
    print(f"\nBuscando match óptimo (tolerancia 5%)...")
    print("Probando combinaciones:")
    
    best = None
    for i in range(pu_ptr, min(pu_ptr + 8, len(pu_cands))):
        _, pu_v = pu_cands[i]
        if pu_v >= Decimal("5000"): 
            continue
        for j in range(imp_ptr, min(imp_ptr + 12, len(imp_cands))):
            _, imp_v, _ = imp_cands[j]
            esperado = pu_v * q
            diferencia = abs(esperado - imp_v)
            rel = diferencia / (imp_v if imp_v else Decimal("1"))
            
            if rel <= Decimal("0.05"):
                if not best or rel < best[0]:
                    print(f"  [OK] Token[{pu_cands[i][0]}] P/U=${pu_v} x {q} = ${esperado} ~ Token[{imp_cands[j][0]}] ${imp_v} (error: {rel*100:.2f}%)")
                    best = (rel, i, j, pu_v, imp_v)
    
    if best:
        rel, i, j, pu_v, imp_v = best
        print(f"\n[MEJOR MATCH]:")
        print(f"   P/U: ${pu_v}")
        print(f"   Importe: ${imp_v}")
        print(f"   Verificacion: {q} x ${pu_v} = ${pu_v * q}")
        pu_ptr = i + 1
        imp_ptr = j + 1
    else:
        print(f"\n[NO MATCH], usando fallback...")
        if imp_ptr < len(imp_cands):
            imp_v = imp_cands[imp_ptr][1]
            pu_v = (imp_v / q).quantize(Decimal("0.01"))
            print(f"   Calculado: P/U = ${imp_v} / {q} = ${pu_v}")
            imp_ptr += 1

print()
print("="*80)
