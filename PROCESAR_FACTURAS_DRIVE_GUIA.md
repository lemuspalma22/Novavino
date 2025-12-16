# 📥 Guía: Procesar Facturas desde Google Drive

## 🎯 Descripción

Esta funcionalidad te permite procesar facturas PDF directamente desde el Django Admin, sin necesidad de usar la terminal.

---

## 🚀 Cómo Usar

### Opción 1: Desde Lista de Compras (Recomendado)

1. **Ve al Admin de Django** → `Compras` → `Compras`
2. **NO selecciones ninguna compra** (o selecciona cualquiera, será ignorada)
3. **En el menú desplegable "Acción"**, selecciona:
   ```
   📥 Procesar facturas desde Google Drive
   ```
4. **Haz clic en "Ir"**
5. **Espera** mientras se procesan las facturas (puede tardar 1-3 minutos)
6. **Verás mensajes** en la parte superior indicando:
   - ✓ Facturas registradas exitosamente
   - ℹ Facturas duplicadas (omitidas)
   - ✗ Facturas con errores

---

## 📊 Qué Hace Exactamente

1. **Conecta** con Google Drive usando credenciales almacenadas
2. **Lee** PDFs de la carpeta `Compras_Nuevas`
3. **Extrae** datos (folio, proveedor, productos, totales, etc.)
4. **Valida** la información extraída
5. **Registra** en la base de datos
6. **Mueve** archivos según resultado:
   - ✓ Éxito → Carpeta `Compras_Procesadas`
   - ℹ Duplicada → Carpeta `Compras_Procesadas`
   - ✗ Error → Carpeta `Compras_Errores`

---

## 📁 Estructura de Carpetas en Drive

```
Facturas Proveedores/
├── Compras_Nuevas/          ← Coloca aquí los PDFs nuevos
├── Compras_Procesadas/      ← Facturas exitosas
└── Compras_Errores/         ← Facturas con problemas
    ├── factura.pdf          (archivo original)
    ├── factura.pdf.error.txt  (descripción del error)
    └── factura.pdf.data.json  (datos extraídos)
```

---

## ⚠️ Consideraciones Importantes

### 1. **Timeout en el Navegador**

Si tienes **más de 30 facturas** pendientes, el navegador puede mostrar timeout (503/504).

**Solución:**
- Procesa en lotes de 20-30 facturas
- Si aparece timeout, **espera 2-3 minutos** y recarga la página
- Las facturas SÍ se están procesando aunque no veas feedback

### 2. **Facturas Duplicadas**

El sistema detecta duplicados por:
- UUID de factura (SAT)
- Folio + Proveedor + Fecha

**Las duplicadas se omiten** automáticamente (no se registran dos veces).

### 3. **Errores Comunes**

| Error | Causa | Solución |
|-------|-------|----------|
| `No se encontró 'folio'` | PDF mal formado | Verificar PDF manualmente |
| `Proveedor no reconocido` | Nombre de proveedor nuevo | Agregar alias en admin |
| `Producto no reconocido` | Producto nuevo | Se crea PNR para revisión |
| `ImportError: pydrive2` | Dependencia faltante | `pip install pydrive2` |

### 4. **Autenticación Google Drive**

Si es la **primera vez** que usas esta función:

1. El sistema abrirá una ventana de navegador
2. **Inicia sesión** con la cuenta de Google Drive
3. **Autoriza** el acceso a Drive
4. Las credenciales se guardan en `token.json`

**Renovación automática:** El token se renueva solo, no necesitas volver a autenticar.

---

## 🔧 Configuración Avanzada

### Variables de Entorno (`.env`)

```bash
# IDs de carpetas de Google Drive
COMPRAS_ROOT_ID=1o9SkoeJ66qoBEbmyzXXhs1I67PQStTWV
COMPRAS_NUEVAS_ID=1yQ4Jq2nQuJsKxxdoIJ2VLAjszSx19d4U
COMPRAS_PROCESADAS_ID=1k_1LT-J4foKRw2-pAYuAWBntmab6Yix7
COMPRAS_ERRORES_ID=1YSo5L2VCoswN-vYr1kOCiTVctGp70ZV2

# Modo de validación: "strict", "lenient" o "off"
VALIDATION_MODE=lenient
```

### Modo de Validación

- **`lenient`** (recomendado): Validación flexible, permite pequeñas discrepancias
- **`strict`**: Validación estricta, rechaza cualquier inconsistencia
- **`off`**: Sin validación, registra todo (NO recomendado)

---

## 🐛 Debugging

### Ver Logs Detallados

Si hay errores, revisa:

1. **Consola del servidor Django** (terminal donde corre `runserver`)
2. **Carpeta `Compras_Errores`** en Drive:
   - `.error.txt` → Descripción del error
   - `.data.json` → Datos extraídos del PDF

### Probar Manualmente

También puedes ejecutar el script desde terminal (como antes):

```bash
python process_drive_invoices.py
```

Esto da output más detallado para debugging.

---

## 📈 Optimizaciones Futuras

Si en el futuro necesitas procesar > 50 facturas diarias:

1. **Migrar a Celery** (procesamiento asíncrono)
2. **Agregar barra de progreso** en tiempo real
3. **Programar ejecución automática** (cron/schedule)

Por ahora, con < 20 facturas 2x/semana, la solución actual es **perfecta**.

---

## ✅ Checklist de Uso

- [ ] Subir PDFs a carpeta `Compras_Nuevas` en Drive
- [ ] Ir a Admin → Compras
- [ ] Seleccionar acción "📥 Procesar facturas desde Google Drive"
- [ ] Hacer clic en "Ir"
- [ ] Esperar feedback (1-3 minutos)
- [ ] Revisar mensajes de éxito/error
- [ ] Si hay PNRs, resolverlos en el widget de cada compra

---

## 🆘 Soporte

Si encuentras problemas:

1. **Revisa logs** en consola del servidor
2. **Verifica carpeta Errores** en Drive
3. **Comprueba credenciales** de Google Drive (`token.json`)
4. **Valida PDFs** manualmente si persiste el error

---

**¡Listo para procesar facturas desde el admin!** 🎉
