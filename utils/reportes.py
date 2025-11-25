# utils/reportes.py
"""
Módulo común para lógica de reportes y cortes.
Abstrae la duplicación entre compras y ventas.
"""
from decimal import Decimal
from typing import Dict, List, Any, Tuple, Optional
from django.db.models import QuerySet, Sum, F
from django.db.models.functions import Coalesce


def calcular_agregados_periodo_compras(queryset: QuerySet, fecha_inicio=None, fecha_fin=None) -> Dict[str, Any]:
    """
    Calcula agregados para compras en un período.
    
    Args:
        queryset: QuerySet de CompraProducto
        fecha_inicio: Fecha inicio del período (opcional)
        fecha_fin: Fecha fin del período (opcional)
    
    Returns:
        Dict con totales, productos personalizados/no personalizados
    """
    # Aplicar filtros de fecha si se proporcionan
    if fecha_inicio and fecha_fin:
        queryset = queryset.filter(compra__fecha__range=(fecha_inicio, fecha_fin))
    
    # Optimizar con select_related
    queryset = queryset.select_related('producto', 'compra')
    
    total_gastado = Decimal('0')
    productos_personalizados = 0
    productos_no_personalizados = 0
    
    for producto_compra in queryset:
        subtotal = producto_compra.subtotal()
        total_gastado += Decimal(str(subtotal))
        
        if producto_compra.producto.es_personalizado:
            productos_personalizados += producto_compra.cantidad
        else:
            productos_no_personalizados += producto_compra.cantidad
    
    return {
        'total_gastado': float(total_gastado),
        'productos_personalizados': productos_personalizados,
        'productos_no_personalizados': productos_no_personalizados,
        'queryset': queryset
    }


def calcular_agregados_periodo_ventas(queryset: QuerySet, fecha_inicio=None, fecha_fin=None, 
                                     campo_fecha='fecha_facturacion', solo_pagadas=False) -> Dict[str, Any]:
    """
    Calcula agregados para ventas en un período.
    
    Args:
        queryset: QuerySet de Factura
        fecha_inicio: Fecha inicio del período (opcional)
        fecha_fin: Fecha fin del período (opcional)
        campo_fecha: Campo de fecha a usar ('fecha_facturacion' o 'fecha_pago')
        solo_pagadas: Si True, filtrar solo facturas pagadas
    
    Returns:
        Dict con totales, productos personalizados/no personalizados
    """
    # Aplicar filtros
    if solo_pagadas:
        queryset = queryset.filter(pagado=True)
    
    if fecha_inicio and fecha_fin:
        filtro_fecha = f"{campo_fecha}__range"
        queryset = queryset.filter(**{filtro_fecha: (fecha_inicio, fecha_fin)})
    
    # Calcular totales usando agregación simple (sin JOINs para evitar duplicación)
    agregados = queryset.aggregate(
        total_venta=Sum('total')
    )
    
    # Calcular costo total manualmente para evitar JOINs problemáticos
    costo_total = Decimal('0')
    for factura in queryset:
        for detalle in factura.detalles.all():
            costo_total += (detalle.precio_compra or 0) * (detalle.cantidad or 0)
    
    # Optimizar con prefetch_related DESPUÉS de la agregación
    queryset = queryset.prefetch_related("detalles__producto")
    
    total_venta = agregados['total_venta'] or Decimal('0')
    ganancia_total = total_venta - costo_total
    
    # Calcular productos personalizados/no personalizados
    # Usar una sola query para evitar N+1
    facturas_list = list(queryset)
    productos_personalizados = 0
    productos_no_personalizados = 0
    
    for factura in facturas_list:
        for detalle in factura.detalles.all():
            cantidad = detalle.cantidad or 0
            if getattr(detalle.producto, 'es_personalizado', False):
                productos_personalizados += cantidad
            else:
                productos_no_personalizados += cantidad
    
    return {
        'total_venta': float(total_venta),
        'costo_total': float(costo_total),
        'ganancia_total': float(ganancia_total),
        'productos_personalizados': productos_personalizados,
        'productos_no_personalizados': productos_no_personalizados,
        'queryset': queryset
    }


def generar_dict_reporte_factura(factura) -> Dict[str, Any]:
    """
    Genera diccionario estandarizado para reporte de factura.
    
    Args:
        factura: Instancia de Factura
    
    Returns:
        Dict con datos de la factura para reporte
    """
    # Calcular costo y ganancia
    costo = sum((d.cantidad or 0) * (d.precio_compra or 0) for d in factura.detalles.all())
    ganancia = (factura.total or 0) - costo
    
    # Agrupar productos por personalizado/no personalizado
    pers, no_pers = {}, {}
    for d in factura.detalles.all():
        key = d.producto.nombre
        bucket = pers if getattr(d.producto, "es_personalizado", False) else no_pers
        bucket[key] = bucket.get(key, 0) + (d.cantidad or 0)
    
    return {
        "folio": factura.folio_factura,
        "cliente": str(factura.cliente),
        "fecha": factura.fecha_facturacion.strftime("%d-%b-%Y"),
        "total_venta": factura.total or 0,
        "costo_proveedores": costo,
        "ganancia": ganancia,
        "productos_personalizados": pers or "Ninguno",
        "productos_no_personalizados": no_pers or "Ninguno",
    }


def generar_dict_reporte_compra(compra_producto) -> Dict[str, Any]:
    """
    Genera diccionario estandarizado para reporte de compra.
    
    Args:
        compra_producto: Instancia de CompraProducto
    
    Returns:
        Dict con datos de la compra para reporte
    """
    return {
        "folio": compra_producto.compra.folio,
        "fecha": compra_producto.compra.fecha.strftime("%d-%b-%Y"),
        "proveedor": compra_producto.compra.proveedor.nombre if compra_producto.compra.proveedor else "Sin proveedor",
        "producto": compra_producto.producto.nombre,
        "cantidad": compra_producto.cantidad,
        "precio_unitario": compra_producto.precio_unitario,
        "subtotal": compra_producto.subtotal(),
        "personalizado": "Sí" if compra_producto.producto.es_personalizado else "No"
    }
