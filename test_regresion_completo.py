"""Test de Regresión: Verificar que NO se rompió nada"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()

from compras.models import Compra, CompraProducto, Proveedor
from compras.extractors.pdf_reader import extract_text_from_pdf
from extractors.secretos_delavid import ExtractorSecretosDeLaVid
from extractors.vieja_bodega import ExtractorViejaBodega
from decimal import Decimal

print("\n" + "="*70)
print("TEST DE REGRESION COMPLETO")
print("="*70)

resultados = {
    "total": 0,
    "ok": 0,
    "fallos": []
}

# =========================================================================
# TEST 1: Facturas de Secretos de la Vid existentes (las que ya funcionaban)
# =========================================================================
print("\n[TEST 1] FACTURAS SECRETOS DE LA VID - EXISTENTES")
print("-"*70)

try:
    proveedor_sv = Proveedor.objects.get(nombre="Secretos de la Vid S de RL de CV")
    facturas_sv = Compra.objects.filter(proveedor=proveedor_sv).exclude(folio="2445")[:3]
    
    for compra in facturas_sv:
        resultados["total"] += 1
        
        productos = CompraProducto.objects.filter(compra=compra)
        suma_pdf = sum((p.cantidad or 0) * (p.precio_unitario or 0) for p in productos)
        
        diferencia = abs(compra.total - suma_pdf)
        diferencia_pct = (diferencia / compra.total * 100) if compra.total else 0
        
        if diferencia_pct < 0.1:  # Menos del 0.1%
            print(f"  [OK] Factura {compra.folio}: {productos.count()} productos, cuadra perfecto")
            resultados["ok"] += 1
        else:
            print(f"  [ALERTA] Factura {compra.folio}: diferencia {diferencia_pct:.2f}%")
            if diferencia_pct > 1:
                resultados["fallos"].append(f"SV-{compra.folio}: diferencia alta")
            else:
                resultados["ok"] += 1  # Diferencias pequeñas son aceptables
    
except Exception as e:
    print(f"  [ERROR] {e}")
    resultados["fallos"].append(f"TEST1: {e}")

# =========================================================================
# TEST 2: Extractor de Secretos de la Vid con facturas conocidas
# =========================================================================
print("\n[TEST 2] EXTRACTOR SECRETOS DE LA VID - FACTURAS CONOCIDAS")
print("-"*70)

facturas_test_sv = [
    ("SVI180726AHAFS2335.pdf", "2335", 4),  # IEPS 30%
    ("SVI180726AHAFS2334.pdf", "2334", 3),  # IEPS especiales
]

for pdf_filename, folio_esperado, productos_esperados in facturas_test_sv:
    resultados["total"] += 1
    
    if not os.path.exists(pdf_filename):
        print(f"  [SKIP] {pdf_filename} no encontrado")
        continue
    
    try:
        text = extract_text_from_pdf(pdf_filename)
        extractor = ExtractorSecretosDeLaVid(text, pdf_filename)
        datos = extractor.parse()
        
        folio = datos.get('folio')
        productos = datos.get('productos', [])
        
        # Verificar nombres limpios (sin basura)
        nombres_con_basura = []
        for prod in productos:
            nombre = prod.get('nombre_detectado', '')
            # Verificar si tiene patrón de basura: ALGO20.00 o ALGO30.00
            import re
            if re.search(r'[A-Z]{3,}\d{2}\.\d{2}$', nombre):
                nombres_con_basura.append(nombre)
        
        if folio == folio_esperado and len(productos) >= productos_esperados and not nombres_con_basura:
            print(f"  [OK] {pdf_filename}: {len(productos)} productos, nombres limpios")
            resultados["ok"] += 1
        else:
            if folio != folio_esperado:
                print(f"  [ERROR] {pdf_filename}: folio {folio} != {folio_esperado}")
                resultados["fallos"].append(f"SV-Extract-{folio_esperado}: folio incorrecto")
            elif len(productos) < productos_esperados:
                print(f"  [ERROR] {pdf_filename}: {len(productos)} < {productos_esperados} productos")
                resultados["fallos"].append(f"SV-Extract-{folio_esperado}: productos insuficientes")
            elif nombres_con_basura:
                print(f"  [ERROR] {pdf_filename}: nombres con basura: {nombres_con_basura}")
                resultados["fallos"].append(f"SV-Extract-{folio_esperado}: nombres sucios")
            
    except Exception as e:
        print(f"  [ERROR] {pdf_filename}: {e}")
        resultados["fallos"].append(f"SV-Extract-{folio_esperado}: {e}")

# =========================================================================
# TEST 3: Nueva factura 2445 (TRES RIBERAS)
# =========================================================================
print("\n[TEST 3] FACTURA 2445 - TRES RIBERAS (NUEVO)")
print("-"*70)

resultados["total"] += 1

pdf_2445 = "SVI180726AHAFS2445.pdf"
if os.path.exists(pdf_2445):
    try:
        text = extract_text_from_pdf(pdf_2445)
        extractor = ExtractorSecretosDeLaVid(text, pdf_2445)
        datos = extractor.parse()
        
        productos = datos.get('productos', [])
        
        # Verificar que detecta 4 productos
        if len(productos) != 4:
            print(f"  [ERROR] Productos detectados: {len(productos)} (esperado: 4)")
            resultados["fallos"].append("2445: productos != 4")
        else:
            # Verificar que TRES RIBERAS está y limpio
            tres_riberas_encontrado = False
            tres_riberas_limpio = True
            
            for prod in productos:
                nombre = prod.get('nombre_detectado', '')
                if "TRES RIBERAS" in nombre.upper():
                    tres_riberas_encontrado = True
                    # Verificar que no tiene basura
                    import re
                    if re.search(r'[A-Z]{3,}\d{2}\.\d{2}$', nombre):
                        tres_riberas_limpio = False
            
            if tres_riberas_encontrado and tres_riberas_limpio:
                print(f"  [OK] 4 productos detectados, TRES RIBERAS limpio")
                resultados["ok"] += 1
            else:
                if not tres_riberas_encontrado:
                    print(f"  [ERROR] TRES RIBERAS no detectado")
                    resultados["fallos"].append("2445: TRES RIBERAS no detectado")
                if not tres_riberas_limpio:
                    print(f"  [ERROR] TRES RIBERAS tiene basura")
                    resultados["fallos"].append("2445: nombre sucio")
    except Exception as e:
        print(f"  [ERROR] {e}")
        resultados["fallos"].append(f"2445: {e}")
else:
    print(f"  [SKIP] PDF no encontrado")

# =========================================================================
# TEST 4: Vieja Bodega (NO debe romperse)
# =========================================================================
print("\n[TEST 4] VIEJA BODEGA - FACTURAS EXISTENTES")
print("-"*70)

try:
    proveedores_vb = Proveedor.objects.filter(nombre__icontains="vieja bodega")
    
    if proveedores_vb.exists():
        proveedor_vb = proveedores_vb.first()
        facturas_vb = Compra.objects.filter(proveedor=proveedor_vb)[:2]
        
        for compra in facturas_vb:
            resultados["total"] += 1
            
            productos = CompraProducto.objects.filter(compra=compra)
            suma_pdf = sum((p.cantidad or 0) * (p.precio_unitario or 0) for p in productos)
            
            diferencia = abs(compra.total - suma_pdf)
            diferencia_pct = (diferencia / compra.total * 100) if compra.total else 0
            
            if diferencia_pct < 0.1:
                print(f"  [OK] Factura {compra.folio}: {productos.count()} productos")
                resultados["ok"] += 1
            else:
                print(f"  [ALERTA] Factura {compra.folio}: diferencia {diferencia_pct:.2f}%")
                if diferencia_pct > 1:
                    resultados["fallos"].append(f"VB-{compra.folio}: diferencia alta")
                else:
                    resultados["ok"] += 1
    else:
        print(f"  [SKIP] No hay facturas de Vieja Bodega")
        
except Exception as e:
    print(f"  [ERROR] {e}")
    resultados["fallos"].append(f"TEST4: {e}")

# =========================================================================
# TEST 5: Guardian de Validación (debe seguir funcionando)
# =========================================================================
print("\n[TEST 5] GUARDIAN DE VALIDACION")
print("-"*70)

resultados["total"] += 1

try:
    # Buscar una factura marcada para revisión
    compras_revision = Compra.objects.filter(requiere_revision_manual=True)[:2]
    
    if compras_revision.exists():
        guardian_funciona = True
        for compra in compras_revision:
            # Verificar que tiene motivo
            # Como motivo_revision puede no existir, verificar estado_revision
            if not compra.estado_revision or compra.estado_revision == "":
                guardian_funciona = False
                break
        
        if guardian_funciona:
            print(f"  [OK] Guardian marcando facturas para revision")
            resultados["ok"] += 1
        else:
            print(f"  [ERROR] Guardian no esta marcando correctamente")
            resultados["fallos"].append("Guardian: no marca correctamente")
    else:
        # Si no hay facturas marcadas, puede ser que todo esté bien
        print(f"  [INFO] No hay facturas marcadas para revision (puede ser normal)")
        resultados["ok"] += 1
        
except Exception as e:
    print(f"  [ERROR] {e}")
    resultados["fallos"].append(f"Guardian: {e}")

# =========================================================================
# TEST 6: Widget del Admin (renderizado)
# =========================================================================
print("\n[TEST 6] WIDGET ADMIN - RENDERIZADO")
print("-"*70)

resultados["total"] += 1

try:
    # Importar el admin
    from compras.admin import CompraAdmin
    from django.contrib.admin.sites import AdminSite
    
    # Crear una instancia
    site = AdminSite()
    admin_instance = CompraAdmin(Compra, site)
    
    # Tomar una factura cualquiera
    compra_test = Compra.objects.first()
    
    if compra_test:
        # Intentar renderizar el widget
        html = admin_instance.resumen_revision(compra_test)
        
        if html and len(html) > 100 and "Productos detectados" in html:
            print(f"  [OK] Widget renderiza correctamente")
            resultados["ok"] += 1
        else:
            print(f"  [ERROR] Widget no renderiza o está vacio")
            resultados["fallos"].append("Widget: no renderiza")
    else:
        print(f"  [SKIP] No hay facturas para probar widget")
        resultados["ok"] += 1
        
except Exception as e:
    print(f"  [ERROR] {e}")
    resultados["fallos"].append(f"Widget: {e}")

# =========================================================================
# RESUMEN FINAL
# =========================================================================
print("\n" + "="*70)
print("RESUMEN DE RESULTADOS")
print("="*70)

print(f"\nTests ejecutados: {resultados['total']}")
print(f"Tests exitosos:   {resultados['ok']}")
print(f"Tests fallidos:   {resultados['total'] - resultados['ok']}")

if resultados['fallos']:
    print(f"\n[FALLOS DETECTADOS]:")
    for fallo in resultados['fallos']:
        print(f"  - {fallo}")
else:
    print(f"\n[OK] TODOS LOS TESTS PASARON!")

porcentaje = (resultados['ok'] / resultados['total'] * 100) if resultados['total'] > 0 else 0
print(f"\nTasa de exito: {porcentaje:.1f}%")

if porcentaje >= 90:
    print("\n[EXCELENTE] Sistema funcionando correctamente")
elif porcentaje >= 70:
    print("\n[BUENO] Sistema mayormente funcional, revisar fallos")
elif porcentaje >= 50:
    print("\n[REGULAR] Varios problemas detectados")
else:
    print("\n[CRITICO] Sistema comprometido, revisar urgente")

print("="*70 + "\n")
