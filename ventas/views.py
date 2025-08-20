from django.http import HttpResponse, JsonResponse
from inventario.models import Producto
from django.shortcuts import render
from .models import Factura, DetalleFactura
from datetime import datetime
import csv  # Importar csv para exportación a CSV
from reportlab.lib.pagesizes import letter  # Importar report lab para PDF
from reportlab.pdfgen import canvas
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse, Http404

def get_producto_precio(request, producto_id):
    try:
        producto = Producto.objects.get(id=producto_id)
        return JsonResponse({"precio_unitario": str(producto.precio_venta)})
    except Producto.DoesNotExist:
        return JsonResponse({"error": "Producto no encontrado"}, status=404)

def _parse_date(s: str):
    if not s:
        return None
    try:
        # Inputs type="date" llegan como YYYY-MM-DD
        return datetime.strptime(s, "%Y-%m-%d").date()
    except Exception:
        return None

@require_http_methods(["GET", "POST"])
def corte_semanal(request):
    """
    GET  con ?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD  -> JSON (para el fetch)
    POST con fecha_inicio/fecha_fin                      -> JSON (compatibilidad)
    GET sin parámetros                                   -> render del template
    """
    # 1) Leer parámetros (soporta ambos nombres y métodos)
    start_raw = request.GET.get("start_date") or request.POST.get("fecha_inicio")
    end_raw   = request.GET.get("end_date")   or request.POST.get("fecha_fin")

    start_date = _parse_date(start_raw)
    end_date   = _parse_date(end_raw)

    # Si no hay fechas: render normal del template (carga inicial de la página)
    if not (start_date and end_date):
        return render(request, "ventas/corte_semanal.html")

    # 2) Query (optimizada con prefetch)
    facturas = (
        Factura.objects
        .filter(fecha_facturacion__range=[start_date, end_date])
        .prefetch_related("detalles__producto")
    )

    # 3) Acumuladores
    total_venta = 0
    total_costo_proveedores = 0
    total_ganancia = 0
    total_productos_personalizados = {}
    total_productos_no_personalizados = {}

    reporte = []

    for factura in facturas:
        # Costo de proveedores por factura
        costo_proveedores = sum(
            (det.cantidad or 0) * (det.precio_compra or 0)
            for det in factura.detalles.all()
        )
        ganancia = (factura.total or 0) - costo_proveedores

        # Diccionarios por factura
        productos_personalizados = {}
        productos_no_personalizados = {}

        for det in factura.detalles.all():
            producto = det.producto
            cantidad = det.cantidad or 0
            if getattr(producto, "es_personalizado", False):
                productos_personalizados[producto.nombre] = (
                    productos_personalizados.get(producto.nombre, 0) + cantidad
                )
                total_productos_personalizados[producto.nombre] = (
                    total_productos_personalizados.get(producto.nombre, 0) + cantidad
                )
            else:
                productos_no_personalizados[producto.nombre] = (
                    productos_no_personalizados.get(producto.nombre, 0) + cantidad
                )
                total_productos_no_personalizados[producto.nombre] = (
                    total_productos_no_personalizados.get(producto.nombre, 0) + cantidad
                )

        reporte.append({
            "folio": getattr(factura, "folio_factura", ""),
            # Si cliente es FK, lo convertimos a string legible
            "cliente": str(getattr(factura, "cliente", "")),
            "fecha": factura.fecha_facturacion.strftime("%d-%b-%Y"),
            "total_venta": factura.total or 0,
            "costo_proveedores": costo_proveedores,
            "ganancia": ganancia,
            "productos_personalizados": productos_personalizados or "Ninguno",
            "productos_no_personalizados": productos_no_personalizados or "Ninguno",
        })

        total_venta += (factura.total or 0)
        total_costo_proveedores += costo_proveedores
        total_ganancia += ganancia

    return JsonResponse({
        "reporte": reporte,
        "totales": {
            "total_venta": total_venta,
            "total_costo_proveedores": total_costo_proveedores,
            "total_ganancia": total_ganancia,
            "productos_personalizados": total_productos_personalizados or "Ninguno",
            "productos_no_personalizados": total_productos_no_personalizados or "Ninguno",
        }
    })


