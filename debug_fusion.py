"""
Script de debug para probar la vista de fusión
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()

from inventario.admin import ProductoAdmin
from inventario.models import Producto
from django.test import RequestFactory
from django.contrib.auth import get_user_model
from django.contrib.admin.sites import AdminSite

# Simular request
factory = RequestFactory()
request = factory.get('/admin/inventario/producto/fusionar-confirmar/?ids=457,357')
User = get_user_model()
request.user = User.objects.first()

# Crear admin con admin_site
site = AdminSite()
admin = ProductoAdmin(Producto, site)

# Intentar la vista
try:
    response = admin.fusionar_confirmar_view(request)
    print("✓ Funciona!")
    print(f"Status code: {response.status_code}")
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
