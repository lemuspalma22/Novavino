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
    qs = Factura.objects.all()
    if fi and ff:
        qs = qs.filter(fecha_facturacion__range=(fi, ff))
    qs = qs.prefetch_related("detalles__producto")

    # Armar reporte (estructura compatible con tu template actual)
    reporte = []
    for f in qs:
        costo = sum((d.cantidad or 0) * (d.precio_compra or 0) for d in f.detalles.all())
        ganancia = (f.total or 0) - costo
        pers, no_pers = {}, {}
        for d in f.detalles.all():
            key = d.producto.nombre
            bucket = pers if getattr(d.producto, "es_personalizado", False) else no_pers
            bucket[key] = bucket.get(key, 0) + (d.cantidad or 0)

        reporte.append({
            "folio": f.folio_factura,
            "cliente": str(f.cliente),
            "fecha": f.fecha_facturacion.strftime("%d-%b-%Y"),
            "total_venta": f.total or 0,
            "costo_proveedores": costo,
            "ganancia": ganancia,
            "productos_personalizados": pers or "Ninguno",
            "productos_no_personalizados": no_pers or "Ninguno",
        })

    tot_vta, tot_costo, tot_gan = _totales(qs)
    return render(request, "ventas/corte.html", {
        "modo": "contable",
        "facturas": qs,
        "reporte": reporte,
        "fi": fi, "ff": ff,
        "totales": {
            "total_venta": tot_vta,
            "total_costo_proveedores": tot_costo,
            "total_ganancia": tot_gan,
        },
    })


@require_http_methods(["GET"])
def corte_flujo(request):
    """Corte por fecha de PAGO (solo pagadas)."""
    fi, ff = _rangos(request)
    qs = Factura.objects.filter(pagado=True)
    if fi and ff:
        qs = qs.filter(fecha_pago__range=(fi, ff))
    qs = qs.prefetch_related("detalles__producto")

    reporte = []
    for f in qs:
        costo = sum((d.cantidad or 0) * (d.precio_compra or 0) for d in f.detalles.all())
        ganancia = (f.total or 0) - costo
        pers, no_pers = {}, {}
        for d in f.detalles.all():
            key = d.producto.nombre
            bucket = pers if getattr(d.producto, "es_personalizado", False) else no_pers
            bucket[key] = bucket.get(key, 0) + (d.cantidad or 0)

        reporte.append({
            "folio": f.folio_factura,
            "cliente": str(f.cliente),
            "fecha": f.fecha_pago.strftime("%d-%b-%Y") if f.fecha_pago else "",
            "total_venta": f.total or 0,
            "costo_proveedores": costo,
            "ganancia": ganancia,
            "productos_personalizados": pers or "Ninguno",
            "productos_no_personalizados": no_pers or "Ninguno",
        })

    tot_vta, tot_costo, tot_gan = _totales(qs)
    return render(request, "ventas/corte.html", {
        "modo": "flujo",
        "facturas": qs,
        "reporte": reporte,
        "fi": fi, "ff": ff,
        "totales": {
            "total_venta": tot_vta,
            "total_costo_proveedores": tot_costo,
            "total_ganancia": tot_gan,
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
    w.writerow(["Folio", "Cliente", "Fecha", "Total Venta", "Costo Proveedores",
                "Ganancia", "Productos Personalizados", "Productos No Personalizados"])

    for f in qs:
        costo = sum(d.cantidad * d.precio_compra for d in f.detalles.all())
        gan = (f.total or 0) - costo
        pers = sum(d.cantidad for d in f.detalles.all() if getattr(d.producto, "es_personalizado", False))
        no_pers = sum(d.cantidad for d in f.detalles.all() if not getattr(d.producto, "es_personalizado", False))
        fecha = (f.fecha_pago if modo == "flujo" else f.fecha_facturacion).strftime("%d-%b-%Y")
        w.writerow([f.folio_factura, f.cliente, fecha, f.total, costo, gan, pers, no_pers])

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
        gan = (f.total or 0) - costo
        fecha = (f.fecha_pago if modo == "flujo" else f.fecha_facturacion).strftime("%d-%b-%Y")

        p.drawString(80, y, f"Factura {f.folio_factura} - Cliente: {f.cliente}")
        p.drawString(80, y-15, f"Fecha: {fecha}  |  Total: {f.total}  |  Costo: {costo}  |  Ganancia: {gan}")
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
    for f in qs:
        costo = sum((d.cantidad or 0) * (d.precio_compra or 0) for d in f.detalles.all())
        ganancia = (f.total or 0) - costo
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
            "ganancia": float(ganancia),
            "productos_personalizados": pers or "Ninguno",
            "productos_no_personalizados": no_pers or "Ninguno",
        })

    tot_vta, tot_costo, tot_gan = _totales(qs)

    return JsonResponse({
        "modo": modo,
        "reporte": reporte,
        "totales": {
            "total_venta": float(tot_vta),
            "total_costo_proveedores": float(tot_costo),
            "total_ganancia": float(tot_gan),
            "productos_personalizados": "Ninguno",
            "productos_no_personalizados": "Ninguno",
        },
    })