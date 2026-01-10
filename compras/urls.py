# compras/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("compras-pagadas/", views.compras_pagadas_vista, name="compras_pagadas"),
    path("corte-compras/", views.corte_compras, name="corte_compras"), 
]
