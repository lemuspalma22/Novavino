# 🧹 Limpieza del Repositorio

## ✅ Archivos a ELIMINAR (seguros)

### 1. **Archivos Python Compilados** (.pyc, __pycache__)
```bash
# Estos se regeneran automáticamente
git rm -r __pycache__/
git rm -r compras/__pycache__/
git rm -r crm_project/__pycache__/
git rm -r extractors/__pycache__/
git rm -r inventario/__pycache__/
git rm -r reportes/__pycache__/
git rm -r utils/__pycache__/
git rm -r ventas/__pycache__/
```

### 2. **Archivos Vacíos** (0 bytes)
```bash
git rm 25.2
git rm backup.sql
git rm backup_local.sql
```

### 3. **PDFs de Prueba/Ejemplo**
```bash
# No deben estar en el repo - usar .gitignore
git rm LEPR970522CD0_Factura_1106_E234D345-D60D-4576-9301-2EC0B1405A53.pdf
git rm LEPR970522CD0_Factura_1137_6AC32C47-863E-4E7E-85A5-0DD0F991AEB4.pdf
git rm VBM041202DD1FB25078.pdf
```

### 4. **Archivos ZIP de Descarga**
```bash
git rm drive-download-20251112T021545Z-1-001.zip
```

### 5. **Archivos CSV Temporales**
```bash
git rm inventario_prueba.csv
git rm productos_revision.csv
git rm productos_revision_corregido.csv
```

### 6. **Archivos TXT Temporales**
```bash
git rm factura_1127_texto.txt
git rm productos_actualizacion_log.txt
git rm urls_novavino_prject.txt
git rm "Instrucciones y comandos.txt"
```

### 7. **Backups JSON**
```bash
git rm backup_inventario.json
```

---

## 🔍 Scripts de Debug/Corrección (REVISAR antes de eliminar)

### Scripts de Corrección Específica (probablemente obsoletos)
```bash
# Una vez ejecutados, ya no son necesarios
git rm actualizar_mensaje_2335.py
git rm corregir_bacalauh.py
git rm corregir_epico.py
git rm corregir_factura_1116.py
git rm corregir_factura_1127.py
git rm corregir_factura_1137.py
git rm corregir_flags_ieps.py
git rm corregir_stock_duplicado.py
git rm limpiar_2334.py
git rm limpiar_alias_redundantes.py
git rm limpiar_flags_revisadas.py
git rm limpiar_pnr_huerfanos.py
git rm limpiar_y_reprocesar.py
git rm normalizar_proveedor_secretos_vid.py
git rm sincronizar_costos_transporte.py
```

### Scripts de Análisis/Debug (temporales)
```bash
git rm analizar_diferencias_totales.py
git rm analizar_factura_1127.py
git rm analizar_factura_1137.py
git rm analizar_pdf_2445.py
git rm analizar_pnr.py
git rm debug_*.py  # Todos los debug_*.py
git rm diagnostico_*.py
git rm investigar_*.py
git rm revisar_*.py
git rm verificar_*.py
git rm ver_texto_*.py
git rm extraer_texto_1127.py
git rm leer_pdf_1127.py
```

### Scripts de Importación/Exportación (uno por uno)
```bash
# Estos pueden ser útiles - revisar antes
git rm exportar_productos_revision.py
git rm importar_productos_corregidos.py
git rm importar_productos_corregidos_auto.py
git rm configurar_costos_transporte.py
```

### Scripts de Procesamiento (posiblemente obsoletos)
```bash
git rm factura_parser.py
git rm reprocesar_factura_2445.py
git rm procesar_factura_2470_test.py
git rm simular_corte_1106.py
git rm reorganizar_carpetas_ventas_drive.py
git rm detectar_duplicados_ventas.py
```

---

## 📚 Documentación (CONSOLIDAR)

