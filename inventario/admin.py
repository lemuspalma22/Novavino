from django.contrib import admin, messages
from django.db import transaction
from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect
from django.urls import path, reverse
from django import forms
from django.utils.html import format_html, format_html_join
from .models import Producto, AliasProducto, ProductoNoReconocido, LogFusionProductos
from .fusion import fusionar_productos_suave, fusionar_multiples_productos, deshacer_fusion, validar_fusion
import json


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
    list_display  = ("nombre", "proveedor", "precio_venta", "stock", "estado_fusion_display", "es_personalizado")
    list_filter   = ("activo", "proveedor", "es_personalizado")
    search_fields = ("nombre", "proveedor__nombre")
    change_list_template = "producto_changelist.html"
    actions = ["fusionar_productos_accion", "deshacer_fusion_accion"]
    form = ProductoAdminForm
    # ordering ya está definido en Meta del modelo como ['-activo', 'nombre']

    def estado_fusion_display(self, obj):
        """Muestra el estado de fusión del producto."""
        if not obj.activo:
            if obj.fusionado_en:
                return format_html(
                    '<span style="color: #e74c3c;">→ Fusionado en <a href="{}">{}</a></span>',
                    reverse('admin:inventario_producto_change', args=[obj.fusionado_en.id]),
                    obj.fusionado_en.nombre
                )
            return format_html('<span style="color: #999;">Inactivo</span>')
        
        count = obj.count_fusionados()
        if count > 0:
            return format_html(
                '<span style="color: #27ae60;">Activo ({} fusionado{})</span>',
                count,
                's' if count > 1 else ''
            )
        return format_html('<span style="color: #27ae60;">Activo</span>')
    estado_fusion_display.short_description = "Estado"
    
    @admin.action(description="Fusionar productos seleccionados (Fusión Suave)")
    def fusionar_productos_accion(self, request, queryset):
        """
        Nueva acción de fusión usando el sistema de Fusión Suave.
        No elimina productos, solo los marca como fusionados.
        """
        count = queryset.count()
        if count < 2:
            self.message_user(
                request,
                "Selecciona al menos 2 productos para fusionar.",
                level=messages.WARNING
            )
            return
        
        # Redirigir a vista de confirmación
        ids = ','.join(str(p.id) for p in queryset)
        return HttpResponseRedirect(
            reverse('admin:inventario_fusionar_confirmar') + f'?ids={ids}'
        )
    
    @admin.action(description="Deshacer fusión (reactivar productos)")
    def deshacer_fusion_accion(self, request, queryset):
        """
        Deshace la fusión de productos seleccionados, reactivándolos.
        Solo funciona con productos inactivos que fueron fusionados.
        """
        # Filtrar solo productos fusionados
        productos_fusionados = queryset.filter(activo=False, fusionado_en__isnull=False)
        
        if not productos_fusionados.exists():
            self.message_user(
                request,
                "Ninguno de los productos seleccionados está fusionado.",
                level=messages.WARNING
            )
            return
        
        # Deshacer cada fusión
        exitosos = 0
        errores = []
        
        for producto in productos_fusionados:
            resultado = deshacer_fusion(
                producto_fusionado=producto,
                restaurar_stock=True,
                usuario=request.user
            )
            
            if resultado['success']:
                exitosos += 1
            else:
                errores.append(f"{producto.nombre}: {resultado.get('error', 'Error desconocido')}")
        
        # Mensajes
        if exitosos > 0:
            self.message_user(
                request,
                f"Se deshicieron {exitosos} fusión(es) exitosamente.",
                level=messages.SUCCESS
            )
        
        if errores:
            for error in errores:
                self.message_user(request, error, level=messages.ERROR)
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'fusionar-confirmar/',
                self.admin_site.admin_view(self.fusionar_confirmar_view),
                name='inventario_fusionar_confirmar'
            ),
        ]
        return custom_urls + urls
    
    def fusionar_confirmar_view(self, request):
        """Vista de confirmación para fusión de productos."""
        ids_raw = request.GET.get('ids', '')
        ids = [int(x) for x in ids_raw.split(',') if x.isdigit()]
        productos = Producto.objects.filter(id__in=ids).order_by('nombre')
        
        if productos.count() < 2:
            messages.error(request, "Selecciona al menos 2 productos para fusionar.")
            return redirect('admin:inventario_producto_changelist')
        
        if request.method == 'POST':
            principal_id = request.POST.get('principal_id')
            razon = request.POST.get('razon', 'Productos duplicados')
            
            if not principal_id:
                messages.error(request, "Debes seleccionar el producto principal.")
                return redirect(request.path + f'?ids={ids_raw}')
            
            try:
                principal = Producto.objects.get(id=principal_id)
                secundarios = productos.exclude(id=principal_id)
                
                # Ejecutar fusión múltiple
                resultado = fusionar_multiples_productos(
                    principal,
                    secundarios,
                    request.user,
                    razon=razon
                )
                
                if resultado['success']:
                    messages.success(
                        request,
                        f"✓ Fusión completada: {resultado['fusionados']} producto(s) fusionado(s) en '{principal.nombre}'. "
                        f"Stock transferido: {resultado['stock_total_transferido']}"
                    )
                    
                    # Mostrar advertencias si las hay
                    for advertencia in resultado.get('advertencias', []):
                        messages.warning(request, advertencia)
                else:
                    for error in resultado.get('errores', []):
                        messages.error(request, error)
                
                return redirect('admin:inventario_producto_changelist')
                
            except Exception as e:
                messages.error(request, f"Error al fusionar: {str(e)}")
                return redirect('admin:inventario_producto_changelist')
        
        # GET: Mostrar formulario
        # Calcular vista previa
        stock_total = sum(p.stock or 0 for p in productos)
        
        # Validar cada combinación posible
        validaciones = {}
        for principal in productos:
            errores_total = []
            advertencias_total = []
            for secundario in productos:
                if principal.id != secundario.id:
                    es_valido, errores, advertencias = validar_fusion(principal, secundario)
                    errores_total.extend(errores)
                    advertencias_total.extend(advertencias)
            
            validaciones[principal.id] = {
                'es_valido': len(errores_total) == 0,
                'errores': list(set(errores_total)),
                'advertencias': list(set(advertencias_total))
            }
        
        # Preparar contexto base del admin
        admin_context = {}
        if self.admin_site:
            admin_context = self.admin_site.each_context(request)
        
        context = {
            **admin_context,
            'title': 'Confirmar Fusión de Productos',
            'productos': productos,
            'stock_total': stock_total,
            'validaciones': validaciones,
            'validaciones_json': json.dumps(validaciones),
            'ids': ids_raw,
            'opts': self.model._meta,
        }
        
        return render(request, 'admin/inventario/fusionar_confirmar.html', context)


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
                        # NOTA: No llamar obj.procesar_a_stock() aquí
                        # El signal post_save ya lo hace automáticamente cuando procesado=True
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


