# ventas/extractors/novavino.py
import re
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from compras.extractors.pdf_reader import extract_text_from_pdf
from extractors.utils_extractores import extraer_total

MONEY_RE = re.compile(r"\$\s*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]{2})|[0-9]+(?:\.[0-9]{2}))")
SKU_LIKE_RE = re.compile(r"^[A-Z0-9\-]{2,12}$")
UNIT_RE = re.compile(r"^[A-Za-z0-9]{1,}(?:\s*-\s*[A-Za-z0-9]{1,})?$", re.IGNORECASE)  # p.ej. "H87 - Bot", "PZA"

def _to_decimal(s: str) -> Decimal | None:
    try:
        return Decimal(s.replace(",", ""))
    except Exception:
        return None

def _find_section(lines, start_kw, end_kw_opts):
    """Devuelve (i_start, i_end) de la sección entre start_kw y cualquiera de end_kw_opts."""
    i_start = None
    for i, ln in enumerate(lines):
        if start_kw in ln:
            i_start = i
            break
    if i_start is None:
        return None, None
    i_end = len(lines)
    for j in range(i_start + 1, len(lines)):
        if any(kw in lines[j] for kw in end_kw_opts):
            i_end = j
            break
    return i_start, i_end

def _line_es_meta(s: str) -> bool:
    s = (s or "").strip()
    if not s:
        return True
    meta_prefixes = (
        "Clave Prod. Serv.", "Impuestos:", "Traslados:", "Retenciones:",
        "Objeto Imp.", "Objeto de impuesto", "Objeto de Impuesto",
        "No. Identificación -", "No. Identificacion -", "Descripción", "Descripcion"
    )
    if any(s.startswith(p) for p in meta_prefixes):
        return True
    # Evita "02 - Sí objeto" y el renglón siguiente "de impuesto."
    if re.match(r"^\d{2}\s*-\s+Sí objeto", s) or s.lower() == "de impuesto.":
        return True
    # Línea que solo trae dinero
    if re.fullmatch(r"\$\s*[0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]{2})|\$\s*[0-9]+(?:\.[0-9]{2})", s):
        return True
    return False

def _es_producto_valido(nombre: str) -> bool:
    nombre = (nombre or "").strip()
    if not nombre:
        return False
    if nombre in {"0.00", "0", "00"}:
        return False
    # evita números/montos sueltos
    if re.fullmatch(r"^[-+]?\d{1,3}(?:,\d{3})*(?:\.\d+)?$|^\d+(\.\d+)?$", nombre):
        return False
    # cabeceras / ruido típico
    prohibidos = [
        r"^IEPS", r"^IVA", r"^pz$", r"^CP:", r"^\d{5}$", r"Comprobante", r"Pago", r"Emisión",
        r"^Fecha", r"^NOMBRE:", r"^RFC", r"^Uso CFDI", r"^SUBTOTAL", r"^TOTAL", r"^Importe",
        r"[A-Z]{5,}[0-9]{2,}", r"^No\. Identificaci[oó]n", r"^\d{2}\s*-\s+"
    ]
    for p in prohibidos:
        if re.search(p, nombre, re.IGNORECASE):
            return False
    return True

