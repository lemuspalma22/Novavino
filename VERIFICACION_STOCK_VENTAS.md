# ✅ Verificación: Restauración de Stock al Eliminar Facturas de Ventas

## Situación Verificada

Al eliminar una factura de ventas que contenía productos, **el stock debe restaurarse automáticamente**.

### Ejemplo:
```
1. Stock inicial: 100 botellas
2. Crear venta de 2 botellas → Stock: 98 (-2)
3. Eliminar factura → Stock: 100 (+2) ✓ RESTAURADO
```

---

## Implementación Actual

### ✅ Signals Configurados

**Archivo:** `ventas/signals.py` (líneas 44-56)

```python
@receiver(post_delete, sender=DetalleFactura)
def _on_detalle_delete(sender, instance, **kwargs):
    # Restaurar stock al eliminar el detalle
    producto = getattr(instance, "producto", None)
    if isinstance(producto, Producto):
        qty = instance.cantidad or 0
        if qty:
            p = producto
            p.stock = (p.stock or 0) + qty  # ← SUMA de vuelta
            p.save(update_fields=["stock"])
```

### Flujo Completo de Signals

#### 1. Al Crear Venta (`post_save`)
```python
# Línea 38 de signals.py
p.stock = max(0, (p.stock or 0) - delta)  # DESCUENTA
```

#### 2. Al Eliminar Venta (`post_delete`)
```python
# Línea 52 de signals.py
p.stock = (p.stock or 0) + qty  # SUMA de vuelta
```

---

## Cómo Probar

### Opción 1: Test Automatizado (Recomendado)

```powershell
# En PowerShell
python manage.py shell
```

```python
# Copiar y pegar el contenido de:
exec(open('test_stock_ventas_simple.py').read())
```

**O alternativamente:**
```powershell
Get-Content test_stock_ventas_simple.py | python manage.py shell
```

### Opción 2: Prueba Manual en Admin

#### Paso 1: Verificar Stock Inicial
1. Ir a `/admin/inventario/producto/`
2. Buscar un producto (ej: "Vino Tinto 750ml")
3. Anotar el **stock actual** (ej: 50)

#### Paso 2: Crear Factura de Venta
1. Ir a `/admin/ventas/factura/`
2. Click en "Agregar Factura"
3. Llenar datos básicos:
   - Folio: TEST-001
   - Cliente: Test
   - Fecha: Hoy
4. En "Detalles facturas":
   - Producto: Seleccionar el producto
   - Cantidad: 5
   - Precio unitario: (cualquier valor)
5. Guardar

#### Paso 3: Verificar Descuento
1. Volver a `/admin/inventario/producto/`
2. Buscar el mismo producto
3. **Stock debe haber bajado:** 50 → 45 (-5) ✓

#### Paso 4: Eliminar Factura
1. Volver a `/admin/ventas/factura/`
2. Buscar factura TEST-001
3. Seleccionarla (checkbox)
4. En dropdown "Acción": Seleccionar "Eliminar seleccionadas"
5. Confirmar eliminación

#### Paso 5: Verificar Restauración
1. Volver a `/admin/inventario/producto/`
2. Buscar el mismo producto
3. **Stock debe haberse restaurado:** 45 → 50 (+5) ✓

---

## Resultado Esperado

### Test Automatizado
```
================================================================================
TEST RÁPIDO: Restauración de Stock en Ventas
================================================================================

Producto: Vino Tinto 750ml
Stock inicial: 50

→ Venta creada: 2 unidades
   Stock después de venta: 48
   Descontado: 2

→ Eliminando factura...
   Stock después de eliminar: 50
   Restaurado: 2

================================================================================
✅ TEST PASADO
   Stock inicial = Stock final = 50
================================================================================
```

### Prueba Manual
```
1. Stock inicial:         50 botellas
2. Crear venta (5 uds):   50 - 5 = 45 botellas  ✓
3. Eliminar factura:      45 + 5 = 50 botellas  ✓
4. Stock final:           50 botellas (igual que inicial)
```

