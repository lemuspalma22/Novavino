from datetime import date
from django.db.models import Sum
from .models import Compra, CompraProducto

def obtener_compras_pagadas(fecha_inicio: date, fecha_fin: date):
    """
    Obtiene todas las compras que han sido pagadas en un periodo de tiempo especificado.

    Args:
        fecha_inicio (date): La fecha de inicio del periodo.
        fecha_fin (date): La fecha de fin del periodo.

    Returns:
        QuerySet: Un QuerySet de compras que han sido pagadas en el periodo especificado.
    """
    compras_pagadas = Compra.objects.filter(
        pagado=True,
        fecha_pago__range=(fecha_inicio, fecha_fin)
    )
    return compras_pagadas
