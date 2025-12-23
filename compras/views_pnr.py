# compras/views_pnr.py
"""
Vistas para reconciliación de Productos No Reconocidos desde el detalle de Compra.
"""
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from decimal import Decimal
import logging

from .models import Compra, CompraProducto
from inventario.models import Producto, ProductoNoReconocido, AliasProducto

logger = logging.getLogger(__name__)

def asignar_pnr_view(request, object_id):
    """Asignar PNR a producto existente."""
    if request.method != "POST":
        return redirect('admin:compras_compra_change', object_id)
    
    compra = get_object_or_404(Compra, pk=object_id)
    pnr_id = request.POST.get("pnr_id")
    producto_id = request.POST.get("producto_id")
    crear_alias = request.POST.get("crear_alias") == "on"
    
    if not pnr_id or not producto_id:
        messages.error(request, "Faltan datos: PNR o Producto.")
        return redirect('admin:compras_compra_change', object_id)
    
    pnr = get_object_or_404(ProductoNoReconocido, pk=pnr_id)
    producto = get_object_or_404(Producto, pk=producto_id)
    
    print(f"\n{'='*60}")
    print(f"ASIGNAR PNR: {pnr.nombre_detectado} → {producto.nombre}")
    print(f"PNR ID: {pnr_id}, Producto ID: {producto_id}, Crear alias: {crear_alias}")
    print(f"{'='*60}\n")
    
    try:
        with transaction.atomic():
            print("→ Iniciando transacción atómica...")
            # Usar get_or_create para evitar duplicar CompraProducto
            print("→ Creando/obteniendo CompraProducto...")
            compra_producto, created = CompraProducto.objects.get_or_create(
                compra=compra,
                producto=producto,
                defaults={
                    "cantidad": int(pnr.cantidad or 0),
                    "precio_unitario": Decimal(str(pnr.precio_unitario or 0)),
                    "detectado_como": pnr.nombre_detectado,
                }
            )
            print(f"→ CompraProducto {'creado' if created else 'ya existía'} (ID: {compra_producto.id})")
            
            # Actualizar stock
            cantidad_pnr = int(pnr.cantidad or 0)
            if created:
                # Nuevo CompraProducto: sumar stock
                stock_anterior = producto.stock or 0
                producto.stock = stock_anterior + cantidad_pnr
                producto.save(update_fields=["stock"])
                print(f"→ Stock actualizado: {stock_anterior} + {cantidad_pnr} = {producto.stock}")
            else:
                # CompraProducto ya existía: SUMAR cantidades
                cantidad_anterior = compra_producto.cantidad
                compra_producto.cantidad += cantidad_pnr
                compra_producto.save(update_fields=["cantidad"])
                
                stock_anterior = producto.stock or 0
                producto.stock = stock_anterior + cantidad_pnr
                producto.save(update_fields=["stock"])
                print(f"→ CompraProducto actualizado: cantidad {cantidad_anterior} + {cantidad_pnr} = {compra_producto.cantidad}")
                print(f"→ Stock actualizado: {stock_anterior} + {cantidad_pnr} = {producto.stock}")
        
        print("✓ Transacción atómica completada exitosamente\n")
        
        # Marcar PNR como procesado FUERA de la transacción para evitar rollback
        # IMPORTANTE: Marcamos movimiento_generado=True para que el signal NO procese
        # Ya sumamos stock y creamos CompraProducto arriba
        pnr.procesado = True
        pnr.producto = producto
        pnr.movimiento_generado = True  # Evita que el signal duplique
        pnr.save(update_fields=["procesado", "producto", "movimiento_generado"])
        print(f"✓ PNR {pnr_id} marcado como procesado (fuera de transacción)")
        
        # Verificar que el PNR realmente se marcó como procesado
        pnr.refresh_from_db()
        print(f"DEBUG: Verificando PNR después de save - procesado={pnr.procesado}, producto_id={pnr.producto_id}")
        
        # Crear alias FUERA de la transacción para que no revierta todo si falla
        if crear_alias and pnr.nombre_detectado:
            print(f"\n→ Intentando crear alias: '{pnr.nombre_detectado}' → {producto.nombre}")
            try:
                alias_obj, alias_created = AliasProducto.objects.get_or_create(
                    alias=pnr.nombre_detectado,
                    defaults={"producto": producto}
                )
                print(f"✓ Alias {'creado' if alias_created else 'ya existía'}")
                messages.success(request, f"✓ '{pnr.nombre_detectado}' asignado a '{producto.nombre}' y alias creado.")
            except Exception as e:
                print(f"✗ ERROR creando alias: {type(e).__name__}: {str(e)}")
                logger.error(f"Error creando alias para PNR {pnr_id}: {type(e).__name__}: {str(e)}", exc_info=True)
                messages.warning(request, f"✓ '{pnr.nombre_detectado}' asignado pero NO se pudo crear alias: {str(e)}")
        else:
            print("→ No se solicitó crear alias")
            messages.success(request, f"✓ '{pnr.nombre_detectado}' asignado a '{producto.nombre}'.")
    except Exception as e:
        print(f"\n✗ ERROR EN TRANSACCIÓN: {type(e).__name__}: {str(e)}\n")
        logger.error(f"Error asignando PNR {pnr_id}: {str(e)}", exc_info=True)
        messages.error(request, f"Error al asignar PNR: {str(e)}")
    
    return redirect('admin:compras_compra_change', object_id)