def exportar_csv(request):
    fecha_inicio = request.GET.get("fecha_inicio")
    fecha_fin = request.GET.get("fecha_fin")

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="corte_semanal.csv"'
    
    writer = csv.writer(response)
    writer.writerow(["Folio", "Cliente", "Fecha", "Total Venta", "Costo Proveedores", "Ganancia", "Productos Personalizados", "Productos No Personalizados"])

    facturas = Factura.objects.filter(fecha_facturacion__range=[fecha_inicio, fecha_fin])
    
    for factura in facturas:
        costo_proveedores = sum(detalle.cantidad * detalle.precio_compra for detalle in factura.detalles.all())
        ganancia = factura.total - costo_proveedores

        productos_personalizados = sum(
            detalle.cantidad for detalle in factura.detalles.all() if detalle.producto.es_personalizado
        )
        productos_no_personalizados = sum(
            detalle.cantidad for detalle in factura.detalles.all() if not detalle.producto.es_personalizado
        )

        writer.writerow([
            factura.folio_factura,
            factura.cliente,
            factura.fecha_facturacion.strftime("%d-%b-%Y"),
            factura.total,
            costo_proveedores,
            ganancia,
            productos_personalizados,
            productos_no_personalizados
        ])

    return response


def exportar_pdf(request):
    fecha_inicio = request.GET.get("fecha_inicio")
    fecha_fin = request.GET.get("fecha_fin")

    if not fecha_inicio or not fecha_fin:
        return HttpResponse("Error: Debes proporcionar un rango de fechas válido en el formato YYYY-MM-DD.", status=400)

    try:
        fecha_inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d").date()
        fecha_fin = datetime.strptime(fecha_fin, "%Y-%m-%d").date()
    except ValueError:
        return HttpResponse("Error: Formato de fecha inválido. Debe ser YYYY-MM-DD.", status=400)

    facturas = Factura.objects.filter(fecha_facturacion__range=[fecha_inicio, fecha_fin])

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="corte_semanal.pdf"'
    
    p = canvas.Canvas(response, pagesize=letter)
    p.drawString(100, 750, "Reporte de Corte Semanal")

    y = 730
    for factura in facturas:
        costo_proveedores = sum(detalle.cantidad * detalle.precio_compra for detalle in factura.detalles.all())
        ganancia = factura.total - costo_proveedores

        productos_personalizados = sum(
            detalle.cantidad for detalle in factura.detalles.all() if detalle.producto.es_personalizado
        )
        productos_no_personalizados = sum(
            detalle.cantidad for detalle in factura.detalles.all() if not detalle.producto.es_personalizado
        )

        p.drawString(100, y, f"Factura {factura.folio_factura} - Cliente: {factura.cliente}")
        p.drawString(100, y-15, f"Total: {factura.total} | Costo Proveedores: {costo_proveedores} | Ganancia: {ganancia}")
        p.drawString(100, y-30, f"Personalizados: {productos_personalizados} | No Personalizados: {productos_no_personalizados}")
        y -= 50

    p.showPage()
    p.save()
    return response

def api_producto_precios(request, pk: int):
    try:
        p = Producto.objects.get(pk=pk)
    except Producto.DoesNotExist:
        raise Http404("Producto no encontrado")

    # Ajusta los nombres de campo si en tu modelo se llaman diferente
    precio_venta = getattr(p, "precio_unitario", None) or getattr(p, "precio_venta", 0) or 0
    precio_compra = getattr(p, "precio_compra", 0) or 0

    return JsonResponse({
        "precio_venta": float(precio_venta),
        "precio_compra": float(precio_compra),
    })