from django.urls import path
from .views import upload_csv, export_product_template_csv, upload_stock_csv

urlpatterns = [
    path('upload_csv/', upload_csv, name="upload_csv"),
    path('exportar_plantilla_csv/', export_product_template_csv, name="exportar_plantilla_csv"),
    path('upload_stock_csv/', upload_stock_csv, name="upload_stock_csv"),
]
