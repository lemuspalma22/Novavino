from django.http import HttpResponse, JsonResponse
from inventario.models import Producto
from django.shortcuts import render
from .models import Factura, DetalleFactura
from datetime import datetime
import csv  # Importar csv para exportación a CSV
from reportlab.lib.pagesizes import letter  # Importar report lab para PDF
from reportlab.pdfgen import canvas

def get_producto_precio(request, producto_id):
    try:
        producto = Producto.objects.get(id=producto_id)
        return JsonResponse({"precio_unitario": str(producto.precio_venta)})
    except Producto.DoesNotExist:
        return JsonResponse({"error": "Producto no encontrado"}, status=404)

def corte_semanal(request):
    if request.method == "POST":
        fecha_inicio = request.POST.get("fecha_inicio")
        fecha_fin = request.POST.get("fecha_fin")

        # Convertir a tipo fecha
        fecha_inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d").date()
        fecha_fin = datetime.strptime(fecha_fin, "%Y-%m-%d").date()

        # Obtener facturas en el rango de fechas
        facturas = Factura.objects.filter(fecha_facturacion__range=[fecha_inicio, fecha_fin])

        # Inicializar totales
        total_venta = 0
        total_costo_proveedores = 0
        total_ganancia = 0
        total_productos_personalizados = {}
        total_productos_no_personalizados = {}

        reporte = []

        for factura in facturas:
            costo_proveedores = sum(detalle.cantidad * detalle.precio_compra for detalle in factura.detalles.all())
            ganancia = factura.total - costo_proveedores

            # Diccionarios de productos por factura
            productos_personalizados = {}
            productos_no_personalizados = {}

            for detalle in factura.detalles.all():
                producto = detalle.producto
                cantidad = detalle.cantidad

                if producto.es_personalizado:
                    productos_personalizados[producto.nombre] = productos_personalizados.get(producto.nombre, 0) + cantidad
                    total_productos_personalizados[producto.nombre] = total_productos_personalizados.get(producto.nombre, 0) + cantidad
                else:
                    productos_no_personalizados[producto.nombre] = productos_no_personalizados.get(producto.nombre, 0) + cantidad
                    total_productos_no_personalizados[producto.nombre] = total_productos_no_personalizados.get(producto.nombre, 0) + cantidad

            # Agregar datos al reporte
            reporte.append({
                "folio": factura.folio_factura,
                "cliente": factura.cliente,
                "fecha": factura.fecha_facturacion.strftime("%d-%b-%Y"),
                "total_venta": factura.total,
                "costo_proveedores": costo_proveedores,
                "ganancia": ganancia,
                "productos_personalizados": productos_personalizados if productos_personalizados else "Ninguno",
                "productos_no_personalizados": productos_no_personalizados if productos_no_personalizados else "Ninguno",
            })

            # Acumular totales
            total_venta += factura.total
            total_costo_proveedores += costo_proveedores
            total_ganancia += ganancia

        # Responder con JSON para el frontend
        return JsonResponse({
            "reporte": reporte,
            "totales": {
                "total_venta": total_venta,
                "total_costo_proveedores": total_costo_proveedores,
                "total_ganancia": total_ganancia,
                "productos_personalizados": total_productos_personalizados if total_productos_personalizados else "Ninguno",
                "productos_no_personalizados": total_productos_no_personalizados if total_productos_no_personalizados else "Ninguno",
            }
        })

    return render(request, "ventas/corte_semanal.html")


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
