from datetime import datetime
import csv

from django.db.models import F, Sum
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import render
from django.utils.dateparse import parse_date
from django.views.decorators.http import require_http_methods
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from inventario.models import Producto
from .models import Factura
from utils.reportes import calcular_agregados_periodo_ventas, generar_dict_reporte_factura


# ----------------------------- utilidades -----------------------------

def _parse_date_html(value: str):
    if not value:
        return None
    try:
        # inputs type="date"
        return datetime.strptime(value, "%Y-%m-%d").date()
    except Exception:
        return None


def _rangos(request):
    # Soporta nombres usados en tu template actual
    fi = _parse_date_html(request.GET.get("fecha_inicio") or request.GET.get("start_date"))
    ff = _parse_date_html(request.GET.get("fecha_fin") or request.GET.get("end_date"))
    return fi, ff


def _totales(qs):
    # costo = sum(precio_compra * cantidad)
    costo_total = (
        qs.aggregate(
            s=Sum(F("detalles__precio_compra") * F("detalles__cantidad"))
        )["s"]
        or 0
    )
    total_venta = qs.aggregate(s=Sum("total"))["s"] or 0
    return total_venta, costo_total, (total_venta - costo_total)


# ----------------------------- API pequeña -----------------------------

def get_producto_precio(request, producto_id):
    try:
        p = Producto.objects.get(id=producto_id)
        return JsonResponse({"precio_unitario": str(p.precio_venta)})
    except Producto.DoesNotExist:
        return JsonResponse({"error": "Producto no encontrado"}, status=404)


def api_producto_precios(request, pk: int):
    try:
        p = Producto.objects.get(pk=pk)
    except Producto.DoesNotExist:
        raise Http404("Producto no encontrado")

    precio_venta = getattr(p, "precio_unitario", None) or getattr(p, "precio_venta", 0) or 0
    precio_compra = getattr(p, "precio_compra", 0) or 0
    return JsonResponse({"precio_venta": float(precio_venta), "precio_compra": float(precio_compra)})


# ----------------------------- Cortes -----------------------------

@require_http_methods(["GET"])
def corte_contable(request):
    """Corte por fecha de FACTURACIÓN."""
    fi, ff = _rangos(request)
    
    # Usar la nueva función abstraída
    agregados = calcular_agregados_periodo_ventas(
        Factura.objects.filter(fecha_facturacion__isnull=False),  # Query defensivo
        fi, ff,
        campo_fecha='fecha_facturacion',
        solo_pagadas=False
    )
    
    qs = agregados['queryset']
    
    # Armar reporte usando función abstraída
    reporte = []
    for f in qs:
        reporte.append(generar_dict_reporte_factura(f))

    # Calcular porcentaje de ganancia total
    porcentaje_ganancia_total = 0
    if agregados['total_venta'] > 0:
        porcentaje_ganancia_total = (agregados['ganancia_total'] / agregados['total_venta']) * 100
    
    return render(request, "ventas/corte.html", {
        "modo": "contable",
        "facturas": qs,
        "reporte": reporte,
        "fi": fi, "ff": ff,
        "totales": {
            "total_venta": agregados['total_venta'],
            "total_costo_proveedores": agregados['costo_total'],
            "total_transporte": agregados['transporte_total'],
            "total_ganancia": agregados['ganancia_total'],
            "porcentaje_ganancia": porcentaje_ganancia_total,
        },
    })


