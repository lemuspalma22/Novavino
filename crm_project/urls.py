# crm_project/urls.py
from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse

def home(request):
    return HttpResponse("¡El servidor está corriendo en Render!")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('compras/', include('compras.urls')),
    path('inventario/', include('inventario.urls')),
    path("ventas/", include("ventas.urls")),
    path('reportes/', include('reportes.urls')),  # Fase 3: Dashboards

]
