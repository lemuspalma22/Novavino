from django.urls import path
from . import views

urlpatterns = [
    # API/auxiliares
    path("get_producto_precio/<int:producto_id>/", views.get_producto_precio, name="get_producto_precio"),
    path("api/producto-precios/<int:pk>/", views.api_producto_precios, name="api_producto_precios"),

    # Cortes
    path("corte-contable/", views.corte_contable, name="corte_contable"),
    path("corte-flujo/", views.corte_flujo, name="corte_flujo"),

    # Exportaciones (usan ?modo=contable|flujo & fecha_inicio=YYYY-MM-DD & fecha_fin=YYYY-MM-DD)
    path("exportar-csv/", views.exportar_csv, name="exportar_csv"),
    path("exportar-pdf/", views.exportar_pdf, name="exportar_pdf"),

        # Pantalla del corte + API JSON para el fetch del template
    path("corte-semanal/", views.corte_semanal_page, name="corte_semanal_page"),
    path("api/corte-semanal/", views.corte_semanal, name="corte_semanal"),

]