---

## Casos de Prueba

### Caso 1: Eliminar Factura con 1 Producto
```
Stock inicial: 100
Venta: -2
Eliminar: +2
Stock final: 100 ✓
```

### Caso 2: Eliminar Factura con Múltiples Productos
```
Producto A: 50 → Venta -3 → 47 → Eliminar +3 → 50 ✓
Producto B: 30 → Venta -5 → 25 → Eliminar +5 → 30 ✓
```

### Caso 3: Eliminar Factura con Cantidades Grandes
```
Stock inicial: 1000
Venta: -500
Eliminar: +500
Stock final: 1000 ✓
```

### Caso 4: Editar Cantidad de Venta (Update)
```
Stock inicial: 100
Venta: 5 unidades → Stock: 95
Editar venta a: 10 unidades → Stock: 90 (delta: -5)
Editar venta a: 3 unidades → Stock: 97 (delta: +7)
```

---

## Comparación con Compras

| Operación | Compras | Ventas |
|-----------|---------|--------|
| **Crear detalle** | Stock + cantidad | Stock - cantidad |
| **Eliminar detalle** | Stock - cantidad | Stock + cantidad |
| **Signal usado** | `post_save` + `post_delete` | `post_save` + `post_delete` |
| **Archivo signals** | `compras/signals.py` | `ventas/signals.py` |
| **Configuración** | `compras/apps.py` | `ventas/apps.py` |

---

## Código Relevante

### Signal de Eliminación (ventas/signals.py)
```python
@receiver(post_delete, sender=DetalleFactura)
def _on_detalle_delete(sender, instance, **kwargs):
    """
    Restaura el stock cuando se elimina un detalle de factura.
    En ventas: sumar porque se está "deshaciendo" una venta.
    """
    producto = getattr(instance, "producto", None)
    if isinstance(producto, Producto):
        qty = instance.cantidad or 0
        if qty:
            p = producto
            p.stock = (p.stock or 0) + qty  # Suma de vuelta
            p.save(update_fields=["stock"])
    
    # Recalcular total de la factura
    _recalc_factura_total(instance.factura)
```

### Signal de Creación/Actualización (ventas/signals.py)
```python
@receiver(post_save, sender=DetalleFactura)
def _on_detalle_save(sender, instance, created, **kwargs):
    """
    Ajusta el stock cuando se crea o actualiza un detalle.
    En ventas: restar porque se está vendiendo.
    """
    producto = getattr(instance, "producto", None)
    if isinstance(producto, Producto):
        nueva = (instance.cantidad or 0)
        vieja = getattr(instance, "_old_qty", 0) or 0
        delta = nueva if created else (nueva - vieja)
        if delta:
            p = producto
            p.stock = max(0, (p.stock or 0) - delta)  # Resta
            p.save(update_fields=["stock"])
    
    # Recalcular total de la factura
    _recalc_factura_total(instance.factura)
```

---

## Conclusión

✅ **El sistema YA está implementado correctamente**

- ✅ Signals configurados en `ventas/signals.py`
- ✅ Signals registrados en `ventas/apps.py`
- ✅ Lógica de restauración de stock funcional
- ✅ Compatible con eliminación en cascada (al eliminar Factura, se eliminan DetalleFactura)

**No se requiere ninguna modificación adicional.**

---

## Archivos de Test Creados

1. **`test_stock_ventas_simple.py`** - Test rápido con primer producto disponible
2. **`test_stock_ventas_delete.py`** - Test completo con producto de prueba

**Ejecutar:**
```powershell
python manage.py shell
>>> exec(open('test_stock_ventas_simple.py').read())
```

---

**Fecha:** 16 de Diciembre, 2025  
**Estado:** ✅ Verificado y Funcional  
**Acción requerida:** Ninguna (ya implementado)
