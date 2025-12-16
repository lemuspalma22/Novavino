# 📥 Procesamiento de Facturas de Ventas desde Google Drive

Esta funcionalidad te permite procesar facturas de ventas PDF directamente desde el Django Admin, sin necesidad de usar la terminal.

---

## 🚀 Cómo Usar

### Desde Admin de Ventas

1. **Ve al Admin de Django** → `Ventas` → `Facturas`
2. **Haz clic en el botón** (arriba a la derecha):
   ```
   📥 Procesar Facturas desde Drive
   ```
3. **Espera** mientras se procesan las facturas (puede tardar 1-3 minutos)
4. **Verás mensajes** en la parte superior indicando:
   - ✅ Facturas registradas exitosamente
   - ❌ Facturas con errores

---

## 📊 Qué Hace Exactamente

1. **Conecta** con Google Drive usando credenciales almacenadas
2. **Lee** PDFs de la carpeta `Facturas Ventas por Procesar (Nuevas)`
3. **Extrae** datos (folio, cliente, productos, totales, etc.) usando el extractor de Novavino
4. **Registra** en la base de datos (con reemplazo si ya existe)
5. **Mueve** archivos según resultado:
   - ✅ Éxito → Carpeta `Facturas Ventas Procesadas`
   - ❌ Error → Carpeta `Facturas Ventas Errores`

---

## 📁 Estructura de Carpetas en Drive

```
Facturas_Ventas/
  ├─ Facturas Ventas por Procesar (Nuevas)/  ← Deposita PDFs aquí
  ├─ Facturas Ventas Procesadas/              ← PDFs procesados exitosamente
  └─ Facturas Ventas Errores/                 ← PDFs con errores
```

### IDs de Carpetas:
- **Carpeta Padre**: `1I6yGfo7qpq7Eb4T9KpqWnL4qKihbpwiZ`
- **Nuevas**: `1jhsWqGxrVPeokIUCzFjS_Q-0kDE4jI9r`
- **Procesadas**: `19sDwsEL5xE4k-RQPQ18B-LEMwEv6tP1v`
- **Errores**: `1f91IEc8lCW9nZA32qHW1c2L9FpAzWnqA`

---

## ⚙️ Configuración

### Variables de Entorno (.env)

Asegúrate de tener estas variables en tu archivo `.env`:

```env
# Carpetas de Google Drive para Ventas
VENTAS_ROOT_ID=1I6yGfo7qpq7Eb4T9KpqWnL4qKihbpwiZ
VENTAS_NUEVAS_ID=1jhsWqGxrVPeokIUCzFjS_Q-0kDE4jI9r
VENTAS_PROCESADAS_ID=19sDwsEL5xE4k-RQPQ18B-LEMwEv6tP1v
VENTAS_ERRORES_ID=1f91IEc8lCW9nZA32qHW1c2L9FpAzWnqA
```

---

## 🔍 Validaciones Automáticas

El sistema automáticamente:

1. **Extrae datos** del PDF usando el extractor de Novavino
2. **Valida folio** (obligatorio)
3. **Calcula costos** con transporte incluido:
   - `precio_compra + costo_transporte = costo_total`
4. **Deduplica** por folio (reemplaza si ya existe)
5. **Calcula totales** automáticamente

---

## ✅ Facturas Procesadas Correctamente

Una factura se procesa correctamente si:
- ✅ Se extrajo el folio
- ✅ Se extrajo el cliente
- ✅ Se extrajeron los productos y cantidades
- ✅ Se registraron todos los detalles en BD
- ✅ Se calculó el total correctamente

El PDF se mueve a `Facturas Ventas Procesadas/`

---

## ❌ Facturas con Errores

Una factura va a errores si:
- ❌ No se pudo leer el PDF
- ❌ No se encontró el folio
- ❌ Error al extraer datos
- ❌ Error al guardar en BD

El PDF se mueve a `Facturas Ventas Errores/` y puedes revisar el error en el admin.

---

## 🔧 Solución de Problemas

### Error: "No se encontraron facturas pendientes"
- **Causa**: La carpeta `Nuevas` está vacía
- **Solución**: Deposita PDFs en la carpeta correcta

### Error: "No se pudo importar el módulo drive_processor"
- **Causa**: Falta el módulo `ventas/utils/drive_processor.py`
- **Solución**: Verifica que el archivo existe

### Error: "Faltan variables de entorno"
- **Causa**: No están configuradas las variables en `.env`
- **Solución**: Agrega las variables según la sección de Configuración

### Error: "No se encontró el folio"
- **Causa**: El PDF no tiene un formato reconocible
- **Solución**: Verifica que sea una factura de Novavino válida

---

## 💡 Consejos

1. **Procesa en lotes pequeños** (20-30 facturas máximo)
2. **Revisa los errores** en la carpeta de Errores
3. **Verifica duplicados** antes de procesar
4. **Haz backup** antes de procesar muchas facturas

---

## 📝 Notas Importantes

- **Reemplazo automático**: Si una factura con el mismo folio ya existe, se reemplaza
- **Cálculo de costos**: El sistema suma automáticamente `precio_compra + costo_transporte`
- **Movimiento de archivos**: Los PDFs se mueven automáticamente, no se copian
- **Logs detallados**: Los logs aparecen en la consola del servidor Django

---

## 🆚 Diferencia con Compras

| Feature | Compras | Ventas |
|---------|---------|--------|
| **Extractor** | Múltiples proveedores | Solo Novavino |
| **Duplicados** | Se omiten | Se reemplazan |
| **Validación** | Lenient/Strict | Automática |
| **Carpeta Drive** | `Compras_Nuevas` | `Facturas Ventas por Procesar (Nuevas)` |

---

## 🔄 Flujo Completo

1. **Depositas** PDFs en `Facturas Ventas por Procesar (Nuevas)`
2. **Haces clic** en "Procesar Facturas desde Drive" en el admin
3. **El sistema**:
   - Lee los PDFs
   - Extrae datos
   - Registra en BD
   - Mueve archivos
4. **Verificas** el resultado en los mensajes del admin
5. **Revisas** facturas con errores si es necesario

---

## 📞 Soporte

Si encuentras problemas:
1. Revisa los logs en la consola del servidor
2. Verifica las variables de entorno
3. Confirma que las carpetas en Drive existen y tienen los IDs correctos
