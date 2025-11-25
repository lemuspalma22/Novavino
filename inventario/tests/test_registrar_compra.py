import pytest
from decimal import Decimal
from django.utils.timezone import now
from django.db import transaction

from compras.models import Compra, CompraProducto, Proveedor
from inventario.models import Producto, AliasProducto, ProductoNoReconocido
from compras.utils.registrar_compra import registrar_compra_automatizada

pytestmark = pytest.mark.django_db

def _base_datos_extraidos(proveedor, productos, conceptos=None, folio="F-1", uuid="UUID-1", total="100.00"):
    return {
        "folio": folio,
        "uuid": uuid,
        "uuid_sat": uuid,
        "proveedor": proveedor,     # instancia FK requerida por registrar_compra
        "fecha_emision": now().date().isoformat(),
        "total": total,
        "productos": productos,
        "conceptos": conceptos or productos,  # para snapshot PNR si aplica
    }

def test_match_por_nombre_crea_detalle_y_suma_stock():
    prov = Proveedor.objects.create(nombre="Casa X")
    prod = Producto.objects.create(
        nombre="Cabernet 750",
        proveedor=prov,
        precio_compra=Decimal("120"),
        precio_venta=Decimal("200"),
        stock=0,
    )
    datos = _base_datos_extraidos(
        prov,
        productos=[{"nombre": "Cabernet 750", "cantidad": "2", "precio_unitario": "110"}],
        folio="C-001",
        uuid="U-001",
    )

    compra = registrar_compra_automatizada(datos)
    det = CompraProducto.objects.get(compra=compra)

    assert det.producto == prod
    assert det.cantidad == 2
    assert det.precio_unitario == Decimal("110")
    prod.refresh_from_db()
    assert prod.stock == 2  # suma stock en compras

def test_match_por_alias_crea_detalle():
    prov = Proveedor.objects.create(nombre="Casa Y")
    prod = Producto.objects.create(
        nombre="Malbec 750",
        proveedor=prov,
        precio_compra=Decimal("90"),
        precio_venta=Decimal("150"),
        stock=5,
    )
    AliasProducto.objects.create(alias="MLB 750", producto=prod)

    datos = _base_datos_extraidos(
        prov,
        productos=[{"nombre": "MLB 750", "cantidad": "3", "precio_unitario": "95"}],
        folio="C-002",
        uuid="U-002",
    )

    compra = registrar_compra_automatizada(datos)
    det = CompraProducto.objects.get(compra=compra)

    assert det.producto == prod
    assert det.cantidad == 3
    prod.refresh_from_db()
    assert prod.stock == 8

def test_ambiguo_no_crea_detalle_crea_pnr():
    prov = Proveedor.objects.create(nombre="Casa Z")
    p1 = Producto.objects.create(nombre="Sauvignon Blanc", proveedor=prov, precio_compra=Decimal("80"), precio_venta=Decimal("120"))
    p2 = Producto.objects.create(nombre="Sauvignon Reserva", proveedor=prov, precio_compra=Decimal("100"), precio_venta=Decimal("160"))

    # Ambigüedad por contiene (soft match): "Sauvignon"
    datos = _base_datos_extraidos(
        prov,
        productos=[{"nombre": "Sauvignon", "cantidad": "1", "precio_unitario": "100"}],
        folio="C-003",
        uuid="U-003",
    )

    compra = registrar_compra_automatizada(datos)
    assert CompraProducto.objects.filter(compra=compra).count() == 0
    pnr = ProductoNoReconocido.objects.get(uuid_factura="U-003")
    assert "Sauvignon" in pnr.nombre_detectado
    assert pnr.procesado is False
    assert pnr.origen == "compra"

def test_not_found_crea_pnr_con_snapshot():
    prov = Proveedor.objects.create(nombre="Casa W")

    conceptos = [{"descripcion": "Item misterioso", "cantidad": "4", "precio_unitario": "50"}]
    datos = _base_datos_extraidos(
        prov,
        productos=[{"nombre": "Item misterioso", "cantidad": "4", "precio_unitario": "50"}],
        conceptos=conceptos,
        folio="C-004",
        uuid="U-004",
    )

    compra = registrar_compra_automatizada(datos)
    assert CompraProducto.objects.filter(compra=compra).count() == 0

    pnr = ProductoNoReconocido.objects.get(uuid_factura="U-004")
    assert pnr.raw_conceptos is not None
    assert pnr.cantidad == Decimal("4")
    assert pnr.precio_unitario == Decimal("50")

def test_pu_faltante_se_prefillea_desde_conceptos_en_pnr():
    prov = Proveedor.objects.create(nombre="Casa V")
    conceptos = [{"descripcion": "Desconocido V", "cantidad": "2", "precio_unitario": "30"}]
    datos = _base_datos_extraidos(
        prov,
        productos=[{"nombre": "Desconocido V", "cantidad": "2"}],  # sin precio_unitario
        conceptos=conceptos,
        folio="C-005",
        uuid="U-005",
    )

    registrar_compra_automatizada(datos)
    pnr = ProductoNoReconocido.objects.get(uuid_factura="U-005")
    assert pnr.cantidad == Decimal("2")
    assert pnr.precio_unitario == Decimal("30")