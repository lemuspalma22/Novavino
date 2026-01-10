# 🔍 Instrucciones para Debuggear el Admin Action

## Problema Reportado

Al ejecutar la acción "📥 Procesar facturas desde Google Drive" aparece:
```
⚠️ Deben existir ítems seleccionados para poder realizar acciones sobre los mismos.
```

---

## ✅ Verificación Paso a Paso

### 1. Verificar que el Servidor Django Esté Corriendo

En la terminal donde corre `python manage.py runserver`, verifica si aparecen logs cuando ejecutas la acción.

**Deberías ver algo como:**
```
[13/Dec/2025 14:00:00] "POST /admin/compras/compra/ HTTP/1.1" 302 0
```

**Si NO ves logs:** La acción no se está ejecutando.

---

### 2. Verificar en la Consola del Servidor

Cuando ejecutes la acción desde el admin, **observa la consola** del servidor.

**Si se ejecuta correctamente, verás:**
- Mensajes de inicio
- Conexión con Drive
- Listado de archivos
- Procesamiento de cada factura

**Si NO se ejecuta:**
- No aparece nada en la consola
- Solo el log HTTP

---

### 3. Ejecutar Desde Terminal (Workaround Temporal)

Si el botón del admin no funciona, puedes usar el script:

```bash
python procesar_factura_2470_test.py
```

Esto procesa las facturas **sin usar el admin**.

---

### 4. Verificar Permisos

¿Tu usuario tiene permisos de staff?

1. Ve a: Admin → Usuarios → Tu usuario
2. Verifica que esté marcado:
   - ✅ **Activo**
   - ✅ **Es staff**
   - ✅ **Es superusuario** (opcional pero recomendado)

---

### 5. Verificar Configuración del Action

El action está configurado para **NO requerir selección** de items.

**Archivo:** `compras/admin.py`
**Línea:** ~516-613

La función `procesar_facturas_drive` debería ejecutarse **aunque no haya items seleccionados**.

---

## 🔧 Solución Temporal

Mientras investigamos el problema del admin, usa este workaround:

### Opción A: Script de Terminal

```bash
python process_drive_invoices.py
```

O el nuevo:

```bash
python procesar_factura_2470_test.py
```

### Opción B: Shell de Django

```bash
python manage.py shell
```

Luego ejecuta:

```python
from compras.utils.drive_processor import process_drive_invoices

resultado = process_drive_invoices()
print(f"Procesadas: {resultado['success']}")
print(f"Errores: {resultado['error']}")
```

---

## 📊 Información Necesaria

Para resolver el problema del admin, necesito saber:

1. **¿Aparecen logs** en la consola del servidor cuando ejecutas la acción?
2. **¿Ves algún mensaje** en la parte superior del admin (aunque sea error)?
3. **¿Tienes permisos** de staff/superusuario?
4. **¿Qué versión de Django** usas? (corre: `python manage.py version`)

---

## ✅ Resumen

**Problema 1 (Resuelto):** Factura 2070 no está en Drive
- **Solución:** Verificar ubicación y subir a `Compras_Nuevas`

**Problema 2 (En investigación):** Admin action no ejecuta
- **Workaround:** Usar script de terminal
- **Fix permanente:** Necesitamos más info de logs

---

**Próximos pasos:**
1. Verifica dónde está la factura 2070 en Drive
2. Súbela a `Compras_Nuevas`
3. Mientras tanto, ejecuta: `python procesar_factura_2470_test.py`
