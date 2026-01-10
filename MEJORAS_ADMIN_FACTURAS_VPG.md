# MEJORAS ADMIN DE FACTURAS - SISTEMA VPG

## 📋 Resumen de Cambios Implementados

Se implementó un sistema completo para gestionar **Ventas Público General (VPG)** con mejoras significativas en el admin de facturas, incluyendo filtros avanzados, ordenamiento cronológico y generación automática de folios VPG.

---

## ✅ Funcionalidades Implementadas

### 1. **Sistema VPG (Venta Público General)**

#### Campos Nuevos en Modelo `Factura`:
- `es_vpg` (Boolean): Marca si es una VPG
- `folio_vpg_anio` (Integer): Año del folio VPG (2025, 2026...)
- `folio_vpg_numero` (Integer): Número consecutivo en el año

#### Generación Automática de Folios:
- Formato: **VPG26-1, VPG26-2, VPG26-3...**
- Consecutivo se reinicia cada año
- Se genera automáticamente al guardar

#### Propiedades Nuevas:
- `tipo_venta`: Retorna "VPG" o "Factura"
- `folio_display`: Retorna el folio formateado

---

### 2. **Mejoras en Admin de Facturas**

#### Columna Nueva: **Tipo de Venta**
- Badge visual: 🏢 Factura (azul) / 👥 VPG (verde)
- Permite identificar rápidamente el tipo de venta

#### Ordenamiento Cronológico:
- Por defecto: `-fecha_facturacion, -id`
- VPG y facturas normales aparecen mezcladas por fecha
- Respeta el orden temporal real de las ventas

#### Búsqueda Mejorada:
- Busca en: `folio_factura`, `cliente`, `uuid_factura`, `notas`
- Ejemplo: Buscar "VPG" muestra todas las VPG
- Ejemplo: Buscar "1142" encuentra la factura 1142

---

### 3. **Filtros Personalizados**

#### Filtro: **Tipo de Venta**
- Factura
- VPG

#### Filtro: **Estado de Pago**
- PAGADA: Completamente pagada
- PARCIAL: Con pagos pero saldo pendiente
- PENDIENTE: Sin pagos, no vencida
- VENCIDA: Sin pagar y vencimiento pasado

#### Filtro: **Vencimiento**
- Vencidas
- Por vencer en 7 días
- Por vencer en 15 días
- Por vencer en 30 días

#### Filtro: **Método de Pago (Pagos)**
- Filtra por método de pago de los pagos registrados
- Efectivo, Transferencia, Cheque, Tarjeta, Depósito, Otro

#### Filtros Existentes Mantenidos:
- Método de pago (PUE/PPD)
- Fecha de facturación
- Requiere revisión manual
- Estado de revisión

---

### 4. **Dos Formas de Crear VPG**

#### Opción A: Checkbox en Formulario Normal
1. Admin → Facturas → Agregar Factura
2. Marcar: ☑ **Es Venta Público General**
3. El campo folio se vuelve readonly automáticamente
4. Mensaje: "El folio VPG se generará automáticamente"
5. Llenar datos y guardar
6. Sistema genera: VPG26-X

#### Opción B: Botón Dedicado "Agregar VPG"
1. Admin → Facturas → Click **"👥 Agregar VPG"** (botón verde)
2. Formulario simplificado con solo campos esenciales:
   - Cliente (obligatorio)
   - Fecha de facturación (obligatorio)
   - Total (obligatorio)
   - Subtotal (opcional)
   - Descuento (opcional)
   - Vencimiento (opcional, se calcula automáticamente)
   - Método de pago
   - Notas
3. Guardar → Sistema genera folio automáticamente
4. Redirige al detalle de la VPG creada

---

## 📊 Vista de Lista Mejorada

### Columnas Visibles:
```
Tipo | Folio | Cliente | Total | Pagado | Saldo | Estado Pago | Fecha Emisión | Vencimiento | Método Pago | Estado Revisión
```

### Ejemplo Visual:
```
👥 VPG    VPG26-3   Barbara Aldana    $2,261    $2,261    $0.00    ✅ PAGADA      2026-01-09    2026-01-24    PUE    ✓ OK
🏢 Fact   1144      Enoch Cruz        $4,740    $0.00     $4,740   ⏳ PENDIENTE   2026-01-09    2026-01-24    PPD    ✓ OK
🏢 Fact   1143      GERDOBA REST.     $8,670    $5,000    $3,670   ⚠️ PARCIAL     2026-01-09    2026-01-24    PPD    ✓ OK
```

---

## 🔄 Flujos de Trabajo

### Flujo 1: Procesar Facturas desde Drive (Sin cambios)
```
1. python process_drive_sales.py
2. Se extraen facturas normales del PDF
3. Folio viene del PDF (1140, 1141, etc.)
4. es_vpg = False (automático)
5. Aparecen en lista ordenadas por fecha
```

### Flujo 2: Crear VPG con Checkbox
```
1. Admin → Facturas → Agregar Factura
2. Marcar: ☑ Es Venta Público General
3. Llenar: Cliente, Total, Fecha
4. Guardar
5. Sistema genera: VPG26-4 (automático)
6. Aparece en lista ordenada por fecha
```

### Flujo 3: Crear VPG con Botón Dedicado
```
1. Admin → Facturas → Click "👥 Agregar VPG"
2. Formulario simplificado
3. Llenar datos
4. Guardar
5. Sistema genera: VPG26-5 (automático)
6. Redirige al detalle de la VPG
```

### Flujo 4: Buscar Facturas Vencidas de Cliente
```
1. Filtro Cliente: "BAHIA CHELEM"
2. Filtro Estado Pago: "VENCIDA"
3. Ver resultados
4. Seleccionar → Exportar a Excel (si necesario)
```

