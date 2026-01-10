import csv
import io
from decimal import Decimal, InvalidOperation
from collections import defaultdict
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from ventas.models import Factura, DetalleFactura
from inventario.models import Producto
from inventario.utils import encontrar_producto_unico  # usamos tu buscador seguro


class Command(BaseCommand):
    help = (
        "Importa facturas desde CSV de manera idempotente por folio. "
        "Si el folio ya existe, reemplaza TODOS los detalles dentro de una transacción "
        "(restaura stock de los detalles anteriores y descuenta el de los nuevos). "
        "Formato de columnas (mínimas): "
        "folio_factura,cliente,fecha_facturacion,producto,cantidad,precio_unitario"
    )

    def add_arguments(self, parser):
        parser.add_argument("csv_path", type=str, help="Ruta al CSV")
        parser.add_argument(
            "--encoding", default="utf-8-sig",
            help="Codificación del CSV (default: utf-8-sig)"
        )
        parser.add_argument(
            "--dry-run", action="store_true",
            help="No guarda cambios, solo simula"
        )

    def handle(self, *args, **opts):
        path = opts["csv_path"]
        encoding = opts["encoding"]
        dry = opts["dry_run"]

        try:
            with open(path, "rb") as f:
                data = f.read()
        except OSError as e:
            raise CommandError(f"No pude leer {path}: {e}")

        decoded = data.decode(encoding, errors="replace")
        reader = csv.DictReader(io.StringIO(decoded))
        required = {"folio_factura", "cliente", "fecha_facturacion", "producto", "cantidad", "precio_unitario"}
        if not required.issubset({c.strip() for c in reader.fieldnames or []}):
            raise CommandError(
                f"El CSV debe tener columnas: {', '.join(sorted(required))}. "
                f"Encontré: {reader.fieldnames}"
            )

        # Agrupar filas por folio
        grupos = defaultdict(list)
        for i, row in enumerate(reader, start=2):  # header es 1
            grupos[(row.get("folio_factura") or "").strip()].append((i, row))

        resumen = {"creadas": 0, "actualizadas": 0, "saltadas": 0, "errores": 0}
        problemas = []

        for folio, filas in grupos.items():
            if not folio:
                problemas.append(f"Folio vacío en grupo con {len(filas)} filas.")
                resumen["errores"] += 1
                continue

            try:
                # Transacción por FACTURA ⇒ (8) si algo falla, no queda a medias (stock incluido)
                with transaction.atomic():
                    # Idempotencia ⇒ si existe, reemplazamos detalles (borramos todos y recreamos)
                    factura, creada = Factura.objects.get_or_create(
                        folio_factura=folio,
                        defaults={
                            "cliente": (filas[0][1].get("cliente") or "").strip(),
                            # Ajusta parseo de fecha según formato que uses
                            "fecha_facturacion": (filas[0][1].get("fecha_facturacion") or timezone.now().date()),
                            "total": Decimal("0.00"),
                        },
                    )
                    if not creada:
                        # Si existe, actualizamos datos básicos
                        factura.cliente = (filas[0][1].get("cliente") or "").strip()
                        # Si traes fecha en CSV, setéala; si no, conserva la actual
                        fecha_csv = (filas[0][1].get("fecha_facturacion") or "").strip()
                        if fecha_csv:
                            factura.fecha_facturacion = fecha_csv  # parsea si necesitas DateField
                        factura.save(update_fields=["cliente", "fecha_facturacion"])

                        # Borrar TODOS los detalles actuales → signals restauran stock
                        DetalleFactura.objects.filter(factura=factura).delete()

                    # Crear los nuevos detalles según CSV → signals descuentan stock y recalculan total
                    for line_no, row in filas:
                        nombre = (row.get("producto") or "").strip()
                        if not nombre:
                            raise CommandError(f"[{folio}] Fila {line_no}: 'producto' vacío.")

                        prod, err = encontrar_producto_unico(nombre)
                        if err == "not_found":
                            raise CommandError(f"[{folio}] Fila {line_no}: producto '{nombre}' no encontrado.")
                        if err == "ambiguous":
                            raise CommandError(f"[{folio}] Fila {line_no}: producto '{nombre}' ambiguo.")

                        # cantidad
                        raw_qty = (row.get("cantidad") or "").strip()
                        try:
                            qty = int(Decimal(raw_qty))
                        except (InvalidOperation, ValueError):
                            raise CommandError(f"[{folio}] Fila {line_no}: cantidad inválida '{raw_qty}'.")

                        if qty <= 0:
                            raise CommandError(f"[{folio}] Fila {line_no}: cantidad debe ser > 0.")

                        # precio_unitario (si no viene, puedes tomar prod.precio_venta)
                        raw_pu = (row.get("precio_unitario") or "").strip()
                        if raw_pu == "":
                            precio_unitario = prod.precio_venta or Decimal("0.00")
                        else:
                            try:
                                precio_unitario = Decimal(raw_pu)
                            except InvalidOperation:
                                raise CommandError(f"[{folio}] Fila {line_no}: precio_unitario inválido '{raw_pu}'.")

                        # (Opcional) precio_compra si tu modelo lo trae en el detalle
                        raw_pc = (row.get("precio_compra") or "").strip()
                        precio_compra = None
                        if raw_pc != "":
                            try:
                                precio_compra = Decimal(raw_pc)
                            except InvalidOperation:
                                raise CommandError(f"[{folio}] Fila {line_no}: precio_compra inválido '{raw_pc}'.")

                        kwargs = {
                            "factura": factura,
                            "producto": prod,
                            "cantidad": qty,
                            "precio_unitario": precio_unitario,
                        }
                        if "precio_compra" in [f.name for f in DetalleFactura._meta.get_fields()]:
                            kwargs["precio_compra"] = precio_compra if precio_compra is not None else getattr(prod, "precio_compra", None)

                        DetalleFactura.objects.create(**kwargs)

                    # Al salir del with, signals ya recalcularon total y ajustaron stock por cada renglón
                    if dry:
                        # Forzar rollback “manual” en dry-run
                        raise transaction.TransactionManagementError("DRY-RUN: rollback intencional")

                    if creada:
                        resumen["creadas"] += 1
                    else:
                        resumen["actualizadas"] += 1

            except transaction.TransactionManagementError as e:
                if "DRY-RUN" in str(e):
                    self.stdout.write(self.style.WARNING(f"[{folio}] DRY-RUN exitoso (sin cambios)."))
                    continue
                resumen["errores"] += 1
                problemas.append(f"[{folio}] Error transaccional: {e}")
            except CommandError as e:
                resumen["errores"] += 1
                problemas.append(str(e))
            except Exception as e:
                resumen["errores"] += 1
                problemas.append(f"[{folio}] Error inesperado: {e}")

        # Reporte final
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(f"Facturas creadas: {resumen['creadas']}"))
        self.stdout.write(self.style.SUCCESS(f"Facturas actualizadas (reemplazadas): {resumen['actualizadas']}"))
        self.stdout.write(self.style.WARNING(f"Saltadas: {resumen['saltadas']}"))
        self.stdout.write(self.style.ERROR(f"Errores: {resumen['errores']}"))
        if problemas:
            self.stdout.write("\nDetalle de problemas:")
            for p in problemas:
                self.stdout.write(f"  - {p}")
