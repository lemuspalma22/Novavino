# ventas/extractors/novavino.py
import re
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from compras.extractors.pdf_reader import extract_text_from_pdf
from extractors.utils_extractores import extraer_total

MONEY_RE = re.compile(r"\$\s*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]{2})|[0-9]+(?:\.[0-9]{2}))")

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

def _es_producto_valido(nombre: str) -> bool:
    nombre = (nombre or "").strip()
    if not nombre:
        return False
    if nombre in {"0.00", "0", "00"}:
        return False
    # evita números montos sueltos
    if re.fullmatch(r"^[-+]?\d{1,3}(?:,\d{3})*(?:\.\d+)?$|^\d+(\.\d+)?$", nombre):
        return False
    # cabeceras / ruido típico
    prohibidos = [
        r"^IEPS", r"^IVA", r"^pz$", r"^CP:", r"^\d{5}$", r"Comprobante", r"Pago", r"Emisión",
        r"^Fecha", r"^NOMBRE:", r"^RFC", r"^Uso CFDI", r"^SUBTOTAL", r"^TOTAL", r"^Importe",
        r"[A-Z]{5,}[0-9]{2,}"
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

    # Total robusto
    data["total"] = Decimal(str(extraer_total(texto))) if extraer_total(texto) is not None else None

    # ===== Productos =====
    i0, i1 = _find_section(lines, "CONCEPTOS", ["IMPORTE CON LETRA", "TOTAL"])
    if i0 is None:
        return data

    IVA_RE  = re.compile(r"002\s+IVA\s+Base\s*-\s*([0-9\.]+)\s+Tasa\s*-\s*(0\.\d+)\s+Importe\s*-\s*\$\s*([0-9,\.]+)")
    IEPS_RE = re.compile(r"003\s+IEPS\s+Base\s*-\s*([0-9\.]+)\s+Tasa\s*-\s*(0\.\d+)\s+Importe\s*-\s*\$\s*([0-9,\.]+)")

    i = i0 + 1
    while i < i1:
        ln = lines[i].strip()
        m_qty = re.match(r"^(\d+(?:\.\d{1,2})?)$", ln)
        if not m_qty:
            i += 1
            continue

        cantidad = _to_decimal(m_qty.group(1))
        if not cantidad or cantidad <= 0:
            i += 1
            continue

        # Nombre producto
        nombre = None
        if i + 2 < i1:
            posible_nombre = lines[i + 2].strip()
            nombre = posible_nombre

        if not nombre or not _es_producto_valido(nombre):
            i += 1
            continue

        # Buscar precio unitario base
        precio_unitario = None
        importe = None
        j = i
        limit = min(i + 16, i1)

        # 1) Precio Unitario explícito
        for k in range(j, limit):
            lnk = lines[k]
            if "Precio Unitario" in lnk:
                m_money = MONEY_RE.search(lnk)
                if m_money:
                    cand = _to_decimal(m_money.group(1))
                    if cand:
                        precio_unitario = cand
                        break

        # 2) Si no lo encontró: línea con solo $
        if precio_unitario is None:
            for k in range(j, limit):
                lnk = lines[k].strip()
                if "Importe -" in lnk or "IVA" in lnk or "IEPS" in lnk:
                    continue
                m_only = re.match(r"^\$\s*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]{2})|[0-9]+(?:\.[0-9]{2}))\s*$", lnk)
                if m_only:
                    precio_unitario = _to_decimal(m_only.group(1))
                    break

        # 3) Captura importe total de partida
        for k in range(j, limit):
            lnk = lines[k]
            if "Importe -" in lnk:
                m_imp = MONEY_RE.search(lnk)
                if m_imp:
                    importe = _to_decimal(m_imp.group(1))

        # 4) Fallback importe/cantidad
        if precio_unitario is None and importe:
            try:
                precio_unitario = (importe / cantidad).quantize(Decimal("0.01"))
            except (InvalidOperation, ZeroDivisionError):
                precio_unitario = None

        # ==== Calcular impuestos ====
        iva_total_line = Decimal("0.00")
        ieps_total_line = Decimal("0.00")
        iva_base = iva_tasa = ieps_base = ieps_tasa = None

        for k in range(j, limit):
            lnk = lines[k]
            m_iva = IVA_RE.search(lnk)
            if m_iva:
                iva_base = _to_decimal(m_iva.group(1))
                iva_tasa = _to_decimal(m_iva.group(2))
                iva_total_line = _to_decimal(m_iva.group(3)) or Decimal("0.00")
            m_ieps = IEPS_RE.search(lnk)
            if m_ieps:
                ieps_base = _to_decimal(m_ieps.group(1))
                ieps_tasa = _to_decimal(m_ieps.group(2))
                ieps_total_line = _to_decimal(m_ieps.group(3)) or Decimal("0.00")

        iva_per_unit = iva_total_line / cantidad if iva_total_line and cantidad > 0 else Decimal("0.00")
        ieps_per_unit = ieps_total_line / cantidad if ieps_total_line and cantidad > 0 else Decimal("0.00")

        if precio_unitario:
            precio_unitario_con_impuestos = (precio_unitario + iva_per_unit + ieps_per_unit).quantize(Decimal("0.01"))
        elif importe and cantidad > 0:
            base_unit = (importe / cantidad).quantize(Decimal("0.01"))
            precio_unitario_con_impuestos = (base_unit + iva_per_unit + ieps_per_unit).quantize(Decimal("0.01"))
        else:
            precio_unitario_con_impuestos = None

        print(f"[DEBUG Producto]")
        print(f"  Nombre: {nombre.strip()}")
        print(f"  Cantidad: {cantidad}")
        print(f"  Precio base: {precio_unitario}")
        print(f"  IVA por unidad: {iva_per_unit}")
        print(f"  IEPS por unidad: {ieps_per_unit}")
        print(f"  Precio final con impuestos: {precio_unitario_con_impuestos}")
        print(f"  Importe total producto: {precio_unitario_con_impuestos * cantidad}")
        print("--------------------------------------------------")

        if precio_unitario_con_impuestos and _es_producto_valido(nombre):
            data["productos"].append({
                "nombre": nombre.strip(),
                "cantidad": cantidad,
                "precio_unitario": precio_unitario_con_impuestos
            })

        i = j if j > i else i + 1

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