def extraer_factura_novavino(texto: str) -> dict:
    data = {
        "folio": None,
        "uuid": None,
        "fecha_emision": None,
        "cliente": None,
        "total": None,
        "metodo_pago": None,
        "productos": []
    }
    lines = [ln.rstrip() for ln in texto.splitlines()]

    # UUID
    m_uuid = re.search(r"[A-Z0-9]{8}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{12}", texto)
    if m_uuid:
        data["uuid"] = m_uuid.group(0)

    # Folio
    m_folio = re.search(r"Factura\s+(\d+)", texto, re.IGNORECASE)
    if m_folio:
        data["folio"] = m_folio.group(1)

    # Fecha emisión
    for i, ln in enumerate(lines):
        if "FECHA Y HORA DE EMISIÓN DE CFDI" in ln:
            if i + 1 < len(lines):
                data["fecha_emision"] = lines[i + 1].strip()
            break

    # Cliente
    for i, ln in enumerate(lines):
        if ln.strip() == "CLIENTE":
            if i + 1 < len(lines):
                data["cliente"] = lines[i + 1].strip()
            break

    # Método de pago (PUE/PPD)
    m_metodo = re.search(r"M[ée]todo de pago[:\s]+(PUE|PPD)", texto, re.IGNORECASE)
    if m_metodo:
        data["metodo_pago"] = m_metodo.group(1).upper()

    # Total robusto
    total_extraido = extraer_total(texto)
    data["total"] = Decimal(str(total_extraido)) if total_extraido is not None else None

    # ===== Productos =====
    i0, i1 = _find_section(lines, "CONCEPTOS", ["IMPORTE CON LETRA", "TOTAL"])
    if i0 is None:
        return data

    i = i0 + 1
    while i < i1:
        ln = lines[i].strip()
        # Detecta inicio de concepto: cantidad sola en la línea (ej. "2.00")
        m_qty = re.match(r"^(\d+(?:\.\d+)?)$", ln)
        if not m_qty:
            i += 1
            continue

        if i + 1 >= i1 or not UNIT_RE.match(lines[i + 1].strip()):
            i += 1
            continue

        cantidad = _to_decimal(m_qty.group(1))
        if not cantidad or cantidad <= 0:
            i += 1
            continue

        # === Nombre de producto, tolerando "No. Identificación" (SKU) ===
        nombre = None
        sku = None
        pos = i + 2  # después de la unidad

        if pos < i1 and SKU_LIKE_RE.fullmatch(lines[pos].strip()):
            sku = lines[pos].strip()
            pos += 1

        while pos < i1 and _line_es_meta(lines[pos]):
            pos += 1

        if pos < i1:
            nombre = lines[pos].strip()

        if not nombre or not _es_producto_valido(nombre):
            i += 1
            continue

        # Buscar precio base / importe
        precio_unitario = None
        importe = None
        j = i
        limit = min(i + 16, i1)

        # Precio unitario explícito
        for k in range(j, limit):
            lnk = lines[k]
            if "Precio Unitario" in lnk:
                m_money = MONEY_RE.search(lnk)
                if m_money:
                    cand = _to_decimal(m_money.group(1))
                    if cand:
                        precio_unitario = cand
                        break

        # Fallback: $ X.XX en línea suelta
        if precio_unitario is None:
            for k in range(j, limit):
                lnk = lines[k].strip()
                if "Importe -" in lnk or "IVA" in lnk or "IEPS" in lnk:
                    continue
                m_only = re.match(r"^\$\s*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]{2})|[0-9]+(?:\.[0-9]{2}))\s*$", lnk)
                if m_only:
                    precio_unitario = _to_decimal(m_only.group(1))
                    break

        # ==== Calcular impuestos por unidad (ahora soporta saltos de línea) ====
        def _read_wrapped_amount(idx_start: int, idx_end: int, needle: str) -> Decimal:
            k = idx_start
            while k < idx_end:
                l = lines[k]
                if needle in l and "Importe" in l:
                    # intentar mismo renglón
                    m = MONEY_RE.search(l)
                    if m:
                        dec = _to_decimal(m.group(1))
                        if dec is not None:
                            return dec
                    # intentar renglones siguientes cercanos
                    look = k + 1
                    while look < min(k + 4, idx_end):
                        l2 = lines[look].strip()
                        if not l2:
                            look += 1
                            continue
                        m2 = MONEY_RE.search(l2)
                        if m2:
                            dec = _to_decimal(m2.group(1))
                            if dec is not None:
                                return dec
                        m3 = re.match(r"^([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]{2})|[0-9]+(?:\.[0-9]{2}))$", l2)
                        if m3:
                            dec = _to_decimal(m3.group(1))
                            if dec is not None:
                                return dec
                        look += 1
                k += 1
            return Decimal("0.00")

        iva_total_line  = _read_wrapped_amount(j, limit, "002 IVA")
        ieps_total_line = _read_wrapped_amount(j, limit, "003 IEPS")

        iva_per_unit  = (iva_total_line / cantidad)  if iva_total_line and cantidad > 0 else Decimal("0.00")
        ieps_per_unit = (ieps_total_line / cantidad) if ieps_total_line and cantidad > 0 else Decimal("0.00")

        # Calcular precio final con impuestos
        if precio_unitario:
            precio_unitario_con_impuestos = (precio_unitario + iva_per_unit + ieps_per_unit).quantize(Decimal("0.01"))
        else:
            precio_unitario_con_impuestos = None

        print(f"[DEBUG Producto]")
        print(f"  Nombre: {nombre.strip()}")
        print(f"  Cantidad: {cantidad}")
        print(f"  Precio base: {precio_unitario}")
        print(f"  IVA por unidad: {iva_per_unit}")
        print(f"  IEPS por unidad: {ieps_per_unit}")
        print(f"  Precio final con impuestos: {precio_unitario_con_impuestos}")
        if precio_unitario_con_impuestos is not None and cantidad is not None:
            print(f"  Importe total producto: {precio_unitario_con_impuestos * cantidad}")
        print("--------------------------------------------------")

        if precio_unitario_con_impuestos and _es_producto_valido(nombre):
            data["productos"].append({
                "nombre": nombre.strip(),
                "cantidad": cantidad,
                "precio_unitario": precio_unitario_con_impuestos
            })

        # Avanza al siguiente posible concepto
        next_i = pos
        while next_i < i1:
            cand = lines[next_i].strip()
            if re.match(r"^(\d+(?:\.\d+)?)$", cand):
                if next_i + 1 < i1 and UNIT_RE.match(lines[next_i + 1].strip()):
                    break
            next_i += 1
        i = next_i

    # === Ajuste al centavo ===
    if data["productos"] and data["total"]:
        suma_importes = sum(p["cantidad"] * p["precio_unitario"] for p in data["productos"])
        diferencia = (data["total"] - suma_importes).quantize(Decimal("0.01"))
        if abs(diferencia) <= Decimal("0.02"):
            ultimo = data["productos"][-1]
            nuevo_precio_unitario = (ultimo["precio_unitario"] + (diferencia / ultimo["cantidad"])).quantize(Decimal("0.01"))
            data["productos"][-1]["precio_unitario"] = nuevo_precio_unitario

    return data

def extract_venta_data(pdf_path: str) -> dict:
    """Wrapper por si en algún punto llamas por ruta en lugar de texto."""
    texto = extract_text_from_pdf(pdf_path)
    return extraer_factura_novavino(texto)