@require_http_methods(["GET"])
def corte_flujo(request):
    """Corte por fecha de PAGO (solo pagadas)."""
    fi, ff = _rangos(request)
    
    # Usar la nueva función abstraída
    agregados = calcular_agregados_periodo_ventas(
        Factura.objects.filter(fecha_pago__isnull=False),  # Query defensivo
        fi, ff,
        campo_fecha='fecha_pago',
        solo_pagadas=True
    )
    
    qs = agregados['queryset']
    
    # Armar reporte usando función abstraída
    reporte = []
    for f in qs:
        reporte_dict = generar_dict_reporte_factura(f)
        # Ajustar fecha para modo flujo (fecha_pago en lugar de fecha_facturacion)
        if f.fecha_pago:
            reporte_dict["fecha"] = f.fecha_pago.strftime("%d-%b-%Y")
        reporte.append(reporte_dict)

    # Calcular porcentaje de ganancia total
    porcentaje_ganancia_total = 0
    if agregados['total_venta'] > 0:
        porcentaje_ganancia_total = (agregados['ganancia_total'] / agregados['total_venta']) * 100
    
    return render(request, "ventas/corte.html", {
        "modo": "flujo",
        "facturas": qs,
        "reporte": reporte,
        "fi": fi, "ff": ff,
        "totales": {
            "total_venta": agregados['total_venta'],
            "total_costo_proveedores": agregados['costo_total'],
            "total_transporte": agregados['transporte_total'],
            "total_ganancia": agregados['ganancia_total'],
            "porcentaje_ganancia": porcentaje_ganancia_total,
        },
    })


# ----------------------------- Exportaciones -----------------------------

def _facturas_para_export(fecha_inicio, fecha_fin, modo: str):
    if modo == "flujo":
        qs = Factura.objects.filter(pagado=True)
        qs = qs.filter(fecha_pago__range=(fecha_inicio, fecha_fin))
    else:
        qs = Factura.objects.filter(fecha_facturacion__range=(fecha_inicio, fecha_fin))
    return qs.prefetch_related("detalles__producto")


def exportar_csv(request):
    modo = request.GET.get("modo", "contable")  # 'contable' | 'flujo'
    fi = _parse_date_html(request.GET.get("fecha_inicio"))
    ff = _parse_date_html(request.GET.get("fecha_fin"))
    if not (fi and ff):
        return HttpResponse("Rango de fechas inválido", status=400)

    qs = _facturas_para_export(fi, ff, modo)

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="corte_{modo}.csv"'
    w = csv.writer(response)
    w.writerow(["Folio", "Cliente", "Fecha", "Total Venta", "Costo Proveedores", "Transporte",
                "Ganancia", "Porcentaje Ganancia", "Productos Personalizados", "Productos No Personalizados"])

    for f in qs:
        costo = sum(d.cantidad * d.precio_compra for d in f.detalles.all())
        transporte = sum(
            d.cantidad * (getattr(d.producto, 'costo_transporte', 0) or 0)
            for d in f.detalles.all()
        )
        gan = (f.total or 0) - costo
        porcentaje_ganancia = 0
        if f.total and f.total > 0:
            porcentaje_ganancia = (gan / f.total) * 100
        pers = sum(d.cantidad for d in f.detalles.all() if getattr(d.producto, "es_personalizado", False))
        no_pers = sum(d.cantidad for d in f.detalles.all() if not getattr(d.producto, "es_personalizado", False))
        fecha = (f.fecha_pago if modo == "flujo" else f.fecha_facturacion).strftime("%d-%b-%Y")
        w.writerow([f.folio_factura, f.cliente, fecha, f.total, costo, transporte, gan, porcentaje_ganancia, pers, no_pers])

    return response


def exportar_pdf(request):
    modo = request.GET.get("modo", "contable")
    fi = _parse_date_html(request.GET.get("fecha_inicio"))
    ff = _parse_date_html(request.GET.get("fecha_fin"))
    if not (fi and ff):
        return HttpResponse("Rango de fechas inválido", status=400)

    qs = _facturas_para_export(fi, ff, modo)

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="corte_{modo}.pdf"'
    p = canvas.Canvas(response, pagesize=letter)
    titulo = "Corte por Fecha de Pago (Flujo)" if modo == "flujo" else "Corte por Fecha de Factura (Contable)"
    p.drawString(80, 750, titulo)

    y = 730
    for f in qs:
        costo = sum(d.cantidad * d.precio_compra for d in f.detalles.all())
        transporte = sum(
            d.cantidad * (getattr(d.producto, 'costo_transporte', 0) or 0)
            for d in f.detalles.all()
        )
        gan = (f.total or 0) - costo
        porcentaje_ganancia = 0
        if f.total and f.total > 0:
            porcentaje_ganancia = (gan / f.total) * 100
        fecha = (f.fecha_pago if modo == "flujo" else f.fecha_facturacion).strftime("%d-%b-%Y")

        p.drawString(80, y, f"Factura {f.folio_factura} - Cliente: {f.cliente}")
        p.drawString(80, y-15, f"Fecha: {fecha}  |  Total: {f.total}  |  Costo: {costo}  |  Transporte: {transporte}  |  Ganancia: {gan}  |  Porcentaje Ganancia: {porcentaje_ganancia}%")
        y -= 40
        if y < 80:
            p.showPage()
            y = 750

    p.showPage()
    p.save()
    return response

