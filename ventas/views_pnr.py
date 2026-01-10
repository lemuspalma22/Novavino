# ventas/views_pnr.py
"""
Vistas para reconciliación de Productos No Reconocidos desde el detalle de Factura (Ventas).
A diferencia de compras, aquí SOLO permitimos asignar a producto existente (con alias opcional).
NO permitimos crear productos nuevos porque en ventas el producto debe existir previamente.
"""
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from decimal import Decimal
import logging

from .models import Factura, DetalleFactura
from inventario.models import Producto, ProductoNoReconocido, AliasProducto

logger = logging.getLogger(__name__)

def asignar_pnr_venta_view(request, object_id):
    """Asignar PNR a producto existente en una venta."""
    if request.method != "POST":
        return redirect('admin:ventas_factura_change', object_id)
    
    factura = get_object_or_404(Factura, pk=object_id)
    pnr_id = request.POST.get("pnr_id")
    producto_id = request.POST.get("producto_id")
    crear_alias = request.POST.get("crear_alias") == "on"
    
    if not pnr_id or not producto_id:
        messages.error(request, "Faltan datos: PNR o Producto.")
        return redirect('admin:ventas_factura_change', object_id)
    
    pnr = get_object_or_404(ProductoNoReconocido, pk=pnr_id)
    producto = get_object_or_404(Producto, pk=producto_id)
    
    print(f"\n{'='*60}")
    print(f"ASIGNAR PNR (VENTA): {pnr.nombre_detectado} → {producto.nombre}")
    print(f"PNR ID: {pnr_id}, Producto ID: {producto_id}, Crear alias: {crear_alias}")
    print(f"{'='*60}\n")
    
    try:
        with transaction.atomic():
            print("→ Iniciando transacción atómica...")
            # Usar get_or_create para evitar duplicar DetalleFactura
            print("→ Creando/obteniendo DetalleFactura...")
            detalle_factura, created = DetalleFactura.objects.get_or_create(
                factura=factura,
                producto=producto,
                defaults={
                    "cantidad": int(pnr.cantidad or 0),
                    "precio_unitario": Decimal(str(pnr.precio_unitario or 0)) if pnr.precio_unitario else producto.precio_venta,
                }
            )
            print(f"→ DetalleFactura {'creado' if created else 'ya existía'} (ID: {detalle_factura.id})")
            
            # Actualizar stock (descontar en venta)
            cantidad_pnr = int(pnr.cantidad or 0)
            if created:
                # Nuevo DetalleFactura: descontar stock
                stock_anterior = producto.stock or 0
                producto.stock = stock_anterior - cantidad_pnr
                producto.save(update_fields=["stock"])
                print(f"→ Stock actualizado: {stock_anterior} - {cantidad_pnr} = {producto.stock}")
            else:
                # DetalleFactura ya existía: SUMAR cantidades y descontar del stock
                cantidad_anterior = detalle_factura.cantidad
                detalle_factura.cantidad += cantidad_pnr
                detalle_factura.save(update_fields=["cantidad"])
                
                stock_anterior = producto.stock or 0
                producto.stock = stock_anterior - cantidad_pnr
                producto.save(update_fields=["stock"])
                print(f"→ DetalleFactura actualizado: cantidad {cantidad_anterior} + {cantidad_pnr} = {detalle_factura.cantidad}")
                print(f"→ Stock actualizado: {stock_anterior} - {cantidad_pnr} = {producto.stock}")
        
        print("✓ Transacción atómica completada exitosamente\n")
        
        # Marcar PNR como procesado FUERA de la transacción para evitar rollback
        pnr.procesado = True
        pnr.producto = producto
        pnr.save(update_fields=["procesado", "producto"])
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
    
    return redirect('admin:ventas_factura_change', object_id)
