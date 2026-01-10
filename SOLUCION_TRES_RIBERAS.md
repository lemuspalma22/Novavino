# SOLUCIÓN: Nombre Completo para TRES RIBERAS

## Problema
El producto se extrae como: `TRES RIBERAS "HA PASADO UN ÁNGEL"`
Pero se muestra para crear como: `TRES RIBERAS` (truncado)

## Impacto
- Próximas facturas con el nombre completo NO se reconocerán
- Aparecerá nuevamente como Producto No Reconocido
- Trabajo manual repetitivo

## Solución

### Opción 1: Crear producto con nombre completo (RECOMENDADO)
```
Nombre: TRES RIBERAS HA PASADO UN ANGEL
Precio: $117.80
Proveedor: Secretos de la Vid
```

**Nota:** Se recomienda quitar las comillas tipográficas `""` del nombre para evitar problemas de encoding.

### Opción 2: Crear alias DESPUÉS de crear el producto
1. Crea el producto: "TRES RIBERAS" (nombre corto)
2. Ve a: Admin → Alias productos → Agregar alias
3. Agrega alias: `TRES RIBERAS "HA PASADO UN ÁNGEL"` → Producto: TRES RIBERAS

De esta forma:
- El producto tiene un nombre corto y limpio
- El alias captura el nombre completo del PDF
- El sistema detectará automáticamente ambos nombres

### Opción 3: Modificar el nombre en el PNR antes de crear
1. Ve al PNR en Admin
2. Edita el campo "nombre_detectado"
3. Cambia a: `TRES RIBERAS HA PASADO UN ANGEL` (sin comillas)
4. Guarda
5. Ahora crea el producto con ese nombre

## Verificación

Después de crear el producto, prueba:

```python
from inventario.utils import encontrar_producto_unico

# Probar con nombre completo
producto, error = encontrar_producto_unico('TRES RIBERAS "HA PASADO UN ÁNGEL"')
print(f"Encontrado: {producto.nombre if producto else 'NO'}")

# Probar con nombre corto  
producto, error = encontrar_producto_unico('TRES RIBERAS')
print(f"Encontrado: {producto.nombre if producto else 'NO'}")
```

Ambos deberían encontrar el producto (por alias o por nombre).

## Recomendación Final

**Mejor práctica:**
1. Producto: `TRES RIBERAS HA PASADO UN ANGEL` (sin comillas)
2. Precio: $117.80 (incluye impuestos y descuento)
3. Proveedor: Secretos de la Vid

Esto asegura reconocimiento automático en futuras facturas.
