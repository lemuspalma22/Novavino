# compras/views.py
from django.shortcuts import render
from .models import Compra
from compras.models import CompraProducto
from datetime import datetime
from utils.reportes import calcular_agregados_periodo_compras

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

    # Debug: imprimir parámetros recibidos
    print(f"DEBUG - request.GET: {request.GET}")
    print(f"DEBUG - fecha_inicio: {request.GET.get('fecha_inicio')}")
    print(f"DEBUG - fecha_fin: {request.GET.get('fecha_fin')}")

    if request.method == "GET" and request.GET.get("fecha_inicio") and request.GET.get("fecha_fin"):
        fecha_inicio = request.GET.get("fecha_inicio")
        fecha_fin = request.GET.get("fecha_fin")
        
        print(f"DEBUG - Procesando fechas: {fecha_inicio} a {fecha_fin}")

        try:
            fecha_inicio_dt = datetime.strptime(fecha_inicio, "%Y-%m-%d")
            fecha_fin_dt = datetime.strptime(fecha_fin, "%Y-%m-%d")
            
            print(f"DEBUG - Fechas parseadas: {fecha_inicio_dt} a {fecha_fin_dt}")

            # Usar la nueva función abstraída
            agregados = calcular_agregados_periodo_compras(
                CompraProducto.objects.all(),
                fecha_inicio_dt,
                fecha_fin_dt
            )
            
            print(f"DEBUG - Agregados: {agregados}")
            
            compras = agregados['queryset']
            total_gastado = agregados['total_gastado']
            productos_personalizados = agregados['productos_personalizados']
            productos_no_personalizados = agregados['productos_no_personalizados']
            
            print(f"DEBUG - Compras encontradas: {len(compras)}")
            
        except Exception as e:
            print(f"DEBUG - Error: {e}")

    contexto = {
        "compras": compras,
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
        "total_gastado": total_gastado,
        "productos_personalizados": productos_personalizados,
        "productos_no_personalizados": productos_no_personalizados,
    }
    return render(request, "compras/corte_compras.html", contexto)