import csv
import io
from django.shortcuts import render
from .models import Producto
from compras.models import Proveedor
from .forms import CSVUploadForm

def upload_csv(request):
    if request.method == "POST":
        form = CSVUploadForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES["file"]
            
            # Leer el contenido del archivo
            decoded_file = csv_file.read().decode('utf-8-sig')  # Manejo de codificación
            csv_reader = csv.DictReader(io.StringIO(decoded_file))
            
            for row in csv_reader:
                proveedor, _ = Proveedor.objects.get_or_create(nombre=row["proveedor"])
                
                Producto.objects.create(
                    nombre=row["nombre"],
                    uva=row["uva"],
                    tipo=row["tipo"],
                    descripcion=row["descripcion"],
                    proveedor=proveedor,
                    precio_compra=row["precio_compra"],
                    precio_venta=row["precio_venta"]
                )

            return render(request, "upload_success.html")  # Plantilla de éxito

    else:
        form = CSVUploadForm()

    return render(request, "upload_csv.html", {"form": form})