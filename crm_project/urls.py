# crm_project/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('compras/', include('compras.urls')),  # Agrega esta línea
    path('inventario/', include('inventario.urls')),

]
