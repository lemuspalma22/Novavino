from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from inventario.models import Producto, AliasProducto
from compras.models import Proveedor


class InventarioViewsTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Datos base
        self.proveedor = Proveedor.objects.create(nombre="Vieja Bodega")
        self.producto = Producto.objects.create(
            nombre="VT ANÉCDOTA BLEND",
            uva="Merlot-Cabernet",
            tipo="tinto",
            descripcion="Vino tinto blend",
            proveedor=self.proveedor,
            precio_compra="207.85",
            precio_venta="305.00",
            es_personalizado=False,
            stock=5,
        )
        # Alias para probar búsqueda por alias
        self.alias = AliasProducto.objects.create(alias="ANÉCDOTA BLEND", producto=self.producto)

    # -----------------------------
    # export_product_template_csv
    # -----------------------------
    def test_export_product_template_csv_ok(self):
        url = reverse("exportar_plantilla_csv")
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)
        # Content-Type CSV con charset
        self.assertTrue(resp["Content-Type"].startswith("text/csv"))
        # Disposition correcto
        self.assertIn("filename=", resp["Content-Disposition"])

        content = resp.content.decode("utf-8").splitlines()
        # Primera fila = encabezados esperados
        header = content[0].split(",")
        self.assertEqual(
            header,
            [
                "nombre",
                "uva",
                "tipo",
                "descripcion",
                "proveedor",
                "precio_compra",
                "precio_venta",
                "es_personalizado",
                "stock",
            ],
        )
        # Debe incluir el producto exportado
        csv_body = "\n".join(content[1:])
        self.assertIn("VT ANÉCDOTA BLEND", csv_body)
        self.assertIn("Vieja Bodega", csv_body)
        self.assertIn("305.00", csv_body)

    # -----------------------------
    # upload_stock_csv
    # -----------------------------
    def test_upload_stock_csv_updates_stock_by_name(self):
        url = reverse("upload_stock_csv")
        csv_text = "producto,stock\nVT ANÉCDOTA BLEND,12\n"
        upload = SimpleUploadedFile("conteo.csv", csv_text.encode("utf-8"), content_type="text/csv")

        resp = self.client.post(url, data={"file": upload}, follow=True)

        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "upload_stock_result.html")

        # Verifica cambio en BD
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 12)

        # Verifica mensaje de éxito genérico y que no hubo "No encontrados"
        self.assertContains(resp, "Productos actualizados")
        self.assertNotContains(resp, "No encontrados")


    def test_upload_stock_csv_updates_stock_by_alias(self):
        # Cambiamos stock actual para ver el ajuste
        self.producto.stock = 3
        self.producto.save(update_fields=["stock"])

        url = reverse("upload_stock_csv")
        csv_text = "producto,stock\nANÉCDOTA BLEND,9\n"  # usamos el alias
        upload = SimpleUploadedFile("conteo_alias.csv", csv_text.encode("utf-8"), content_type="text/csv")

        resp = self.client.post(url, data={"file": upload}, follow=True)

        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "upload_stock_result.html")

        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 9)

    def test_upload_stock_csv_handles_invalid_stock_and_unknown(self):
        url = reverse("upload_stock_csv")
        csv_text = (
            "producto,stock\n"
            "DESCONOCIDO,5\n"       # no existe
            "VT ANÉCDOTA BLEND,abc\n"  # stock inválido
        )
        upload = SimpleUploadedFile("conteo_mixto.csv", csv_text.encode("utf-8"), content_type="text/csv")

        resp = self.client.post(url, data={"file": upload}, follow=True)

        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "upload_stock_result.html")

        # No debe haber cambiado el stock del producto válido por valor inválido
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 5)

        # Debe listar "no_encontrados" o mensajes de error visibles
        self.assertContains(resp, "No encontrados")
        self.assertContains(resp, "DESCONOCIDO")
        self.assertContains(resp, "stock inválido")

class UploadCSVTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse("upload_csv")

    def _post_csv(self, csv_text: str):
        upload = SimpleUploadedFile("productos.csv", csv_text.encode("utf-8"), content_type="text/csv")
        return self.client.post(self.url, data={"file": upload}, follow=True)

    def test_upload_csv_creates_product_and_provider(self):
        csv_text = (
            "nombre,uva,tipo,descripcion,proveedor,precio_compra,precio_venta,es_personalizado,stock\n"
            "VT ANÉCDOTA BLEND,Merlot-Cabernet,tinto,Vino tinto,Vieja Bodega,207.85,305.00,0,18\n"
        )
        resp = self._post_csv(csv_text)
        self.assertEqual(resp.status_code, 200)

        prov = Proveedor.objects.get(nombre="Vieja Bodega")
        prod = Producto.objects.get(nombre="VT ANÉCDOTA BLEND")
        self.assertEqual(prod.proveedor, prov)
        self.assertEqual(str(prod.precio_compra), "207.85")
        self.assertEqual(str(prod.precio_venta), "305.00")
        self.assertEqual(prod.es_personalizado, False)
        self.assertEqual(prod.stock, 18)

    def test_upload_csv_updates_existing_product_instead_of_dup(self):
        prov = Proveedor.objects.create(nombre="Vieja Bodega")
        prod = Producto.objects.create(
            nombre="VT ANÉCDOTA BLEND",
            uva="Merlot-Cabernet",
            tipo="tinto",
            descripcion="Viejo desc",
            proveedor=prov,
            precio_compra="100.00",
            precio_venta="200.00",
            es_personalizado=False,
            stock=5,
        )
        csv_text = (
            "nombre,uva,tipo,descripcion,proveedor,precio_compra,precio_venta,es_personalizado,stock\n"
            "VT ANÉCDOTA BLEND,Merlot,tinto,Nuevo desc,Vieja Bodega,150.50,250.75,1,12\n"
        )
        resp = self._post_csv(csv_text)
        self.assertEqual(resp.status_code, 200)

        # No duplica
        self.assertEqual(Producto.objects.filter(nombre="VT ANÉCDOTA BLEND").count(), 1)
        prod.refresh_from_db()
        self.assertEqual(prod.uva, "Merlot")
        self.assertEqual(prod.descripcion, "Nuevo desc")
        self.assertEqual(str(prod.precio_compra), "150.50")
        self.assertEqual(str(prod.precio_venta), "250.75")
        self.assertTrue(prod.es_personalizado)
        self.assertEqual(prod.stock, 12)

    def test_upload_csv_parses_boolean_and_stock_variants(self):
        # true/True/1 deben ser True; 0/false vacíos -> False
        csv_text = (
            "nombre,uva,tipo,descripcion,proveedor,precio_compra,precio_venta,es_personalizado,stock\n"
            "A, , , ,P1,10,20,True,7\n"
            "B, , , ,P2,10,20,true,8\n"
            "C, , , ,P3,10,20,1,9\n"
            "D, , , ,P4,10,20,0,0\n"
            "E, , , ,P5,10,20,,\n"
        )
        resp = self._post_csv(csv_text)
        self.assertEqual(resp.status_code, 200)

        self.assertTrue(Producto.objects.get(nombre="A").es_personalizado)
        self.assertTrue(Producto.objects.get(nombre="B").es_personalizado)
        self.assertTrue(Producto.objects.get(nombre="C").es_personalizado)
        self.assertFalse(Producto.objects.get(nombre="D").es_personalizado)
        self.assertFalse(Producto.objects.get(nombre="E").es_personalizado)

        self.assertEqual(Producto.objects.get(nombre="A").stock, 7)
        self.assertEqual(Producto.objects.get(nombre="B").stock, 8)
        self.assertEqual(Producto.objects.get(nombre="C").stock, 9)
        self.assertEqual(Producto.objects.get(nombre="D").stock, 0)
        self.assertEqual(Producto.objects.get(nombre="E").stock, 0)

    def test_upload_csv_skips_row_without_nombre(self):
        csv_text = (
            "nombre,uva,tipo,descripcion,proveedor,precio_compra,precio_venta,es_personalizado,stock\n"
            ",,, ,P1,10,20,1,5\n"   # sin nombre -> debe ignorarse
            "Con Nombre, , , ,P2,10,20,0,3\n"
        )
        resp = self._post_csv(csv_text)
        self.assertEqual(resp.status_code, 200)

        self.assertFalse(Producto.objects.filter(proveedor__nombre="P1").exists())
        self.assertTrue(Producto.objects.filter(nombre="Con Nombre", proveedor__nombre="P2").exists())