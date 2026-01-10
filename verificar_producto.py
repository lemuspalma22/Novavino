from inventario.utils import encontrar_producto_unico

nombre = "bot anecdota espumoso personalizado epico"

print(f"Buscando: '{nombre}'")
producto, error = encontrar_producto_unico(nombre)

if error == "not_found":
    print("  [X] NO EXISTE en la base de datos")
    print("  -> Deberia crear un PNR")
elif error == "ambiguous":
    print("  [!] AMBIGUO (multiples coincidencias)")
    print("  -> Deberia crear un PNR")
elif error:
    print(f"  [!] Error: {error}")
else:
    print(f"  [OK] EXISTE: {producto.nombre}")
    print(f"      ID: {producto.id}")
    print(f"      Stock: {producto.stock}")
