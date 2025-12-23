# Análisis: Diferencia de $0.15 en Factura 1106

## 🔍 Problema Identificado

**Factura 1106**:
- Total en PDF: `$14,651.08` ✅ (extraído correctamente)
- Total en BD: `$14,650.93` ❌ (calculado por suma de detalles)
- **Diferencia: $0.15**

---

## 📊 Causa Raíz

### 1. **Extracción del PDF** ✅
El extractor funciona **perfectamente**:
```
Total extraído: $14,651.08 ← CORRECTO
```

### 2. **Suma de Productos**
Los productos individuales suman:
```
25 × $314.99 = $7,874.75
18 × $337.56 = $6,076.08
 2 × $350.05 =   $700.10
              -----------
              $14,650.93 ← 15 centavos menos
```

### 3. **El Problema: Signal que Recalcula**

**Archivo**: `ventas/signals.py` (líneas 10-17, 42, 56)

```python
def _recalc_factura_total(factura):
    # SUMA los detalles y SOBRESCRIBE el total
    agg = factura.detalles.aggregate(s=Sum(cantidad * precio_unitario))
    factura.total = agg["s"]  # ← SOBRESCRIBE el total del PDF
    factura.save()

# Este signal se ejecuta cada vez que se guarda un DetalleFactura
@receiver(post_save, sender=DetalleFactura)
def _on_detalle_save(...):
    _recalc_factura_total(instance.factura)  # ← AQUÍ SE PIERDE EL TOTAL DEL PDF
```

### 4. **¿Por Qué Difieren?**

**Redondeo de Impuestos**:
- El CFDI calcula impuestos globalmente
- Nosotros calculamos precio unitario con impuestos incluidos
- Al multiplicar `cantidad × precio_unitario`, acumulamos errores de redondeo

**Ejemplo con Anécdota Blend**:
```
PDF dice: 25 botellas = $7,874.75
Nosotros: 25 × $314.99 = $7,874.75 ✅ (coincide por casualidad)

Pero el total global tiene redondeos diferentes del SAT
```

---

## 🎯 Opciones de Solución

### **Opción 1: Mantener Total del PDF (Recomendada)** ⭐

**Cambio mínimo, bajo riesgo**

#### Pros:
- ✅ Total **siempre coincide con el PDF** (inmutable como debe ser)
- ✅ No afecta funcionalidad existente
- ✅ Cambio pequeño y controlado
- ✅ Solo requiere modificar `registrar_venta.py` (guardar total extraído al final)

#### Contras:
- ⚠️ Suma de detalles puede diferir ligeramente del total
- ⚠️ Widget de validación mostraría "diferencia" aunque sea legítima

#### Implementación:
```python
# Al final de registrar_venta_automatizada():
if detalles_creados > 0:
    # Restaurar el total del PDF (sobrescribir el calculado por signals)
    factura.total = total_decimal  # ← del PDF
    factura.save(update_fields=["total"])
```

---

### **Opción 2: Deshabilitar Recálculo Automático**

**Más invasivo, mayor riesgo**

#### Pros:
- ✅ Total siempre es el del PDF
- ✅ No hay recálculos inesperados

#### Contras:
- ❌ Si alguien edita detalles manualmente, el total NO se actualiza
- ❌ Requiere cambiar lógica en múltiples lugares
- ❌ Puede romper flujos existentes (admin, ediciones manuales)

#### Implementación:
- Eliminar signals de recálculo
- Agregar botón "Recalcular Total" manual en admin
- Riesgo: totales incorrectos si no se recalcula manualmente

---

### **Opción 3: Guardar Ambos Totales**

**Solución robusta pero compleja**

#### Pros:
- ✅ Conservas tanto el total del PDF como el calculado
- ✅ Permite auditoría de diferencias
- ✅ Widget puede validar contra ambos

#### Contras:
- ❌ Requiere migración de BD (nuevo campo)
- ❌ Más complejo de mantener
- ❌ Necesita actualizar admin, vistas, reportes

#### Implementación:
```python
# Modelo Factura
total = models.DecimalField()  # Calculado por suma
total_pdf = models.DecimalField(null=True)  # Del CFDI original

# Widget valida:
if abs(total - total_pdf) < 1.00:  # Tolerancia de $1
    mostrar_como_ok()
```

---

### **Opción 4: Usar Subtotales del PDF**

**Solución ideal pero requiere mejorar extractor**

#### Pros:
- ✅ Cada producto tiene su importe exacto del PDF
- ✅ Suma perfecta sin redondeos
- ✅ Total = Suma (siempre)

#### Contras:
- ❌ Requiere modificar extractor
- ❌ PDFs pueden no tener importes por línea claramente
- ❌ Mayor esfuerzo de desarrollo

#### Implementación:
```python
# Extractor debe sacar:
productos = [
    {"nombre": "X", "cantidad": 25, "precio_unitario": 314.99, 
     "importe": 7874.75},  # ← del PDF, no calculado
]
```

---

## 🎯 Recomendación

### **Opción 1: Mantener Total del PDF** ⭐

**Razones**:
1. ✅ **Bajo riesgo**: Cambio mínimo (5 líneas de código)
2. ✅ **Correcto conceptualmente**: Total del CFDI es inmutable
3. ✅ **No rompe nada**: Signals siguen funcionando para ediciones manuales
4. ✅ **Fácil de probar**: Solo necesitas reprocesar 1106 y verificar

**Diferencias aceptables**:
- Las diferencias de centavos entre suma de detalles y total son **normales** por redondeos del SAT
- Mientras el total sea del PDF, estás reportando cifras correctas al SAT

---

## 📝 Siguiente Paso

**Antes de implementar**:
1. ¿Confirmas que prefieres Opción 1?
2. ¿O prefieres explorar otra opción?
3. ¿Quieres que agreguemos un campo de auditoría para trackear estas diferencias?

**Pregunta clave**:
- ¿Es más importante que el total coincida con el PDF, o que el total sea la suma exacta de los detalles?

**Mi opinión**: El total debe coincidir con el PDF siempre. Los redondeos en detalles son inevitables.
