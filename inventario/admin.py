from django.contrib import admin, messages
from django.db import transaction
from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect
from django.urls import path
from django import forms

from .models import Producto, AliasProducto, ProductoNoReconocido


# ------------------------------
# Producto
# ------------------------------
@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display  = ("nombre", "proveedor", "precio_venta", "stock", "es_personalizado")
    list_filter   = ("proveedor", "es_personalizado")
    search_fields = ("nombre", "proveedor__nombre")
    change_list_template = "producto_changelist.html"
    actions = ["fusionar_productos"]  # 👈 acción nueva

    @admin.action(description="Fusionar productos seleccionados (sumar stock y mover alias al primero)")
    @transaction.atomic
    def fusionar_productos(self, request, queryset):
        count = queryset.count()
        if count < 2:
            self.message_user(request, "Selecciona al menos 2 productos para fusionar.", level=messages.WARNING)
            return

        maestro = queryset.order_by("id").first()
        originales = list(queryset.exclude(pk=maestro.pk))

        stock_sumado = maestro.stock or 0
        conflictos_alias = 0
        creados_alias_nombre = 0
        movidos_alias = 0

        for dup in originales:
            # 1) mover todos los alias del duplicado al maestro
            for alias in AliasProducto.objects.filter(producto=dup):
                texto = (alias.alias or "").strip()
                # Evitar duplicados exactos (case-insensitive)
                ya = AliasProducto.objects.filter(alias__iexact=texto, producto=maestro).exists()
                if not ya:
                    alias.producto = maestro
                    alias.save(update_fields=["producto"])
                    movidos_alias += 1
                else:
                    conflictos_alias += 1

            # 2) crear un alias con el NOMBRE del duplicado apuntando al maestro (si no existe)
            nombre_dup = (dup.nombre or "").strip()
            if nombre_dup and not AliasProducto.objects.filter(alias__iexact=nombre_dup, producto=maestro).exists():
                # Si choca por la UniqueConstraint (cuando la agregues), captúralo
                try:
                    AliasProducto.objects.create(alias=nombre_dup, producto=maestro)
                    creados_alias_nombre += 1
                except Exception:
                    conflictos_alias += 1

            # 3) sumar stock
            stock_sumado += (dup.stock or 0)

            # 4) eliminar el duplicado
            dup.delete()

        # 5) guardar stock total en el maestro
        maestro.stock = stock_sumado
        maestro.save(update_fields=["stock"])

        self.message_user(
            request,
            (
                f"Fusión completada. Maestro: '{maestro.nombre}'. "
                f"Fusionados: {len(originales)}. "
                f"Stock total: {stock_sumado}. "
                f"Alias movidos: {movidos_alias}. "
                f"Alias creados desde nombre: {creados_alias_nombre}. "
                f"Conflictos de alias (omitidos): {conflictos_alias}."
            ),
            level=messages.SUCCESS,
        )
# ------------------------------
# Alias de producto
# ------------------------------
@admin.register(AliasProducto)
class AliasProductoAdmin(admin.ModelAdmin):
    list_display  = ("alias", "producto")
    search_fields = ("alias", "producto__nombre")


# ------------------------------
# Productos no reconocidos
# ------------------------------

# Form intermedio para elegir el producto canónico
class SeleccionarProductoDestinoForm(forms.Form):
    producto_destino = forms.ModelChoiceField(
        queryset=Producto.objects.all().order_by("nombre"),
        label="Producto existente",
        help_text="Selecciona el producto real al que se convertirán en alias los nombres detectados.",
        required=True,
    )


@admin.register(ProductoNoReconocido)
class ProductoNoReconocidoAdmin(admin.ModelAdmin):
    list_display  = ("nombre_detectado", "fecha_detectado", "uuid_factura", "procesado", "origen")
    list_filter   = ("procesado", "origen")
    search_fields = ("nombre_detectado", "uuid_factura")
    actions       = ["convertir_en_alias"]  # <- acción visible en el desplegable

    def get_queryset(self, request):
        """
        Por defecto mostramos los NO procesados (lo puedes quitar si prefieres ver todos).
        """
        qs = super().get_queryset(request)
        return qs.filter(procesado=False)

    # --- Acción: lleva a una vista intermedia con dropdown de producto ---
    def convertir_en_alias(self, request, queryset):
        # Guardamos los IDs seleccionados y vamos a la vista intermedia
        ids = ",".join(str(pk) for pk in queryset.values_list("id", flat=True))
        return HttpResponseRedirect(f"convertir-alias/?ids={ids}")

    convertir_en_alias.short_description = "Convertir en alias de producto existente"

    # Añadimos la URL de la vista intermedia
    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                "convertir-alias/",
                self.admin_site.admin_view(self.convertir_alias_view),
                name="inventario_convertir_alias",
            ),
        ]
        return custom + urls

    # Vista intermedia: muestra el form y aplica la creación de alias
    def convertir_alias_view(self, request):
        ids_raw = request.GET.get("ids", "")  # p.ej. "12,13,20"
        ids = [int(x) for x in ids_raw.split(",") if x.isdigit()]
        objetos = ProductoNoReconocido.objects.filter(id__in=ids)

        if request.method == "POST":
            form = SeleccionarProductoDestinoForm(request.POST)
            if form.is_valid():
                destino = form.cleaned_data["producto_destino"]
                creados = 0
                for obj in objetos:
                    # crea el alias (si no existe ya)
                    AliasProducto.objects.get_or_create(
                        alias=obj.nombre_detectado,
                        defaults={"producto": destino},
                        producto=destino,
                    )
                    # marca como procesado
                    if not obj.procesado:
                        obj.procesado = True
                        obj.save(update_fields=["procesado"])
                    creados += 1
                self.message_user(request, f"✅ {creados} alias creados y registros marcados como procesados.")
                return redirect("../")  # vuelve al changelist
        else:
            form = SeleccionarProductoDestinoForm()

        # Render simple usando plantilla del admin (puedes hacer una propia si quieres)
        context = {
            **self.admin_site.each_context(request),
            "title": "Convertir en alias de producto existente",
            "form": form,
            "objetos": objetos,
            "opts": self.model._meta,
            "ids": ids_raw,
        }
        return render(request, "admin/convertir_en_alias.html", context)
