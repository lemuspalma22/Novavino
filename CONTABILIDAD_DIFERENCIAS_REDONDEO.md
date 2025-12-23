# Contabilidad: Diferencias de Redondeo en Facturas

## 🎯 El Problema Contable

### Ejemplo Real - Factura 1106:

```
Producto 1: 25 × $314.99 = $7,874.75
Producto 2: 18 × $337.56 = $6,076.08
Producto 3:  2 × $350.05 =   $700.10
                           -----------
Suma detalles:             $14,650.93
Total CFDI (SAT):          $14,651.08
                           -----------
DIFERENCIA:                    $0.15
```

---

## 🤔 ¿Por Qué Existe Esta Diferencia?

### Cálculo del SAT (CFDI):
```
1. Subtotal (sin impuestos):     $9,984.38
2. IVA (16%):                    $1,597.50
3. IEPS (variable):              $3,069.20
                                 ----------
4. TOTAL:                        $14,651.08 ← Redondeo global
```

### Cálculo Nuestro (por producto):
```
Cada producto tiene precio con impuestos ya incluidos:
$314.99 = precio_base + IVA_unitario + IEPS_unitario

Al multiplicar: 25 × $314.99 = $7,874.75
Acumulamos errores de redondeo centavo por centavo
```

**Resultado**: Diferencia de centavos inevitable

---

## 💰 Implicaciones en Corte de Caja

### Escenario A: Sistema Actual (Suma = Total)

```
╔═══════════════════════════════════════════════════╗
║           CORTE DE CAJA - DÍA 09/12/2025         ║
╠═══════════════════════════════════════════════════╣
║ Factura 1106 (Sistema):        $14,650.93        ║
║ Factura 1106 (CFDI real):      $14,651.08        ║
║                                 ----------        ║
║ FALTANTE EN CAJA:                   $0.15 ❌     ║
╚═══════════════════════════════════════════════════╝
```

**Problema**: 
- Cliente pagó $14,651.08 (según CFDI)
- Sistema espera $14,650.93
- Al cuadrar caja: **¿De dónde salieron $0.15?**

---

### Escenario B: Fix Propuesto (Total = PDF)

```
╔═══════════════════════════════════════════════════╗
║           CORTE DE CAJA - DÍA 09/12/2025         ║
╠═══════════════════════════════════════════════════╣
║ Factura 1106 (Sistema):        $14,651.08 ✅     ║
║ Factura 1106 (CFDI real):      $14,651.08 ✅     ║
║                                 ----------        ║
║ DIFERENCIA:                          $0.00 ✅     ║
╚═══════════════════════════════════════════════════╝
```

**Ventaja**: 
- Caja cuadra perfecto con CFDIs
- No hay "faltantes" misteriosos

**Pero**:
- Suma de productos: $14,650.93
- Total factura: $14,651.08
- **Diferencia "flotante": $0.15**

---

## 📊 ¿Dónde Debe Ir Esta Diferencia?

### Contablemente Hablando:

Existen 3 enfoques:

### **1. Cuenta de Redondeos** (Más profesional)

```sql
-- Al hacer reportes financieros
SELECT 
    folio_factura,
    total AS total_facturado,
    SUM(cantidad * precio_unitario) AS suma_productos,
    (total - SUM(cantidad * precio_unitario)) AS diferencia_redondeo
FROM ventas_factura
JOIN ventas_detallefactura ON ...
GROUP BY factura_id

-- Total diferencias_redondeo → Cuenta contable: "Ajustes por Redondeo"
```

**Ejemplo de salida**:
```
Factura 1106: $14,651.08 - $14,650.93 = +$0.15 (Redondeo a favor)
Factura 1107: $8,234.50 - $8,234.48 = +$0.02 (Redondeo a favor)
Factura 1108: $5,120.00 - $5,120.01 = -$0.01 (Redondeo en contra)
                                       ------
                                       +$0.16 ← Va a "Otros Ingresos - Redondeos"
```

---

### **2. Ignorarla** (Pragmático)

**Justificación**:
- Diferencias < $1.00 en promedio
- Se compensan entre sí (unas + otras -)
- Al final del mes: casi $0 neto

**Riesgo**:
- Auditoría SAT podría cuestionar
- Sistemas de alta precisión lo requieren

---

### **3. Ajustar Último Producto** (No recomendado)

```python
# Forzar que suma = total
ultimo_detalle.precio_unitario += diferencia / cantidad
```

❌ **Problemas**:
- Altera precios unitarios
- No refleja realidad
- Complica auditorías

---

## 🎯 Mi Recomendación

### **Opción B + Reportar Diferencias**

1. **Guardar total del PDF** (fix propuesto)
   - Corte de caja cuadra ✅
   - CFDI coincide ✅

2. **Agregar reporte de diferencias**
   ```python
   def reporte_diferencias_redondeo(mes):
       """Muestra diferencias acumuladas para contabilidad"""
       for factura in Factura.objects.filter(mes=mes):
           suma = factura.detalles.aggregate(...)
           diff = factura.total - suma
           if abs(diff) > 0.01:
               print(f"{factura.folio}: {diff}")
   ```

3. **En contabilidad**:
   - Diferencias positivas → "Otros Ingresos - Redondeos"
   - Diferencias negativas → "Gastos - Ajustes de Redondeo"
   - Típicamente se compensan (neto ~$0)

---

## 📈 ¿Cuánto Representa?

En tus 38 facturas procesadas:
- **0 facturas con diferencias > $0.01** (excluyendo sin detalles)
- Esto sugiere que actualmente el sistema recalcula y "oculta" las diferencias

Si aplicamos el fix y mostramos diferencias:
- Estimado: 5-10% de facturas tendrán diferencias
- Rango: $0.01 - $0.50 por factura
- Mensual: ~$5-20 en total (se compensa)

---

## ❓ Preguntas Para Ti

1. **¿Quieres reportar estas diferencias explícitamente?**
   - Sí → Creo un reporte de "Ajustes por Redondeo"
   - No → Solo guardamos total del PDF y listo

2. **¿Tu contador necesita ver esto?**
   - Sí → Agregamos campo en reportes mensuales
   - No → Lo manejamos internamente

3. **¿Qué tan estricta es tu contabilidad?**
   - Muy estricta → Implemento cuenta de redondeos
   - Normal → Total del PDF es suficiente
   - Relajada → Podemos ignorar diferencias < $1

---

## 🔥 Dato Importante

**En sistemas fiscales mexicanos profesionales** (CONTPAQi, Aspel, etc.):
- Siempre usan el total del CFDI como "oficial"
- Diferencias de redondeo se acumulan en cuenta contable separada
- Al final del mes se reportan (típicamente < $100)
- SAT lo acepta como práctica estándar

**Tu fix propuesto sigue esta mejor práctica** ✅