### Docs de Bugs/Fixes Específicos (mover a /docs/historico/)
```bash
# Mover a carpeta docs/ en lugar de eliminar
mkdir -p docs/bugs_resueltos/
git mv ANALISIS_PROBLEMA_TOTAL_FACTURA_1106.md docs/bugs_resueltos/
git mv BUG_FIX_RESUMEN.md docs/bugs_resueltos/
git mv DEBUG_STOCK_DUPLICADO.md docs/bugs_resueltos/
git mv EXTRACTOR_SECRETOS_VID_ANALISIS.md docs/bugs_resueltos/
git mv FIX_GUARDIAN_VENTAS_IMPLEMENTADO.md docs/bugs_resueltos/
git mv FIX_MENSAJE_PROVEEDOR_NO_SOPORTADO.md docs/bugs_resueltos/
git mv INSTRUCCIONES_DEBUG_ADMIN.md docs/bugs_resueltos/
git mv NORMALIZACION_PROVEEDOR_SECRETOS_VID.md docs/bugs_resueltos/
git mv RESUMEN_EJECUTIVO_FACTURA_1106.md docs/bugs_resueltos/
git mv RESUMEN_FIX_MENSAJE_PROVEEDOR.md docs/bugs_resueltos/
git mv RESUMEN_NORMALIZACION_SV.md docs/bugs_resueltos/
git mv SISTEMA_REVISION_MANUAL.md docs/bugs_resueltos/
git mv SOLUCION_COMPLETA_1127.md docs/bugs_resueltos/
git mv SOLUCION_TRES_RIBERAS.md docs/bugs_resueltos/
git mv VERIFICACION_STOCK_VENTAS.md docs/bugs_resueltos/
```

### Docs de Features (mover a /docs/features/)
```bash
mkdir -p docs/features/
git mv FASE1_PAGOS_PARCIALES_IMPLEMENTADA.md docs/features/
git mv FASE2_PAGOS_PARCIALES_COMPRAS_IMPLEMENTADA.md docs/features/
git mv FASE3_REPORTES_DASHBOARDS_IMPLEMENTADA.md docs/features/
git mv FEATURE_MARCAR_FACTURAS_PAGADAS.md docs/features/
git mv FECHA_PAGO_COMPRAS_AGREGADA.md docs/features/
git mv FUSION_SUAVE_IMPLEMENTADA.md docs/features/
git mv MEJORAS_CORTE_SEMANAL.md docs/features/
git mv PNR_VENTAS_RESUMEN.md docs/features/
git mv INTEGRAR_PNR_ADMIN.md docs/features/
```

### Docs de Guías (mover a /docs/guias/)
```bash
mkdir -p docs/guias/
git mv PROCESAR_FACTURAS_DRIVE_GUIA.md docs/guias/
git mv PROCESAR_FACTURAS_DRIVE_RESUMEN.md docs/guias/
git mv PROCESAR_FACTURAS_VENTAS_DRIVE_GUIA.md docs/guias/
git mv GUIA_REPORTE_DIFERENCIAS_REDONDEO.md docs/guias/
git mv CONTABILIDAD_DIFERENCIAS_REDONDEO.md docs/guias/
```

### Docs de Resumen (mover a /docs/resumen/)
```bash
mkdir -p docs/resumen/
git mv RESUMEN_FASE1_PAGOS_PARCIALES.md docs/resumen/
git mv RESUMEN_FASE2_PAGOS_COMPRAS.md docs/resumen/
git mv RESUMEN_FASE3_REPORTES.md docs/resumen/
git mv RESUMEN_MARCAR_PAGADAS.md docs/resumen/
```

---

## 🧪 Tests (REVISAR cuáles mantener)

### Tests Útiles (MANTENER)
- `test_corte_pagos_parciales.py` ✓
- `test_descuentos_ventas.py` ✓
- `test_pagos_parciales_fase1.py` ✓
- `test_pagos_parciales_compras_fase2.py` ✓
- `test_reportes_fase3.py` ✓
- `test_regresion_completo.py` ✓
- `test_guardian_ventas.py` ✓

### Tests Obsoletos/Específicos (eliminar)
```bash
git rm test_fix_25078.py
git rm test_factura_1127.py
git rm test_factura_2335_regresion.py
git rm test_extractor_1127.py
git rm test_extraccion_completa_2334.py
git rm test_extractor_mejorado_2445.py
git rm test_fix_comillas.py
git rm test_validacion_directa.py
git rm test_vendor_extractor.py
git rm test_vb_no_roto.py
```

---

## 📦 Actualizar .gitignore

Agregar al `.gitignore`:
```
# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.pytest_cache/

# Archivos temporales
*.tmp
*.bak
*.swp
*~

# PDFs de prueba
*.pdf
!docs/*.pdf  # Permitir PDFs en docs/

# Archivos de texto temporal
factura_*_texto.txt
*_log.txt

# CSVs temporales
*_prueba.csv
*_corregido.csv
*_revision.csv

# Backups
backup*.sql
backup*.json
*.zip

# Entorno
.env
.venv/
venv/
token.json
client_secrets.json

# Archivos del IDE
.idea/
.vscode/
*.code-workspace

# Static files
/static/
/staticfiles/

# Base de datos
*.sqlite3
db.sqlite3
