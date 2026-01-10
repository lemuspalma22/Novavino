# Sistema de Productos No Reconocidos (PNR) para Ventas

## 🎯 Objetivo
Implementar un sistema análogo al de compras para manejar productos no reconocidos en facturas de ventas, permitiendo asignarlos a productos existentes y crear aliases, **sin permitir crear nuevos productos** (ya que en ventas el producto debe existir previamente en inventario).

## ✅ Completado

### 1. Modelo Factura (ventas/models.py) ✅
- Agregados campos:
  - `requiere_revision_manual` (BooleanField)
  - `estado_revision` (CharField con choices: pendiente/revisado_ok/revisado_con_cambios)
  - `uuid_factura` (CharField para vincular con PNR)
- Migración creada y aplicada: `0008_agregar_campos_revision`

### 2. Modificación de registrar_venta (ventas/utils/registrar_venta.py) ✅  
- **Antes**: Lanzaba `ValueError` y rechazaba toda la factura si un producto no se encontraba
- **Ahora**: 
  - Registra el producto no encontrado en `ProductoNoReconocido` con `origen="venta"`
  - Guarda cantidad y precio_unitario en el PNR
  - Marca la factura con `requiere_revision_manual=True`
  - Continúa procesando los demás productos
  - La factura se registra con estado `pendiente`

### 3. Vista asignar_pnr (ventas/views_pnr.py) ✅
- Creado archivo `ventas/views_pnr.py` con:
  - `asignar_pnr_venta_view`: asigna PNR a producto existente
  - Descuenta stock (en ventas se resta)
  - Crea DetalleFactura
  - Opcionalmente crea alias
  - **NO tiene opción de crear producto nuevo** (diferencia clave con compras)

## ⏳ Pendiente

### 4. Integración en Admin (ventas/admin.py) - EN PROGRESO
**Archivo restaurado a versión limpia**, necesita:

#### a) Imports
```python
from django.middleware.csrf import get_token
from inventario.models import Producto, ProductoNoReconocido
from .views_pnr import asignar_pnr_venta_view
```

#### b) list_display
Agregar: `"estado_detallado"` (muestra ⚠️ Pendiente (X PNR) o ✓ OK)

#### c) list_filter
Agregar: `"requiere_revision_manual"`, `"estado_revision"`

#### d) readonly_fields
Agregar: `"resumen_revision"` (el widget PNR)

#### e) actions
Agregar: `["marcar_revisado_ok", "marcar_revisado_con_cambios"]`

#### f) fieldsets
Agregar sección:
```python
("Estado de revisión", {
    "fields": ("resumen_revision", "requiere_revision_manual", "estado_revision"),
    "classes": ("wide",),
}),
```

#### g) get_urls()
Agregar URL:
```python
path('<int:object_id>/asignar_pnr/', self.admin_site.admin_view(asignar_pnr_venta_view), name='ventas_factura_asignar_pnr'),
```

#### h) change_view()
Guardar request para readonly_fields

#### i) Funciones nuevas
- `estado_detallado(self, obj)`: Muestra icono y contador de PNR
- `resumen_revision(self, obj)`: Widget HTML con:
  - Lista de PNR pendientes
  - Dropdown para seleccionar producto existente
  - Checkbox "Crear alias automáticamente"
  - Botón "Asignar"
  - **NO botón "Crear producto"** (diferencia con compras)
  - Lista de productos ya en la factura
  - Comparación de totales
- `marcar_revisado_ok(self, request, queryset)`: Acción en masa
- `marcar_revisado_con_cambios(self, request, queryset)`: Acción en masa

## 📋 Flujo Completo del Sistema

### Escenario: Factura con Producto No Reconocido

1. **Procesar Drive** → Se sube factura PDF con producto "Vino Tint0" (typo)
2. **Extractor** → Lee PDF, encuentra "Vino Tint0", cantidad 10, precio $500
3. **registrar_venta** → 
   - Busca "Vino Tint0" → NO encuentra
   - Crea PNR con origen="venta", cantidad=10, precio=500
   - Marca factura con `requiere_revision_manual=True`
   - Registra factura con detalles de productos que SÍ encontró
4. **Admin → Lista** → Factura aparece con ⚠️ "Pendiente (1 PNR)"
5. **Admin → Detalle** → Widget muestra:
   ```
   ⚠️ Productos no reconocidos sin procesar: 1
   
   ℹ️ Nota: En ventas NO se pueden crear productos nuevos.
        Solo puedes asignar a productos existentes...
   
   1. Vino Tint0
      Cant: 10 | P/U: $500.00 | Importe: $5,000.00
      
      [Dropdown: Seleccionar producto] "Vino Tinto 750ml"
      [✓] Crear alias automáticamente
      [Asignar]
   ```
6. **Usuario asigna** → Selecciona "Vino Tinto 750ml", hace clic en Asignar
7. **asignar_pnr_venta_view** →
   - Crea DetalleFactura (factura + Vino Tinto + cant:10 + precio:500)
   - Descuenta stock: Vino Tinto stock -= 10
   - Marca PNR como procesado
   - Crea alias: "Vino Tint0" → Vino Tinto
8. **Refresh** → Widget ahora muestra: "✓ Productos no reconocidos: 0 pendientes"
9. **Usuario marca** → Dropdown "Estado revisión" → "Revisado OK"

## 📊 Diferencias Clave con Compras

| Aspecto | Compras | Ventas |
|---------|---------|--------|
| Crear producto nuevo | ✅ SÍ (es entrada) | ❌ NO (debe existir) |
| Stock | Suma (+) | Resta (-) |
| Botones widget | Asignar + Crear | Solo Asignar |
| Nota explicativa | - | "En ventas NO se pueden crear productos nuevos" |
| Stock en dropdown | - | Muestra stock disponible |

## 🔧 Archivos Modificados

- ✅ `ventas/models.py` - Campos de revisión
- ✅ `ventas/migrations/0008_agregar_campos_revision.py` - Migración
- ✅ `ventas/utils/registrar_venta.py` - No rechazar, registrar PNR
- ✅ `ventas/views_pnr.py` - Vista asignar (sin crear)
- ⏳ `ventas/admin.py` - Widget PNR (pendiente integración)

## 🧪 Testing Pendiente

1. Procesar factura con producto no existente
2. Verificar que aparece en PNR con origen="venta"
3. Verificar que factura se marca como `requiere_revision_manual=True`
4. Verificar widget en admin muestra PNR
5. Asignar PNR a producto existente
6. Verificar que se crea DetalleFactura
7. Verificar que se descuenta stock
8. Verificar que se crea alias
9. Verificar que PNR se marca como procesado
10. Marcar factura como "Revisado OK"

## ✨ Beneficios

- ✅ **No pierde facturas**: Antes se rechazaban, ahora se procesan parcialmente
- ✅ **Trazabilidad**: Registra qué productos no se encontraron
- ✅ **Aliases automáticos**: Aprende variaciones de nombres
- ✅ **UI intuitiva**: Todo desde el admin, sin salir de la página
- ✅ **Seguridad**: No permite crear productos en ventas (lógica de negocio)
- ✅ **Coherente**: Mismo flujo que compras pero adaptado a ventas

## 📝 Próximo Paso

Integrar el código del widget PNR en `ventas/admin.py` de forma limpia y correcta.
