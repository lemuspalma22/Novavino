# compras/views.py
from django.shortcuts import render
from .models import Compra
from compras.models import CompraProducto
from datetime import datetime

def compras_pagadas_vista(request):
    compras_pagadas = []
    fecha_inicio = fecha_fin = None
    
    if request.method == "POST":
        fecha_inicio = request.POST.get("fecha_inicio")
        fecha_fin = request.POST.get("fecha_fin")
        
        if fecha_inicio and fecha_fin:
            fecha_inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d").date()
            fecha_fin = datetime.strptime(fecha_fin, "%Y-%m-%d").date()
            compras_pagadas = Compra.objects.filter(
                pagado=True,
                fecha_pago__range=(fecha_inicio, fecha_fin)
            )
    
    return render(request, "compras/compras_pagadas.html", {
        "compras_pagadas": compras_pagadas,
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
    })


def corte_compras(request):
    compras = []
    fecha_inicio = None
    fecha_fin = None
    total_gastado = 0
    productos_personalizados = 0
    productos_no_personalizados = 0

    if request.method == "GET" and "fecha_inicio" in request.GET and "fecha_fin" in request.GET:
        fecha_inicio = request.GET.get("fecha_inicio")
        fecha_fin = request.GET.get("fecha_fin")

        fecha_inicio_dt = datetime.strptime(fecha_inicio, "%Y-%m-%d")
        fecha_fin_dt = datetime.strptime(fecha_fin, "%Y-%m-%d")

        compras = CompraProducto.objects.filter(
            compra__fecha__range=(fecha_inicio_dt, fecha_fin_dt)
        ).select_related('producto', 'compra')

        for producto in compras:
            subtotal = producto.subtotal()
            total_gastado += float(subtotal)
            if producto.producto.es_personalizado:
                productos_personalizados += producto.cantidad
            else:
                productos_no_personalizados += producto.cantidad

    contexto = {
        "compras": compras,
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
        "total_gastado": total_gastado,
        "productos_personalizados": productos_personalizados,
        "productos_no_personalizados": productos_no_personalizados,
    }
    return render(request, "compras/corte_compras.html", contexto)