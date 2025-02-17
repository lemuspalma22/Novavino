# compras/views.py
from django.shortcuts import render
from .models import Compra
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
