# Mejoras al Sistema de Corte Semanal

## 📅 Fecha: 23 de Diciembre, 2025

---

## 🎯 Objetivos Implementados

### 1. ✅ **Soporte para Pagos Parciales en Corte de Flujo**
**Problema**: El corte de flujo no consideraba facturas con pagos parciales (ej: VPG1125-03)

**Solución**:
- Modificado `utils/reportes.py` para buscar facturas con **cualquier pago** en el periodo
- Ahora considera modelo `PagoFactura` en lugar de solo `fecha_pago` de la factura
- Soporta múltiples pagos distribuidos en el tiempo

**Ejemplo**:
```
Factura VPG1125-03
Total: $3,883.00
Pagos:
  - 13/Dic: $935.00
  - 19/Dic: $1,200.00
  - 22/Dic: $1,000.00

Corte del 15-Dic al 29-Dic:
✓ Incluye esta factura
✓ Suma solo pagos del periodo: $2,200.00 (19/Dic + 22/Dic)
```

---

### 2. ✅ **Checkboxes Interactivos con Recalculación Dinámica**
**Problema**: No se podía filtrar facturas después de generar el reporte

**Solución**:
- Agregada columna de checkboxes en cada fila
- JavaScript recalcula totales automáticamente al activar/desactivar
- Checkbox en encabezado para seleccionar/deseleccionar todo

**Uso**:
1. **Generar reporte completo** → Todas las facturas activas
2. **Desactivar facturas en efectivo** → Ver solo transferencias bancarias
3. **Totales se recalculan** automáticamente

**Totales dinámicos**:
- Total Venta
- Costo Proveedores
- Transporte
- Ganancia Bruta
- % Ganancia

---

## 🔧 Cambios Técnicos

### **Archivo**: `utils/reportes.py`

**Antes**:
```python
if solo_pagadas:
    queryset = queryset.filter(pagado=True)

if fecha_inicio and fecha_fin:
    queryset = queryset.filter(fecha_pago__range=(fecha_inicio, fecha_fin))
```

**Después**:
```python
if campo_fecha == 'fecha_pago' and fecha_inicio and fecha_fin:
    # Buscar facturas con al menos un pago en el periodo
    from ventas.models import PagoFactura
    facturas_con_pagos_periodo = PagoFactura.objects.filter(
        fecha_pago__range=(fecha_inicio, fecha_fin)
    ).values_list('factura_id', flat=True).distinct()
    
    queryset = queryset.filter(id__in=facturas_con_pagos_periodo)
```

---

### **Archivo**: `ventas/views.py`

**Mejoras en `corte_flujo()`**:
- Obtiene todos los pagos en el periodo para cada factura
- Calcula total pagado en el periodo
- Incluye información detallada de pagos

**Nueva información en reporte**:
```python
reporte_dict["pagos_periodo"] = [
    {
        "fecha": "22-Dic-2025",
        "monto": 1000.00,
        "metodo": "efectivo"
    },
    # ...
]
```

---

### **Archivo**: `ventas/templates/ventas/corte.html`

**Nuevos elementos**:

1. **Columna de Checkboxes**:
```html
<th>
  <input type="checkbox" id="toggle-all" checked>
</th>
```

2. **Checkboxes por fila**:
```html
<tr class="factura-row" 
    data-total-venta="{{ item.total_venta }}"
    data-costo="{{ item.costo_proveedores }}"
    data-transporte="{{ item.transporte }}"
    data-ganancia="{{ item.ganancia }}">
  <td>
    <input type="checkbox" class="factura-checkbox" checked>
  </td>
  <!-- ... -->
</tr>
```

3. **IDs en totales** (para JavaScript):
```html
<th id="total-venta">...</th>
<th id="total-costo">...</th>
<th id="total-transporte">...</th>
<th id="total-ganancia">...</th>
<th id="total-porcentaje">...</th>
```

