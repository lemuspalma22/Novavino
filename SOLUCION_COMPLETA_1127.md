# 🎯 Solución Completa - Bug Factura 1127

## Problema Identificado

La factura 1127 **NO detectaba productos** y se procesaba como "OK" sin warnings.

### Causa Raíz (2 bugs)

#### Bug #1: Contador de PNR no se incrementaba
**Archivo:** `ventas/utils/registrar_venta.py`  
**Línea:** 98 (faltaba)

Cuando un producto tenía cantidad inválida, se creaba el PNR pero NO se incrementaba el contador, por lo que la factura no se marcaba para revisión.

**Fix aplicado:**
```python
productos_no_reconocidos += 1  # ← Línea agregada
```

#### Bug #2: Regex de unidades demasiado restrictivo ⭐ **PROBLEMA REAL**
**Archivo:** `ventas/extractors/novavino.py`  
**Línea:** 9

El regex UNIT_RE solo aceptaba MAYÚSCULAS:
```python
# ANTES (bug)
UNIT_RE = re.compile(r"^[A-Z0-9]{1,}(?:\s*-\s*[A-Z0-9]{1,})?$")
```

Esto rechazaba unidades como "H87 - Bot" porque "Bot" tiene minúsculas.

**Fix aplicado:**
```python
# DESPUÉS (corregido)
UNIT_RE = re.compile(r"^[A-Za-z0-9]{1,}(?:\s*-\s*[A-Za-z0-9]{1,})?$", re.IGNORECASE)
```

---

## Impacto

### Antes de los Fixes
```
Factura 1127 procesada
├─ Productos detectados: 0       ❌
├─ PNRs creados: 0                ❌
├─ Estado: ✓ OK                   ❌ (incorrecto)
└─ Widget: "Todo resuelto"        ❌ (falso positivo)
```

### Después de los Fixes
```
Factura 1127 procesada
├─ Productos detectados: 1        ✅
│  └─ "bot anécdota espumoso personalizado épico"
├─ PNRs creados: 1 (si no existe) ✅
├─ Estado: ⚠️ Pendiente (1 PNR)   ✅
└─ Widget: Formulario asignación  ✅
```

---

## Pasos para Aplicar la Solución

### 1. ⚠️ REINICIAR SERVIDOR DJANGO (CRÍTICO)

**Los cambios en Python NO se aplican automáticamente.**

```powershell
# En la terminal donde corre el servidor:
# Presiona Ctrl+C para detener

# Luego reinicia:
python manage.py runserver
```

### 2. Eliminar Factura 1127 (si ya existe)

```powershell
# Abrir shell
python manage.py shell
```

```python
# Copiar y pegar:
from ventas.models import Factura
try:
    f = Factura.objects.get(folio_factura='1127')
    f.delete()
    print("Factura 1127 eliminada")
except:
    print("Factura no existe")
```

### 3. Procesar PDF de Nuevo

1. Colocar el PDF en la carpeta de Drive "Facturas Ventas Nuevas"
2. En admin: Click en "→ PROCESAR FACTURAS DESDE DRIVE"
3. Verificar output en consola del servidor

**Deberías ver:**
```
[DEBUG Producto]
  Nombre: bot anécdota espumoso personalizado épico
  Cantidad: 36.00
  Precio base: 196.95
  ...
  Precio final con impuestos: 289.00
```

### 4. Verificar en Admin

1. Ir a: `/admin/ventas/factura/`
2. Buscar factura 1127
3. Debe mostrar:
   - **Estado revisión:** ⚠️ Pendiente (1 PNR)
   - Al abrirla: Widget con producto "bot anécdota..."

---

## Verificación de la Solución

### Test 1: Verificar Extracción
```powershell
python analizar_factura_1127.py
```

**Resultado esperado:**
```
PRODUCTOS DETECTADOS: 1

1. bot anécdota espumoso personalizado épico
   Cantidad: 36.00
   Precio unitario: $289.00
```

### Test 2: Verificar si Producto Existe en BD

```python
# En shell de Django
from inventario.utils import encontrar_producto_unico

producto, error = encontrar_producto_unico("bot anecdota espumoso personalizado epico")

if error == "not_found":
    print("NO EXISTE → Se creará PNR ✓")
elif error:
    print(f"AMBIGUO → Se creará PNR ✓")
else:
    print(f"EXISTE: {producto.nombre} → Se asignará directamente ✓")
```

### Test 3: Procesar y Verificar

1. Procesar factura desde Drive
2. Verificar en consola que detecta producto
3. Verificar en admin:
   - Si NO existe → ⚠️ Pendiente (1 PNR)
   - Si SÍ existe → ✓ OK (0 PNR)

---

## Archivos Modificados

### 1. `ventas/utils/registrar_venta.py`
**Línea 98** - Agregada:
```python
productos_no_reconocidos += 1  # BUG FIX: incrementar contador
```

### 2. `ventas/extractors/novavino.py`
**Línea 9** - Modificada:
```python
UNIT_RE = re.compile(r"^[A-Za-z0-9]{1,}(?:\s*-\s*[A-Za-z0-9]{1,})?$", re.IGNORECASE)
```

---

## Casos de Prueba Adicionales

### Unidades que ahora funcionan:
- ✅ "H87 - Bot" (antes fallaba)
- ✅ "PZA"
- ✅ "KG"
- ✅ "LT - Litro"
- ✅ "Bot - Botella"

### Facturas que ahora se procesarán correctamente:
- ✅ Facturas con unidades en formato mixto mayúsculas/minúsculas
- ✅ Facturas con productos no existentes (crearán PNR)
- ✅ Facturas con cantidades inválidas (crearán PNR)

---

## Resumen Ejecutivo

| Aspecto | Antes | Ahora |
|---------|-------|-------|
| **Detección de productos** | ❌ 0 detectados | ✅ 1 detectado |
| **Unidades mixtas (H87 - Bot)** | ❌ Rechazadas | ✅ Aceptadas |
| **PNR creado** | ❌ No (bug extractor) | ✅ Sí (si no existe) |
| **Factura marcada para revisión** | ❌ No | ✅ Sí (si PNR) |
| **Estado en admin** | ✓ OK (falso) | ⚠️ Pendiente (correcto) |

---

## Próximos Pasos

1. ✅ **Bugs corregidos** - `registrar_venta.py` + `novavino.py`
2. ⏳ **REINICIAR SERVIDOR** - ⚠️ CRÍTICO para aplicar cambios
3. ⏳ **Eliminar factura 1127** - Para reprocesar limpiamente
4. ⏳ **Procesar de nuevo** - Desde Drive o manualmente
5. ⏳ **Verificar en admin** - Debe aparecer PNR
6. ⏳ **Asignar producto** - Usando widget en admin

---

**Fecha:** 16 de Diciembre, 2025  
**Bugs corregidos:** 2  
**Archivos modificados:** 2  
**Estado:** ✅ Listo para pruebas  
**Acción requerida:** REINICIAR SERVIDOR DJANGO
