# Análisis del Extractor: Secretos de la Vid

## Estado Actual

### ✅ Funcionalidades que funcionan

1. **Extracción de metadatos básicos:**
   - Folio: ✅ Detectado correctamente (1945)
   - UUID: ✅ Detectado correctamente
   - Fecha: ✅ Formato ISO detectado correctamente
   - Total: ✅ Detectado correctamente ($4,286.40)
   - Proveedor: ✅ Creado/obtenido correctamente

2. **Extracción de productos:**
   - Detecta productos con formato específico (unidad "pz" o "PZ")
   - Filtra correctamente líneas de totales/impuestos
   - Captura: cantidad, descripción, precio unitario

### 📋 Formato Detectado

```
Cantidad    Clave        Descripción                     %Desc   P/U        Importe    Unidad
4.0000      POLI/ELI     POLI ELISIR LIMONE / LIMONCELLO  20.00   366.2384   1,464.95   pz
```

### ⚠️ Casos de Prueba Necesarios

Para garantizar robustez, necesitamos probar:

1. **Variaciones en el formato:**
   - Facturas con más/menos productos
   - Productos sin descuento (%Desc = 0.00)
   - Productos con diferentes unidades (litros, cajas, etc.)
   - Facturas con notas de crédito

2. **Casos extremos:**
   - Productos con nombres muy largos (múltiples líneas)
   - Productos con caracteres especiales (ñ, acentos, /)
   - Cantidades decimales vs. enteras
   - Precios muy altos/bajos

3. **Errores comunes de OCR:**
   - Caracteres mal interpretados (O vs 0, l vs I)
   - Espacios adicionales o faltantes
   - Saltos de línea inesperados

### 🔧 Mejoras Implementadas

#### v1 (Original)
```python
# Patrón demasiado amplio - capturaba líneas de totales
r"(\d+\.\d+)\s+[^\n]+\n([^\n]+)\s+\d{2}\.\d{2}\s+([\d,]+\.\d{2})"
```

#### v2 (Actual)
```python
# Patrón más específico - requiere unidad "pz/PZ" al final
patron = r"(\d+\.\d{4})\s+([A-Z0-9/]+)\s+([^\n]+?)\s+(\d{1,3}\.\d{2})\s+([\d,]+\.\d{2,4})\s+([\d,]+\.\d{2})\s+(pz|PZ)"
```

**Ventajas:**
- Evita capturar líneas de totales (IVA, IEPS, Subtotal)
- Valida que la línea tenga estructura completa de producto
- Más resiliente a variaciones en el texto

**Limitaciones:**
- Solo captura productos con unidad "pz" o "PZ"
- Requiere formato muy específico (4 decimales en cantidad)

### 🎯 Próximos Pasos

1. **Testing extensivo:**
   - [ ] Probar con 10+ facturas de Secretos de la Vid
   - [ ] Identificar patrones de fallo
   - [ ] Documentar casos extremos

2. **Mejoras pendientes:**
   - [ ] Soportar otras unidades (LT, KG, etc.)
   - [ ] Manejar cantidades con diferente precisión decimal
   - [ ] Extraer información adicional (IEPS, IVA por producto)
   - [ ] Validar coherencia entre subtotal calculado y total de factura

3. **Integración:**
   - [ ] Probar desde Drive (flujo completo)
   - [ ] Verificar creación de PNRs
   - [ ] Validar reconciliación con productos existentes

## Comando de Prueba

```bash
# Probar un PDF específico
python test_secretos_vid.py ruta/al/pdf.pdf

# Probar todos los PDFs de SVI
python test_secretos_vid.py --todos

# Ver texto extraído para debugging
python test_secretos_vid.py ruta/al/pdf.pdf --mostrar-texto
```

## Resultados de Pruebas

### Prueba 1: SVI180726AHAFS1945.pdf
- **Estado:** ✅ EXITOSA
- **Productos detectados:** 3/3
- **Folio:** 1945
- **Total factura:** $4,286.40
- **Subtotal calculado:** $3,241.56
- **Diferencia:** $1,044.84 (impuestos IVA + IEPS) ✅ Normal

---

**Última actualización:** 11 de diciembre de 2025
