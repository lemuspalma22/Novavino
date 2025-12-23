from django.urls import path
from . import views

app_name = 'reportes'

urlpatterns = [
    path('', views.DashboardPrincipalView.as_view(), name='dashboard'),
    path('cuentas-por-cobrar/', views.CuentasPorCobrarView.as_view(), name='cuentas_por_cobrar'),
    path('cuentas-por-pagar/', views.CuentasPorPagarView.as_view(), name='cuentas_por_pagar'),
    path('flujo-caja/', views.FlujoCajaView.as_view(), name='flujo_caja'),
    path('distribucion-fondos/', views.DistribucionFondosView.as_view(), name='distribucion_fondos'),
]