# ------------------------------
# Log de Fusión de Productos
# ------------------------------
@admin.register(LogFusionProductos)
class LogFusionProductosAdmin(admin.ModelAdmin):
    list_display = (
        'fecha_fusion',
        'producto_principal_display',
        'producto_secundario_nombre',
        'stock_transferido',
        'usuario',
        'revertida'
    )
    list_filter = ('revertida', 'fecha_fusion')
    search_fields = (
        'producto_principal__nombre',
        'producto_principal_nombre',
        'producto_secundario_nombre',
        'razon'
    )
    
    def producto_principal_display(self, obj):
        """Muestra el producto principal o su nombre si fue eliminado."""
        if obj.producto_principal:
            return format_html(
                '<a href="{}">{}</a>',
                reverse('admin:inventario_producto_change', args=[obj.producto_principal.id]),
                obj.producto_principal.nombre
            )
        return format_html(
            '<span style="color: #999;">{} (eliminado)</span>',
            obj.producto_principal_nombre
        )
    producto_principal_display.short_description = "Producto Principal"
    readonly_fields = (
        'producto_principal',
        'producto_secundario_id',
        'producto_secundario_nombre',
        'stock_transferido',
        'fecha_fusion',
        'usuario',
        'fecha_reversion'
    )
    
    fieldsets = (
        ('Información de Fusión', {
            'fields': (
                'producto_principal',
                'producto_secundario_id',
                'producto_secundario_nombre',
                'stock_transferido',
                'fecha_fusion',
                'usuario',
            )
        }),
        ('Razón', {
            'fields': ('razon',)
        }),
        ('Reversión', {
            'fields': ('revertida', 'fecha_reversion'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        # No permitir crear logs manualmente
        return False
    
    def has_delete_permission(self, request, obj=None):
        # No permitir eliminar logs
        return False
    
    def has_module_permission(self, request):
        # Ocultar del menú lateral, pero mantener accesible por URL
        return False
