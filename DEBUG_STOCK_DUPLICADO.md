# 🐛 DEBUG: Stock Duplicado en Productos Nuevos desde Widget

## ❌ Problema Detectado

Al crear productos nuevos directamente desde el widget de PNR (Productos No Reconocidos), el stock se está duplicando:

- **Cantidad extraída del PDF**: 120 unidades ✅
- **Stock en BD**: 240 unidades ❌ (el doble)
- **CompraProducto registrado**: 1 con 120 unidades ✅

### Productos Afectados (Corregidos)

1. ✅ V.T. BACALAUH SAUVGNON BLANC 750 ML: 240 → 120
2. ✅ V.T. EPICO AN ESPUMOSO BLANCO 750 ML: 240 → 120
3. ✅ Alba Vega Albariño: 12 → 6
4. ✅ Anécdota Chenin Blanc: 24 → 12
5. ✅ Y otros 7 productos más...

---

## 🔍 Hipótesis de la Causa

Hay **DOS puntos** donde se suma stock en el flujo:

### 1. `registrar_compra.py` (líneas 98-112)
```python
# Cuando encuentra un producto existente, suma stock aquí
producto.stock = (producto.stock or 0) + inc
producto.save(update_fields=["stock"])
```

### 2. `inventario/signals.py` + `procesar_a_stock()`
```python
# Signal post_save de PNR → llama procesar_a_stock()
# que TAMBIÉN suma stock (líneas 175-182)
prod.stock = (prod.stock or 0) + int(cant)
prod.save(update_fields=["stock"])
```

### Escenario Probable de Duplicación:

1. **Factura procesada** → PNR creado (producto no existe)
2. **Usuario crea producto desde widget** → Producto creado, PNR actualizado
3. **Signal se dispara** → `procesar_a_stock()` suma 120 al stock
4. **`registrar_compra` ya había sumado?** → O el producto se creó durante el procesamiento y también sumó

---

## 🛠️ Cambios Implementados

### ✅ Eliminada duplicación en `conciliar_view()`
- Antes: Llamaba `obj.procesar_a_stock()` manualmente
- Ahora: Solo el signal maneja el procesamiento

### ✅ Agregado Logging Detallado
En los siguientes archivos:
1. `inventario/signals.py` - Logs del signal post_save
2. `inventario/models.py` (`procesar_a_stock`) - Logs de suma de stock
3. `compras/utils/registrar_compra.py` - Logs cuando encuentra producto

---

## 📋 INSTRUCCIONES PARA PRÓXIMA FACTURA

**Cuando proceses la próxima factura que tenga un producto nuevo:**

1. **ANTES de crear el producto en el widget**, revisa la consola de Django
2. Copia **TODOS** los logs que contengan:
   - `[registrar_compra]`
   - `[SIGNAL]`
   - `[procesar_a_stock]`
3. Envíamelos para analizar el flujo completo

### ⚠️ Nota sobre el Checkbox "Crear alias"
Mencionaste que "se queda prendida la palomita de asignar alias". Esto NO debería causar duplicación, pero aún así:
- Verifica que el alias se cree correctamente
- Si ves comportamiento extraño, reporta

---

## 🔧 Scripts de Corrección Creados

1. `corregir_bacalauh.py` - Corrige stock de producto específico
2. `revisar_todos_productos.py` - Detecta y corrige duplicaciones exactas (2x)
3. `corregir_epico.py` - Corrige EPICO y marca PNR
4. `debug_epico.py` - Analiza extracción y estado del producto

---

## 🎯 Próximos Pasos

1. **Procesar nueva factura con producto nuevo**
2. **Capturar logs completos**
3. **Analizar flujo real** para confirmar hipótesis
4. **Implementar fix definitivo** basado en evidencia

---

## ⚡ Corrección Inmediata

Si ves otro producto duplicado AHORA:

```bash
# Ejecuta este script (reemplaza NOMBRE_PRODUCTO)
python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()
from inventario.models import Producto
from compras.models import CompraProducto

p = Producto.objects.filter(nombre__icontains='NOMBRE_PRODUCTO').first()
if p:
    stock_correcto = sum(cp.cantidad for cp in CompraProducto.objects.filter(producto=p))
    if p.stock != stock_correcto:
        print(f'Corrigiendo {p.nombre}: {p.stock} -> {stock_correcto}')
        p.stock = stock_correcto
        p.save(update_fields=['stock'])
"
```

---

**Fecha**: 16 de diciembre 2025
**Status**: 🟡 Investigación en curso - Logs agregados para próxima factura
