import csv
import io
from decimal import Decimal, InvalidOperation
from django.http import HttpResponse
from django.shortcuts import render
from .models import Producto
from compras.models import Proveedor
from .forms import CSVUploadForm
from .utils import encontrar_producto_unico


# --- Exportar plantilla CSV con todos los productos ---
def export_product_template_csv(request):
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="plantilla_productos.csv"'
    writer = csv.writer(response)
    writer.writerow([
        "nombre","uva","tipo","descripcion","proveedor",
        "precio_compra","precio_venta","es_personalizado","stock"
    ])
    for p in Producto.objects.select_related("proveedor").all().order_by("nombre"):
        writer.writerow([
            p.nombre or "",
            p.uva or "",
            p.tipo or "",
            p.descripcion or "",
            p.proveedor.nombre if p.proveedor else "",
            f"{p.precio_compra:.2f}",
            f"{p.precio_venta:.2f}",
            "1" if p.es_personalizado else "0",
            p.stock or 0,
        ])
    return response

# --- Cargar conteo físico y AJUSTAR stock ---
def upload_stock_csv(request):
    contexto = {"form": CSVUploadForm(), "procesados": 0, "no_encontrados": []}
    if request.method == "POST":
        form = CSVUploadForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES["file"]
            decoded = csv_file.read().decode("utf-8-sig")
            reader = csv.DictReader(io.StringIO(decoded))

            procesados = 0
            no_encontrados = []

            for row in reader:
                raw_nombre = (row.get("producto") or "").strip()
                raw_stock = (row.get("stock") or "").strip()
                if not raw_nombre:
                    continue

                prod, err = encontrar_producto_unico(raw_nombre)
                if err == "not_found":
                    no_encontrados.append(f"{raw_nombre} (no encontrado)")
                    continue
                if err == "ambiguous":
                    no_encontrados.append(f"{raw_nombre} (ambigüo: coincide con varios productos/alias)")
                    continue
                
                try:
                    nuevo_stock = int(Decimal(raw_stock))
                except (InvalidOperation, ValueError):
                    no_encontrados.append(f"{raw_nombre} (stock inválido: {raw_stock})")
                    continue

                prod.stock = max(0, nuevo_stock)
                prod.save(update_fields=["stock"])
                procesados += 1

            contexto.update({"procesados": procesados, "no_encontrados": no_encontrados, "ok": True})
            return render(request, "upload_stock_result.html", contexto)

        contexto["form"] = form
        return render(request, "upload_stock.html", contexto)

    return render(request, "upload_stock.html", contexto)

# --- Alta/actualización masiva de productos ---
def upload_csv(request):
    if request.method == "POST":
        form = CSVUploadForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES["file"]
            decoded_file = csv_file.read().decode('utf-8-sig')
            csv_reader = csv.DictReader(io.StringIO(decoded_file))

            creados, actualizados, errores = 0, 0, []

            def as_decimal(v):
                try:
                    return Decimal((v or "0")).quantize(Decimal("0.01"))
                except (InvalidOperation, ValueError):
                    return Decimal("0.00")

            def as_int(v, default=0):
                try:
                    return int(Decimal(v))
                except Exception:
                    return default

            for row in csv_reader:
                try:
                    prov_name = (row.get("proveedor") or "").strip()
                    proveedor = None
                    if prov_name:
                        proveedor, _ = Proveedor.objects.get_or_create(nombre=prov_name)

                    nombre = (row.get("nombre") or "").strip()
                    if not nombre:
                        continue

                    defaults = {
                        "uva": (row.get("uva") or "").strip() or None,
                        "tipo": (row.get("tipo") or "").strip() or None,   # tinto|blanco|rosado
                        "descripcion": (row.get("descripcion") or "").strip() or None,
                        "proveedor": proveedor,
                        "precio_compra": as_decimal(row.get("precio_compra")),
                        "precio_venta": as_decimal(row.get("precio_venta")),
                        "es_personalizado": (str(row.get("es_personalizado") or "0").strip() in ("1","true","True")),
                        "stock": as_int(row.get("stock"), 0),
                    }

                    obj, created = Producto.objects.update_or_create(
                        nombre=nombre,
                        defaults=defaults
                    )
                    creados += 1 if created else 0
                    actualizados += 0 if created else 1

                except Exception as e:
                    errores.append(f"{row.get('nombre')}: {e}")

            return render(
                request,
                "upload_success.html",
                {"creados": creados, "actualizados": actualizados, "errores": errores},
            )
    else:
        form = CSVUploadForm()

    return render(request, "upload_csv.html", {"form": form})