### Flujo 5: Ver Solo VPG del Año Actual
```
1. Filtro Tipo: "VPG"
2. Filtro Fecha: Año 2026
3. Ver todas las VPG de 2026
4. Analítica: Cuántas VPG, total vendido, etc.
```

---

## 🗂️ Archivos Modificados/Creados

### Archivos Modificados:
1. **`ventas/models.py`**
   - Agregados campos: `es_vpg`, `folio_vpg_anio`, `folio_vpg_numero`
   - Método: `generar_folio_vpg()`
   - Propiedades: `tipo_venta`, `folio_display`
   - Modificado `save()` para generar folio VPG automáticamente

2. **`ventas/admin.py`**
   - Agregada columna: `tipo_venta_display`
   - Modificado `list_display` con nueva columna Tipo
   - Modificado `list_filter` con filtros personalizados
   - Agregado `ordering` cronológico
   - Agregado campo `es_vpg` en fieldsets
   - Agregada URL para vista VPG
   - Agregado Media class con JavaScript

### Archivos Creados:
1. **`ventas/admin_filters.py`**
   - `EstadoPagoFilter`: Filtro por estado de pago
   - `VencimientoFilter`: Filtro por vencimiento
   - `TipoVentaFilter`: Filtro por tipo (Factura/VPG)
   - `MetodoPagoRegistradoFilter`: Filtro por método de pago

2. **`ventas/views_vpg.py`**
   - Vista `agregar_vpg_view`: Formulario simplificado para VPG

3. **`ventas/static/js/admin_vpg_form.js`**
   - JavaScript para manejar checkbox VPG
   - Hace readonly el campo folio cuando se marca VPG
   - Muestra mensaje informativo

4. **`ventas/templates/admin/ventas/agregar_vpg.html`**
   - Template del formulario simplificado de VPG

5. **`ventas/templates/admin/ventas/factura/change_list.html`**
   - Template personalizado con botón "Agregar VPG"

6. **`ventas/migrations/0013_factura_es_vpg_factura_folio_vpg_anio_and_more.py`**
   - Migración de BD con nuevos campos

### Scripts de Prueba:
1. **`test_vpg_funcionalidad.py`**
   - Tests completos de funcionalidad VPG

2. **`limpiar_facturas_prueba.py`**
   - Limpieza de facturas de prueba

---

## ✅ Tests Realizados

### Test 1: Crear VPG con Folio Automático
- ✅ VPG creada correctamente
- ✅ Folio generado: VPG26-1
- ✅ Formato correcto

### Test 2: Crear Factura Normal
- ✅ Factura normal funciona igual que antes
- ✅ No se genera folio VPG
- ✅ Campos VPG quedan en NULL

### Test 3: Consecutivo VPG
- ✅ Consecutivo se incrementa correctamente
- ✅ VPG26-1 → VPG26-2 → VPG26-3

### Test 4: Ordenamiento Cronológico
- ✅ VPG y facturas mezcladas por fecha
- ✅ Más recientes primero

### Test 5: Propiedades del Modelo
- ✅ `tipo_venta` retorna "VPG" o "Factura"
- ✅ `folio_display` retorna folio correcto

---

## 🎯 Compatibilidad con Sistema Existente

### ✅ NO SE ROMPIÓ NADA:
- ✅ Facturas normales siguen funcionando igual
- ✅ Procesamiento desde Drive sin cambios
- ✅ Sistema de pagos parciales intacto
- ✅ Complementos de pago funcionando
- ✅ Productos no reconocidos (PNR) sin cambios
- ✅ Todas las propiedades calculadas funcionando
- ✅ Inlines de DetalleFactura y PagoFactura intactos

### ✅ MEJORAS ADICIONALES:
- ✅ Filtros más potentes
- ✅ Búsqueda mejorada
- ✅ Ordenamiento cronológico
- ✅ Indicadores visuales claros

---

## 📝 Uso Diario

### Para Crear una VPG:
1. **Método Rápido**: Click en "👥 Agregar VPG" → Llenar formulario → Guardar
2. **Método Completo**: Agregar Factura → Marcar checkbox VPG → Llenar todo → Guardar

### Para Buscar Facturas:
- **Por folio**: Buscar "1142" o "VPG26-3"
- **Por cliente**: Buscar "BAHIA"
- **Por tipo**: Filtro "Tipo de Venta" → VPG o Factura
- **Por estado**: Filtro "Estado de Pago" → PAGADA/PARCIAL/PENDIENTE/VENCIDA
- **Por vencimiento**: Filtro "Vencimiento" → Vencidas / Por vencer

### Para Ver Estadísticas:
- Filtrar por tipo VPG + año actual = Ver todas las VPG del año
- Útil para analítica y reportes

---

## 🚀 Próximas Mejoras Posibles (Futuras)

1. **Exportar a Excel** con filtros aplicados
2. **Dashboard** con métricas de VPG vs Facturas
3. **Gráficas** de ventas por tipo
4. **Acciones en lote** para VPG
5. **Plantillas** de VPG para clientes frecuentes

---

## 📌 Notas Importantes

- **Consecutivo VPG se reinicia cada año**: VPG25-X → VPG26-1
- **Formato fijo**: VPG{YY}-{N} (no modificable)
- **Folio se genera al guardar**: No se puede editar manualmente
- **Compatible con sistema existente**: No rompe nada
- **Ordenamiento por fecha**: Respeta cronología real

---

## ✅ Estado: COMPLETADO Y PROBADO

Todas las funcionalidades implementadas y probadas exitosamente. El sistema está listo para uso en producción.

**Fecha de implementación**: 09 de Enero de 2026
