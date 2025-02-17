from django.urls import path
from .views import get_producto_precio

urlpatterns = [
    path("get_producto_precio/<int:producto_id>/", get_producto_precio, name="get_producto_precio"),
]
