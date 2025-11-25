from decimal import Decimal, InvalidOperation

TOL = Decimal("1000.00")  # Más permisivo para facturas con impuestos complejos

def _to_decimal_or_none(x):
    if x is None or (isinstance(x, str) and x.strip() == ""):
        return None
    s = str(x).strip().replace("$", "").replace(",", "")
    try:
        return Decimal(s)
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError(f"Valor numérico inválido: {x!r}")

def _D_req(x, field_name):
    v = _to_decimal_or_none(x)
    if v is None:
        raise ValueError(f"Falta valor requerido: {field_name}")
    return v

def _D_opt(x, default=0):
    v = _to_decimal_or_none(x)
    return Decimal(default) if v is None else v

def _coalesce(d, *keys):
    for k in keys:
        val = d.get(k)
        if val is not None and (not isinstance(val, str) or val.strip() != ""):
            return val
    return None

def _sum_conceptos(data):
    conceptos = data.get("conceptos") or data.get("productos") or []
    total = Decimal(0)
    for c in conceptos:
        if not isinstance(c, dict):
            continue
        if "importe" in c and c["importe"] is not None:
            imp = _to_decimal_or_none(c.get("importe"))
            if imp is not None:
                total += imp
                continue
        qty = _to_decimal_or_none(_coalesce(c, "cantidad", "qty", "Cantidad"))
        unit = _to_decimal_or_none(_coalesce(c, "precio_unitario", "unitario", "precio", "pu", "PrecioUnitario"))
        if qty is not None and unit is not None:
            total += qty * unit
    return total

def validate_invoice(data: dict, rfc_esperado: str | None = None, mode: str = "lenient"):
    warnings = []

    subtotal_raw = _coalesce(data, "subtotal", "SubTotal", "sub_total")
    total_raw    = _coalesce(data, "total", "Total", "importe_total", "monto_total")

    iva  = _D_opt(_coalesce(data, "iva", "IVA"))
    ieps = _D_opt(_coalesce(data, "ieps", "IEPS"))
    desc = _D_opt(_coalesce(data, "descuento", "Descuento"))

    subtotal = _to_decimal_or_none(subtotal_raw)
    if subtotal is None:
        suma_conc = _sum_conceptos(data)
        if suma_conc > 0:
            subtotal = suma_conc
            warnings.append("subtotal inferido desde conceptos")
        else:
            total_tmp = _to_decimal_or_none(total_raw)
            if total_tmp is not None:
                subtotal = total_tmp + desc - iva - ieps
                warnings.append("subtotal inferido desde total/impuestos/descuento")

    total = _to_decimal_or_none(total_raw)
    if total is None and subtotal is not None:
        total = subtotal - desc + iva + ieps
        warnings.append("total inferido desde subtotal/impuestos/descuento")

    if subtotal is None:
        if mode == "strict":
            raise ValueError("Falta valor requerido: subtotal")
        warnings.append("subtotal ausente (modo lenient)")
        subtotal = Decimal(0)

    if total is None:
        if mode == "strict":
            raise ValueError("Falta valor requerido: total")
        warnings.append("total ausente (modo lenient)")
        total = subtotal - desc + iva + ieps

    suma_conc = _sum_conceptos(data)
    if suma_conc > 0 and (suma_conc - subtotal).copy_abs() > TOL:
        # En modo lenient, solo advertir pero no fallar
        if mode == "lenient":
            warnings.append(f"Descuadre subtotal: conceptos={suma_conc} vs subtotal={subtotal}")
        else:
            raise ValueError(f"Descuadre subtotal: conceptos={suma_conc} vs subtotal={subtotal}")

    calculado = subtotal - desc + iva + ieps
    if (calculado - total).copy_abs() > TOL:
        # En modo lenient, solo advertir pero no fallar
        if mode == "lenient":
            warnings.append(f"Descuadre total: calc={calculado} vs total={total} (IVA={iva}, IEPS={ieps}, desc={desc})")
        else:
            raise ValueError(f"Descuadre total: calc={calculado} vs total={total} (IVA={iva}, IEPS={ieps}, desc={desc})")

    uuid = (data.get("uuid_sat") or data.get("uuid") or "").strip()
    if uuid:
        from compras.models import Compra
        qs = Compra.objects.all()
        prev = qs.filter(uuid_sat=uuid).first() if hasattr(Compra, "uuid_sat") else None
        if prev is None:
            prev = qs.filter(uuid=uuid).first()
        if prev and hasattr(prev, "total") and prev.total is not None:
            try:
                prev_total = Decimal(str(prev.total))
            except (InvalidOperation, ValueError, TypeError):
                prev_total = None
            if prev_total and (prev_total - total).copy_abs() > TOL:
                raise ValueError(f"UUID repetido con total distinto: prev={prev_total} vs actual={total}")

    if rfc_esperado:
        rfc_emisor = (data.get("rfc_emisor") or "").strip().upper()
        if rfc_emisor and rfc_emisor != rfc_esperado.strip().upper():
            raise ValueError(f"RFC emisor no coincide con alias: {rfc_emisor} ≠ {rfc_esperado}")

    if warnings:
        data["_warnings"] = warnings
    return data