def crear_producto_pnr_view(request, object_id):
    """Crear nuevo producto desde PNR."""
    if request.method != "POST":
        return redirect('admin:compras_compra_change', object_id)
    
    compra = get_object_or_404(Compra, pk=object_id)
    pnr_id = request.POST.get("pnr_id")
    nombre = request.POST.get("nombre", "").strip()
    tipo = request.POST.get("tipo", "").strip() or None
    precio_compra = request.POST.get("precio_compra")
    costo_transporte = request.POST.get("costo_transporte", "0")
    precio_venta = request.POST.get("precio_venta")
    
    if not all([pnr_id, nombre, precio_compra, precio_venta]):
        messages.error(request, "Faltan datos para crear el producto.")
        return redirect('admin:compras_compra_change', object_id)
    
    pnr = get_object_or_404(ProductoNoReconocido, pk=pnr_id)
    
    try:
        producto = None
        with transaction.atomic():
            # Usar costo de transporte del proveedor si no se especificó uno
            costo_transporte_final = Decimal(costo_transporte) if costo_transporte and costo_transporte != "0" else compra.proveedor.costo_transporte_unitario
            
            producto = Producto.objects.create(
                nombre=nombre,
                tipo=tipo,
                proveedor=compra.proveedor,
                precio_compra=Decimal(precio_compra),
                costo_transporte=costo_transporte_final,
                precio_venta=Decimal(precio_venta),
                stock=int(pnr.cantidad or 0),
            )
            
            CompraProducto.objects.create(
                compra=compra,
                producto=producto,
                cantidad=int(pnr.cantidad or 0),
                precio_unitario=Decimal(precio_compra),  # Usar el precio del formulario, no del PNR
                detectado_como=pnr.nombre_detectado,
            )
        
        # Marcar PNR y crear alias FUERA de la transacción
        # Primero marcamos el PNR como procesado
        pnr.procesado = True
        pnr.producto = producto
        pnr.movimiento_generado = True  # Evita que el signal duplique
        pnr.save(update_fields=["procesado", "producto", "movimiento_generado"])
        
        # Luego intentamos crear el alias SOLO si el nombre detectado es diferente al nombre del producto
        if pnr.nombre_detectado and producto:
            # Evitar crear alias con el mismo nombre que el producto (redundante)
            if pnr.nombre_detectado.strip().lower() != producto.nombre.strip().lower():
                try:
                    AliasProducto.objects.get_or_create(
                        alias=pnr.nombre_detectado,
                        defaults={"producto": producto}
                    )
                    messages.success(request, f"✓ Producto '{producto.nombre}' creado, asignado y alias creado.")
                except Exception as e:
                    logger.error(f"Error creando alias para nuevo producto: {str(e)}", exc_info=True)
                    messages.warning(request, f"✓ Producto '{producto.nombre}' creado pero NO se pudo crear alias: {str(e)}")
            else:
                # El nombre detectado es igual al producto, no crear alias
                messages.success(request, f"✓ Producto '{producto.nombre}' creado y asignado.")
        else:
            if producto:
                messages.success(request, f"✓ Producto '{producto.nombre}' creado y asignado.")
    except Exception as e:
        logger.error(f"Error creando producto desde PNR {pnr_id}: {str(e)}", exc_info=True)
        messages.error(request, f"Error al crear producto: {str(e)}")
    
    return redirect('admin:compras_compra_change', object_id)