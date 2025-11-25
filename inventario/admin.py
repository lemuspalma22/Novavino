from django.contrib import admin, messages
from django.db import transaction
from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect
from django.urls import path
from django import forms
from django.utils.html import format_html, format_html_join
from .models import Producto, AliasProducto, ProductoNoReconocido


# ------------------------------
# Producto
# ------------------------------
class ProductoAdminForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = "__all__"
        labels = {
            "precio_compra": "Precio compra (con impuestos)",
            "costo_transporte": "Costo transporte (por unidad)",
        }
        help_texts = {
            "precio_compra": "Precio final según factura, con impuestos. El transporte se guarda aparte en 'Costo transporte'.",
            "costo_transporte": "Costo adicional por unidad (p. ej. flete). Para Vieja Bodega sugerido: $28.",
        }

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display  = ("nombre", "proveedor", "precio_venta", "stock", "es_personalizado")
    list_filter   = ("proveedor", "es_personalizado")
    search_fields = ("nombre", "proveedor__nombre")
    change_list_template = "producto_changelist.html"
    actions = ["fusionar_productos"]
    form = ProductoAdminForm
    ordering = ["nombre"]  # Ordenar alfabéticamente por defecto

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
            # 1) mover alias del duplicado al maestro
            for alias in AliasProducto.objects.filter(producto=dup):
                texto = (alias.alias or "").strip()
                ya = AliasProducto.objects.filter(alias__iexact=texto, producto=maestro).exists()
                if not ya:
                    alias.producto = maestro
                    alias.save(update_fields=["producto"])
                    movidos_alias += 1
                else:
                    conflictos_alias += 1

            # 2) crear alias con el NOMBRE del duplicado apuntando al maestro (si no existe)
            nombre_dup = (dup.nombre or "").strip()
            if nombre_dup and not AliasProducto.objects.filter(alias__iexact=nombre_dup, producto=maestro).exists():
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

# Form intermedio para elegir el producto canónico en la acción masiva
class SeleccionarProductoDestinoForm(forms.Form):
    producto_destino = forms.ModelChoiceField(
        queryset=Producto.objects.all().order_by("nombre"),
        label="Producto existente",
        help_text="Selecciona el producto real al que se convertirán en alias los nombres detectados.",
        required=True,
    )

class ConciliarForm(forms.Form):
    producto_destino = forms.ModelChoiceField(
        queryset=Producto.objects.all().order_by("nombre"),
        label="Producto existente",
        required=True,
    )
    crear_alias = forms.BooleanField(initial=True, required=False, label="Crear alias con el nombre detectado")
    ejecutar_procesar = forms.BooleanField(initial=True, required=False, label="Ejecutar procesar_a_stock()")