4. **JavaScript para recalcular**:
```javascript
function recalcularTotales() {
  let totalVenta = 0;
  // ... suma solo filas con checkbox activo
  
  document.querySelectorAll('.factura-row').forEach(row => {
    if (row.querySelector('.factura-checkbox').checked) {
      totalVenta += parseFloat(row.dataset.totalVenta);
      // ...
    }
  });
  
  // Actualizar DOM
  document.getElementById('total-venta').textContent = totalVenta.toFixed(2);
  // ...
}
```

---

## 🎬 Casos de Uso

### **Caso 1: Ver todo el flujo del periodo**
1. Seleccionar "Flujo (por fecha de pago)"
2. Elegir periodo: 15-Dic-2025 a 29-Dic-2025
3. Generar reporte
4. **Resultado**: Todas las facturas con pagos en ese periodo

### **Caso 2: Ver solo transferencias bancarias**
1. Generar reporte completo (Caso 1)
2. Identificar facturas pagadas en efectivo
3. Desactivar checkboxes de facturas en efectivo
4. **Resultado**: Totales reflejan solo transferencias

### **Caso 3: Analizar pagos específicos**
1. Generar reporte
2. Desactivar todas las facturas (click en checkbox de encabezado)
3. Activar solo las facturas de interés
4. **Resultado**: Totales de subconjunto seleccionado

---

## ✅ Tests y Validación

### **Test**: `test_corte_pagos_parciales.py`

**Resultados**:
```
[OK] Factura VPG1125-03 encontrada
     - 3 pagos parciales
     - Total: $3,883.00
     - Pagado: $3,135.00
     - Saldo: $748.00

[OK] Incluida en corte de flujo (15-Dic a 29-Dic)
[OK] Pagos en periodo: 2 ($2,200.00)
```

---

## 📊 Comparación Antes/Después

### **Antes**:
❌ Factura VPG1125-03 **NO aparecía** en corte de flujo  
❌ Solo facturas 100% pagadas con `pagado=True`  
❌ No se podía filtrar después de generar  
❌ Totales fijos  

### **Después**:
✅ Factura VPG1125-03 **SÍ aparece** en corte de flujo  
✅ Cualquier factura con pagos en el periodo  
✅ Checkboxes interactivos  
✅ Totales dinámicos en tiempo real  

---

## 🚀 Cómo Usar

1. **Iniciar servidor**:
   ```bash
   python manage.py runserver
   ```

2. **Navegar a**:
   ```
   Admin → Corte Semanal
   ```

3. **Seleccionar modo**: Flujo (por fecha de pago)

4. **Elegir periodo**: 15-Dic-2025 a 29-Dic-2025

5. **Generar Reporte**

6. **Interactuar**:
   - ✅ Checkbox encabezado: Toggle todo
   - ✅ Checkbox individual: Incluir/excluir factura
   - ✅ Totales se actualizan automáticamente

---

## 💡 Beneficios

1. **Mayor precisión**: Considera todos los pagos, no solo facturas cerradas
2. **Flexibilidad**: Filtra por método de pago post-generación
3. **Claridad**: Ve exactamente qué pagos entraron en el periodo
4. **Eficiencia**: No necesitas regenerar para ver diferentes vistas
5. **Trazabilidad**: Información detallada de cada pago

---

## 🎯 Próximas Mejoras Sugeridas

- [ ] Filtro por método de pago (efectivo/transferencia) automático
- [ ] Exportar solo facturas seleccionadas
- [ ] Guardar configuraciones de filtros
- [ ] Indicador visual de método de pago en cada fila
- [ ] Subtotales por método de pago

---

## ✨ Resumen Ejecutivo

**Sistema de corte mejorado** con:
- ✅ Pagos parciales correctamente incluidos
- ✅ Checkboxes interactivos
- ✅ Recalculación dinámica de totales
- ✅ 100% compatible con sistema existente

**Impacto**:
- Reportes más precisos
- Mayor control sobre qué ver
- Mejor toma de decisiones
- Separación efectivo/banco en segundos

---

© 2025 Sistema Novavino - Mejoras implementadas 23/Dic/2025
