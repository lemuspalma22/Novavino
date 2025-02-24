from django.urls import path
from .views import get_producto_precio
from .views import corte_semanal
from .views import exportar_csv
from .views import exportar_pdf

urlpatterns = [
    path("get_producto_precio/<int:producto_id>/", get_producto_precio, name="get_producto_precio"),
    path("corte-semanal/", corte_semanal, name="corte_semanal"),
    path("exportar-csv/", exportar_csv, name="exportar_csv"),
    path("exportar-pdf/", exportar_pdf, name="exportar_pdf"),
]