# Form para ajustar etiquetas en el admin de ProductoNoReconocido
class ProductoNoReconocidoAdminForm(forms.ModelForm):
    crear_alias_al_guardar = forms.BooleanField(
        initial=True,
        required=False,
        label="Crear alias al guardar",
        help_text="Crea un alias con el nombre detectado hacia el producto seleccionado al guardar (desmarca si el nombre parece incompleto, p. ej. falta MP/SPIRO/BIB).",
    )

    class Meta:
        model = ProductoNoReconocido
        fields = "__all__"
        labels = {
            "precio_unitario": "Precio unitario (con impuestos)",
        }
        help_texts = {
            "precio_unitario": "Este precio ya incluye impuestos prorrateados. El transporte se maneja por separado como 'Costo transporte' del producto (para Vieja Bodega se sugiere $28 por unidad).",
            "procesado": "Marca esta casilla cuando ya asignaste el Producto correcto; al guardar se concilia y se genera el movimiento.",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            self.fields["producto"].queryset = Producto.objects.all().order_by("nombre")
        except Exception:
            pass


@admin.register(ProductoNoReconocido)
class ProductoNoReconocidoAdmin(admin.ModelAdmin):
    # ← AÑADIMOS columnas para la Opción B (producto, cantidad, precio_unitario, movimiento_generado)
    list_display  = (
        "nombre_detectado", "fecha_detectado", "uuid_factura",
        "origen", "procesado", "producto", "cantidad", "precio_unitario",
        "movimiento_generado",
    )
    form = ProductoNoReconocidoAdminForm
    list_filter   = ("procesado", "origen")
    search_fields = ("nombre_detectado", "uuid_factura")

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        try:
            crear_alias = form.cleaned_data.get("crear_alias_al_guardar")
        except Exception:
            crear_alias = False
        if crear_alias and getattr(obj, "producto_id", None) and getattr(obj, "procesado", False):
            alias_texto = (getattr(obj, "nombre_detectado", "") or "").strip()
            if alias_texto:
                try:
                    AliasProducto.objects.get_or_create(
                        alias=alias_texto,
                        defaults={"producto": obj.producto},
                        producto=obj.producto,
                    )
                except Exception:
                    pass

    # Conservamos tu acción masiva para convertir en alias
    actions = ["rellenar_desde_snapshot","convertir_en_alias","conciliar"]

    # Mostrar primero NO procesados (como tenías)
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(procesado=False)

    # --- Acción masiva: lleva a una vista intermedia con dropdown de producto ---
    def convertir_en_alias(self, request, queryset):
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
            path(
                "conciliar/",
                self.admin_site.admin_view(self.conciliar_view),
                name="inventario_conciliar",
            ),
        ]
        return custom + urls

    # Vista intermedia: muestra el form y aplica la creación de alias
    def convertir_alias_view(self, request):
        ids_raw = request.GET.get("ids", "")
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
                    # marca como procesado (la signal hará el resto si además asignas producto/cant/pu en edición)
                    if not obj.procesado:
                        obj.procesado = True
                        obj.save(update_fields=["procesado"])
                    creados += 1
                self.message_user(request, f"{creados} alias creados y registros marcados como procesados.")
                return redirect("../")
        else:
            form = SeleccionarProductoDestinoForm()

        context = {
            **self.admin_site.each_context(request),
            "title": "Convertir en alias de producto existente",
            "form": form,
            "objetos": objetos,
            "opts": self.model._meta,
            "ids": ids_raw,
        }
        return render(request, "admin/convertir_en_alias.html", context)

    def conciliar(self, request, queryset):
        ids = ",".join(str(pk) for pk in queryset.values_list("id", flat=True))
        return HttpResponseRedirect(f"conciliar/?ids={ids}")

    def conciliar_view(self, request):
        ids_raw = request.GET.get("ids", "")
        ids = [int(x) for x in ids_raw.split(",") if x.isdigit()]
        objetos = ProductoNoReconocido.objects.filter(id__in=ids)

        if request.method == "POST":
            form = ConciliarForm(request.POST)
            if form.is_valid():
                destino = form.cleaned_data["producto_destino"]
                crear_alias = form.cleaned_data.get("crear_alias", True)
                ejecutar = form.cleaned_data.get("ejecutar_procesar", True)
                procesados = 0
                creados_alias = 0
                with transaction.atomic():
                    for obj in objetos.select_for_update():
                        if obj.producto_id != destino.id:
                            obj.producto = destino
                        if not obj.procesado:
                            obj.procesado = True
                        obj.save(update_fields=["producto","procesado"]) if obj.producto_id else obj.save(update_fields=["procesado"]) 
                        if crear_alias:
                            try:
                                AliasProducto.objects.get_or_create(alias=obj.nombre_detectado, defaults={"producto": destino}, producto=destino)
                                creados_alias += 1
                            except Exception:
                                pass
                        if ejecutar:
                            try:
                                obj.procesar_a_stock()
                            except Exception:
                                pass
                        procesados += 1
                self.message_user(request, f"Conciliados: {procesados}. Alias creados: {creados_alias}.", level=messages.SUCCESS)
                return redirect("../")
        else:
            form = ConciliarForm()

        context = {
            **self.admin_site.each_context(request),
            "title": "Conciliar productos no reconocidos",
            "form": form,
            "objetos": objetos,
            "opts": self.model._meta,
            "ids": ids_raw,
        }
        return render(request, "admin/conciliar_no_reconocidos.html", context)

    # ← Campos visibles al editar un registro individual (para Opción B)
    fields = (
        "nombre_detectado",
        "fecha_detectado",
        "uuid_factura",
        "factura_relacionada",
        "origen",
        "producto",
        "cantidad",
        "precio_unitario",
        "procesado",
        "crear_alias_al_guardar",
        "movimiento_generado",
        "ver_lineas_detectadas",
    )
    readonly_fields = ("fecha_detectado", "factura_relacionada", "movimiento_generado", "ver_lineas_detectadas")

    def ver_lineas_detectadas(self, obj):
        conceptos = obj.raw_conceptos or []
        if not conceptos:
            return "-"
        rows = []
        for c in conceptos:
            desc = c.get("descripcion") or c.get("nombre") or ""
            cant = c.get("cantidad") or ""
            pu   = c.get("precio_unitario") or ""
            imp  = c.get("importe") or ""
            rows.append((str(desc), str(cant), str(pu), str(imp)))
        return format_html(
            "<div><strong>Líneas detectadas:</strong> <small style='color:#666'>(Valores base: sin impuestos)</small></div><ul style='margin:0;padding-left:16px'>{}</ul>",
            format_html_join("", "<li>{} | Cant: {} | PU: {} | Importe: {}</li>", ((d,c,p,i) for d,c,p,i in rows))
        )
    ver_lineas_detectadas.short_description = "Snapshot extractor"
    
    def factura_relacionada(self, obj):
        """Muestra el folio de la factura relacionada por UUID."""
        if not obj.uuid_factura:
            return "-"
        try:
            from compras.models import Compra
            compra = Compra.objects.filter(uuid=obj.uuid_factura).first()
            if compra:
                return format_html(
                    '<a href="/admin/compras/compra/{}/change/" target="_blank">Folio: {} ({})</a>',
                    compra.id,
                    compra.folio,
                    compra.proveedor.nombre if compra.proveedor else "Sin proveedor"
                )
            return format_html('<span style="color: #999;">No encontrada (UUID: {}...)</span>', obj.uuid_factura[:12])
        except Exception:
            return "-"
    factura_relacionada.short_description = "Factura relacionada (folio)"

    @admin.action(description="Rellenar cantidad y P.U. desde la primera línea detectada")
    def rellenar_desde_snapshot(self, request, queryset):
        updated = 0
        for obj in queryset:
            conceptos = obj.raw_conceptos or []
            if not conceptos:
                continue
            first = conceptos[0]
            cant = first.get("cantidad")
            pu   = first.get("precio_unitario")
            changed = False
            if cant is not None and obj.cantidad != cant:
                obj.cantidad = cant
                changed = True
            if pu is not None and obj.precio_unitario != pu:
                obj.precio_unitario = pu
                changed = True
            if changed:
                obj.save(update_fields=["cantidad","precio_unitario"])
                updated += 1
        if updated:
            self.message_user(request, f"{updated} elemento(s) prellenados desde snapshot.", level=messages.SUCCESS)
        else:
            self.message_user(request, "No había líneas detectadas o ya estaban prellenados.", level=messages.INFO)