def corte_semanal_page(request):
    return render(request, "ventas/corte_semanal.html")

# --- API JSON que consume el template con fetch ---
from django.views.decorators.http import require_http_methods

@require_http_methods(["GET"])
def corte_semanal(request):
    """
    API JSON.
    modo=contable -> fecha_facturacion (todas)
    modo=flujo    -> fecha_pago (solo pagadas)
    """
    modo = (request.GET.get("modo") or "contable").strip().lower()
    if modo not in ("contable", "flujo"):
        modo = "contable"

    # Tu template manda start_date/end_date (o fecha_inicio/fecha_fin)
    fi, ff = _rangos(request)
    if not (fi and ff):
        return JsonResponse({"error": "Rango de fechas inválido"}, status=400)

    if modo == "flujo":
        qs = Factura.objects.filter(pagado=True, fecha_pago__range=(fi, ff))
    else:
        qs = Factura.objects.filter(fecha_facturacion__range=(fi, ff))

    qs = qs.prefetch_related("detalles__producto")

    reporte = []
    total_transporte_global = 0
    for f in qs:
        costo = sum((d.cantidad or 0) * (d.precio_compra or 0) for d in f.detalles.all())
        transporte = sum(
            (d.cantidad or 0) * (getattr(d.producto, 'costo_transporte', 0) or 0)
            for d in f.detalles.all()
        )
        total_transporte_global += transporte
        ganancia = (f.total or 0) - costo
        porcentaje_ganancia = 0
        if f.total and f.total > 0:
            porcentaje_ganancia = (ganancia / f.total) * 100
        pers, no_pers = {}, {}
        for d in f.detalles.all():
            nombre = d.producto.nombre
            bucket = pers if getattr(d.producto, "es_personalizado", False) else no_pers
            bucket[nombre] = bucket.get(nombre, 0) + (d.cantidad or 0)

        fecha_txt = (f.fecha_pago if modo == "flujo" else f.fecha_facturacion).strftime("%d-%b-%Y")

        reporte.append({
            "folio": f.folio_factura,
            "cliente": str(f.cliente),
            "fecha": fecha_txt,
            "total_venta": float(f.total or 0),
            "costo_proveedores": float(costo),
            "transporte": float(transporte),
            "ganancia": float(ganancia),
            "porcentaje_ganancia": float(porcentaje_ganancia),
            "productos_personalizados": pers or "Ninguno",
            "productos_no_personalizados": no_pers or "Ninguno",
        })

    tot_vta, tot_costo, tot_gan = _totales(qs)
    
    # Calcular porcentaje de ganancia total
    porcentaje_ganancia_total = 0
    if tot_vta > 0:
        porcentaje_ganancia_total = (tot_gan / tot_vta) * 100

    return JsonResponse({
        "modo": modo,
        "reporte": reporte,
        "totales": {
            "total_venta": float(tot_vta),
            "total_costo_proveedores": float(tot_costo),
            "total_transporte": float(total_transporte_global),
            "total_ganancia": float(tot_gan),
            "porcentaje_ganancia": float(porcentaje_ganancia_total),
            "productos_personalizados": "Ninguno",
            "productos_no_personalizados": "Ninguno",
        },
    })