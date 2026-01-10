# 📋 Guía: Reporte de Diferencias por Redondeo

## ✅ ¿Qué se Implementó?

### 1. **Fix del Total** (Mínimo e inocuo)
- **Archivo**: `ventas/utils/registrar_venta.py` (líneas 166-172)
- **Cambio**: Después de que los signals recalculan, restauramos el total del PDF
- **Impacto**: CERO riesgo - solo afecta a facturas nuevas procesadas desde Drive

### 2. **Reporte Mensual en Django Admin**
- Botón visible en la lista de Facturas: **"📋 Reporte de Diferencias"**
- Acceso directo desde el admin de Ventas

### 3. **Comando de Terminal**
- Para reportes automatizados o scripts
- Uso: `python manage.py reporte_diferencias_redondeo --mes 12 --año 2025`

---

## 📍 ¿Dónde Encontrar el Reporte?

### **Opción 1: Desde Django Admin** (Recomendado)

1. Entrar al admin: `http://localhost:8000/admin/`
2. Ir a **Ventas → Facturas**
3. En la barra superior derecha, click en: **"📋 Reporte de Diferencias"**
4. Seleccionar mes y año
5. Click en "Generar Reporte"

**Ruta directa**: 
```
http://localhost:8000/admin/ventas/factura/reporte-diferencias/
```

---

### **Opción 2: Desde Terminal**

```bash
# Reporte del mes actual
python manage.py reporte_diferencias_redondeo

# Reporte de diciembre 2025
python manage.py reporte_diferencias_redondeo --mes 12 --año 2025

# Mostrar todas las facturas (incluso sin diferencias)
python manage.py reporte_diferencias_redondeo --mes 12 --año 2025 --mostrar-todas
```

---

## 📊 ¿Qué Muestra el Reporte?

### Resumen Visual:
- **Total facturas analizadas**
- **Facturas con diferencia** (> $0.01)
- **Diferencia neta acumulada** (suma total)

### Tabla Detallada:
Para cada factura con diferencia:
- Folio
- Cliente
- Total facturado (del CFDI)
- Suma de productos (calculado)
- Diferencia (+/-)

### Registro Contable Sugerido:
Si hay diferencias, muestra la póliza contable:
```
Cargo:  Caja/Bancos              $X.XX
Abono:  Otros Ingresos - Redondeo  $X.XX
        (Diferencias por redondeo fiscal)
```

---

## 🎯 ¿Cuándo Usarlo?

### **Mensualmente** (Recomendado)
- Al cierre de mes, antes de entregar al contador
- Genera el reporte del mes cerrado
- Entrégaselo junto con tu reporte de ventas

### **Cuando notes diferencias en corte de caja**
- Si al cuadrar caja hay discrepancias
- El reporte te dirá si es por redondeos fiscales

### **Para auditorías**
- Tener registro de todas las diferencias
- Demostrar que las diferencias son por redondeos del SAT, no errores

---

## ❓ Preguntas Frecuentes

### ¿Las diferencias son un problema?
**NO**. Son normales y esperadas. El SAT calcula impuestos globalmente, nosotros por producto. Diferencias de centavos son inevitables.

### ¿Debo hacer algo con las diferencias?
Sí, reportarlas mensualmente a tu contador. Él hará una póliza de "Ajustes por Redondeo".

### ¿Se van a acumular?
No necesariamente. Algunas facturas tienen diferencias positivas, otras negativas. Tienden a compensarse.

### ¿El fix rompe algo existente?
**NO**. Solo afecta facturas procesadas DESPUÉS del fix. Las facturas existentes no cambian.

### ¿Funciona con facturas manuales?
Sí. Si editas detalles manualmente, los signals siguen funcionando. El total se actualiza automáticamente.

---

## 🔧 Verificación

### Probar que funciona:

1. **Reprocesar factura 1106**:
   ```bash
   # En el admin, ir a la factura 1106 y "Procesar desde Drive"
   # O ejecutar el procesador de Drive
   ```

2. **Verificar el total**:
   ```bash
   python -c "
   import django
   django.setup()
   from ventas.models import Factura
   f = Factura.objects.get(folio_factura='1106')
   print(f'Total: ${f.total}')
   # Debe mostrar: $14,651.08 (del PDF)
   "
   ```

3. **Generar reporte**:
   ```bash
   python manage.py reporte_diferencias_redondeo --mes 12 --año 2025
   ```

---

## 📝 Notas Importantes

### ✅ **LO QUE SÍ HACE EL FIX**:
- Guarda el total exacto del CFDI
- Hace que la caja cuadre con el dinero real
- Permite reportar diferencias para contabilidad

### ❌ **LO QUE NO HACE EL FIX**:
- NO modifica facturas existentes
- NO cambia el comportamiento de signals
- NO afecta ediciones manuales
- NO toca el módulo de compras
- NO modifica precios unitarios

### 🔐 **GARANTÍAS**:
- Cambio mínimo (7 líneas de código)
- No rompe funcionalidad existente
- Fácilmente reversible si hay problema
- Sigue mejores prácticas contables mexicanas

---

## 🆘 Soporte

Si encuentras algún problema:

1. Verifica que el reporte se genere correctamente
2. Compara una factura antes/después del fix
3. Si hay discrepancias mayores a $1.00, revisar

**Todo debe funcionar exactamente igual, solo con totales correctos del PDF** ✅
