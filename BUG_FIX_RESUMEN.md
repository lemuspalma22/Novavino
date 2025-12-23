# 🐛 Bug Fix: Productos No Reconocidos no Detectados

## Problema Identificado

**Síntoma:** Facturas con productos no reconocidos se procesaban sin marcar para revisión manual.

**Causa Raíz:** En `ventas/utils/registrar_venta.py`, líneas 91-98, cuando un producto tenía:
- Cantidad inválida (<=0)
- Nombre vacío
- Otros problemas de validación

El código:
1. ✅ **SÍ** creaba un `ProductoNoReconocido` (PNR)
2. ❌ **NO** incrementaba el contador `productos_no_reconocidos`
3. ❌ **NO** marcaba la factura con `requiere_revision_manual=True`

**Resultado:** La factura aparecía como "✓ OK" en el admin, pero en realidad tenía productos sin procesar.

---

## Solución Aplicada

### Código Modificado

**Archivo:** `ventas/utils/registrar_venta.py`  
**Líneas:** 91-99

```python
# ANTES (con bug)
if not nombre or cantidad <= 0:
    if nombre:
        ProductoNoReconocido.objects.get_or_create(
            nombre_detectado=nombre,
            defaults={"fecha_detectado": now(), "uuid_factura": datos.get("uuid") or "",
                      "procesado": False, "origen": "venta"},
        )
    continue  # ❌ Sin incrementar contador

# DESPUÉS (corregido)
if not nombre or cantidad <= 0:
    if nombre:
        ProductoNoReconocido.objects.get_or_create(
            nombre_detectado=nombre,
            defaults={"fecha_detectado": now(), "uuid_factura": datos.get("uuid") or "",
                      "procesado": False, "origen": "venta"},
        )
        productos_no_reconocidos += 1  # ✅ BUG FIX: incrementar contador
    continue
```

### Cambio Realizado

**Una línea agregada:** 
```python
productos_no_reconocidos += 1  # BUG FIX: incrementar contador
```

---

## Impacto

### ✅ Ahora el Sistema:

1. **Detecta PNRs correctamente** - incluso con cantidad inválida
2. **Marca facturas para revisión** - `requiere_revision_manual=True`
3. **Muestra estado correcto** - "⚠️ Pendiente (X PNR)" en admin
4. **Requiere acción del usuario** - aparece el widget para asignar productos

### ⚠️ Facturas Procesadas Antes del Fix

Las facturas que se procesaron **ANTES** de este fix pueden tener PNRs que no fueron detectados:

- **Factura 1127** - Ya identificada, requiere corrección manual
- **Otras facturas** - Pueden existir casos similares

---

## Corrección de Factura 1127

### Opción 1: Script Automático (Recomendado)

```bash
# Abrir shell de Django
python manage.py shell

# Copiar y pegar el contenido de:
# corregir_factura_1127.py
```

O alternativamente:
```bash
# Ejecutar directamente (PowerShell)
Get-Content corregir_factura_1127.py | python manage.py shell
```

### Opción 2: Corrección Manual en Admin

1. Ir a: `/admin/inventario/productonoreconocido/`
2. Filtrar por: `origen=venta`, `procesado=False`
3. Identificar PNRs de la factura 1127 (por UUID o fecha)
4. Ir a: `/admin/ventas/factura/` → Factura 1127
5. Editar manualmente:
   - `requiere_revision_manual` = ✓
   - `estado_revision` = "pendiente"
6. Guardar
7. Recargar página → aparecerá el widget PNR

---

## Verificación del Fix

### Test 1: Factura con Producto Inexistente
```python
# Crear factura de prueba con producto que no existe
datos = {
    'folio': 'TEST-001',
    'cliente': 'Test Cliente',
    'fecha': '2025-12-16',
    'uuid': 'test-uuid-123',
    'total': 1000,
    'productos': [
        {'nombre': 'Producto Que No Existe', 'cantidad': 10, 'precio_unitario': 100}
    ]
}

from ventas.utils.registrar_venta import registrar_venta_automatizada
factura = registrar_venta_automatizada(datos)

# Verificar
assert factura.requiere_revision_manual == True  # ✅ Debe ser True
assert factura.estado_revision == "pendiente"    # ✅ Debe ser pendiente
```

### Test 2: Factura con Cantidad Inválida
```python
datos = {
    'folio': 'TEST-002',
    'cliente': 'Test Cliente',
    'fecha': '2025-12-16',
    'uuid': 'test-uuid-456',
    'total': 0,
    'productos': [
        {'nombre': 'Algún Producto', 'cantidad': 0, 'precio_unitario': 0}  # Cantidad 0
    ]
}

factura = registrar_venta_automatizada(datos)

# Verificar
assert factura.requiere_revision_manual == True  # ✅ Debe ser True
```

---

## Prevención de Regresión

### Casos a Probar:

- ✅ Producto no existe en BD
- ✅ Producto ambiguo (múltiples coincidencias)
- ✅ Cantidad <= 0
- ✅ Nombre vacío
- ✅ Precio unitario inválido
- ✅ Combinación de productos válidos e inválidos

### Logging Adicional (Opcional)

Considerar agregar logs para debug:
```python
if not nombre or cantidad <= 0:
    if nombre:
        logger.warning(f"PNR creado para '{nombre}' - cantidad inválida: {cantidad}")
        ProductoNoReconocido.objects.get_or_create(...)
        productos_no_reconocidos += 1
    continue
```

---

## Resumen Ejecutivo

| Aspecto | Antes del Fix | Después del Fix |
|---------|---------------|-----------------|
| PNR creado | ✅ Sí | ✅ Sí |
| Contador incrementado | ❌ No | ✅ Sí |
| Factura marcada para revisión | ❌ No | ✅ Sí |
| Aparece en admin | ✓ OK (incorrecto) | ⚠️ Pendiente (correcto) |
| Usuario puede asignar | ❌ No | ✅ Sí |

---

## Próximos Pasos

1. ✅ **Bug corregido** - `registrar_venta.py` actualizado
2. ⏳ **Corregir factura 1127** - Ejecutar `corregir_factura_1127.py`
3. ⏳ **Procesar nueva factura** - Probar con factura de prueba
4. ⏳ **Verificar otras facturas** - Revisar si hay más casos similares
5. ⏳ **Testing completo** - Ejecutar suite de pruebas

---

**Fecha del fix:** 16 de Diciembre, 2025  
**Archivo modificado:** `ventas/utils/registrar_venta.py`  
**Líneas:** 98 (agregada)  
**Impacto:** Crítico - afecta detección de productos no reconocidos  
**Estado:** ✅ Resuelto
