# extractors/vieja_bodega.py
import os
import re
from decimal import Decimal, InvalidOperation
from pdfminer.high_level import extract_text

VERSION = "VB-2025-11-12b"
DEBUG = os.getenv("NV_DEBUG") in {"1", "true", "True"}

def _D(x):
    try:
        return Decimal(str(x).replace(",", "").replace("$", "").strip())
    except (InvalidOperation, ValueError, TypeError):
        return None

class ExtractorViejaBodega:
    RFC = "VBM041202DD1"

    # Cantidad: SOLO enteros o .00 (30 | 30.00 | 1 | 1.00). Evita 269.86, 96.09, etc.
    _RE_QTY          = re.compile(r"^\d{1,4}(?:\.00)?$")
    _RE_MONEY_SIMPLE = re.compile(r"^\d{1,4}\.\d{2}$")                # 126.75
    _RE_MONEY_COMMA  = re.compile(r"^\d{1,3}(?:,\d{3})+\.\d{2}$")     # 4,857.48
    _RE_SAT_CLAVE    = re.compile(r"^\d{6,}$")                        # 50202203...
    _RE_H87          = re.compile(r"^H87$", re.I)

    _TAX_RATES = {Decimal("16.00"), Decimal("26.50")}  # tasas a ignorar en qty/tokens

    def __init__(self, text: str = None, pdf_path: str = None):
        """
        Inicializa el extractor.
        Args:
            text: Texto extraído del PDF (no se usa, se mantiene por compatibilidad)
            pdf_path: Ruta al archivo PDF
        """
        # Soportar ambas firmas: (pdf_path) y (text, pdf_path)
        if text is not None and pdf_path is None:
            # Llamada antigua: ExtractorViejaBodega(pdf_path)
            self.pdf_path = text
        else:
            # Llamada nueva: ExtractorViejaBodega(text, pdf_path)
            self.pdf_path = pdf_path

    def _find_header(self, lines, regexes, start=0):
        for i in range(start, len(lines)):
            if any(r.search(lines[i]) for r in regexes):
                return i
        return None

    def parse(self) -> dict:
        text = extract_text(self.pdf_path) or ""
        raw_lines = text.splitlines()
        lines = [re.sub(r"\s+", " ", l).strip() for l in raw_lines]
        lines = [l for l in lines if l]

        if DEBUG:
            print(f"[DEBUG] ExtractorViejaBodega VERSION={VERSION} FILE={__file__}")

        data = {"proveedor": "VIEJA BODEGA", "rfc_emisor": self.RFC, "conceptos": []}

        # --------- Encabezados ---------
        for i, l in enumerate(lines):
            if re.search(r"Folio\s+Inte\s*rno\s*:", l, re.I) or re.search(r"\bFolio\s*:", l, re.I):
                for j in range(i + 1, min(i + 6, len(lines))):
                    s = lines[j].strip()
                    if re.fullmatch(r"\d+", s):
                        data["folio"] = s
                        break
                break

        for l in lines:
            m = re.search(r"(20\d{2}-\d{2}-\d{2}|\d{2}/\d{2}/20\d{2})", l)
            if m:
                data["fecha_emision"] = m.group(1)
                break

        for l in lines:
            m = re.search(r"[A-F0-9]{8}-[A-F0-9]{4}-[A-F0-9]{4}-[A-F0-9]{4}-[A-F0-9]{12}", l, re.I)
            if m:
                data["uuid"] = m.group(0)
                break

        for i, l in enumerate(lines):
            if re.search(r"\bSubtotal\b", l, re.I):
                for j in range(i + 1, min(i + 3, len(lines))):
                    m = re.search(r"([0-9,]+\.\d{2})", lines[j]); 
                    if m: data["subtotal"] = _D(m.group(1)); break
                break

        for i, l in enumerate(lines):
            if re.search(r"\bIVA\b", l, re.I):
                for j in range(i + 1, min(i + 3, len(lines))):
                    m = re.search(r"([0-9,]+\.\d{2})", lines[j]); 
                    if m: data["iva"] = _D(m.group(1)); break
                break

        last_total = None
        for i, l in enumerate(lines):
            if re.search(r"\bTOTAL\b", l, re.I):
                for j in range(i + 1, min(i + 3, len(lines))):
                    m = re.search(r"([0-9,]+\.\d{2})", lines[j]); 
                    if m: last_total = _D(m.group(1))
        if last_total is not None:
            data["total"] = last_total

        # --------- Zona de ítems ---------
        desc_headers = [re.compile(r"\bDescripci[oó]n\b", re.I),
                        re.compile(r"\bDESCRIPCION\b", re.I),
                        re.compile(r"\bCantidad\b", re.I)]
        pu_headers   = [re.compile(r"\bP\s*/\s*U\b", re.I),
                        re.compile(r"\bP\.\s*U\.\b", re.I),
                        re.compile(r"\bPU\b", re.I),
                        re.compile(r"\bPrecio\s*Unitario\b", re.I)]
        idx_desc = self._find_header(lines, desc_headers, 0)
        idx_pu   = self._find_header(lines, pu_headers, (idx_desc or 0) + 1)
        if idx_pu is None:
            idx_pu_alt = self._find_header(lines, [re.compile(r"\bImporte\s*Base\b", re.I)], (idx_desc or 0) + 1)
            if idx_pu_alt is not None:
                idx_pu = idx_pu_alt

        end_markers = [re.compile(r"\bSubtotal\b", re.I),
                       re.compile(r"\bTOTAL\b", re.I),
                       re.compile(r"Sello\s*digital", re.I),
                       re.compile(r"IM\s*PORTE\s*EN\s*LETRA", re.I)]
        ends = [self._find_header(lines, [m], (idx_desc or 0) + 1) for m in end_markers]
        ends = [e for e in ends if e is not None]
        end_idx = min(ends) if ends else len(lines)

        if DEBUG:
            print(f"[DEBUG] idx_desc={idx_desc} idx_pu={idx_pu} end_idx={end_idx}")

        def build_region_prepu():
            if idx_pu is not None:
                if idx_desc is not None and idx_pu > idx_desc:
                    return lines[idx_desc + 1: idx_pu]
                return lines[max(0, idx_pu - 30): idx_pu]
            return lines[(idx_desc or 0) + 1: end_idx]

        region_prepu = build_region_prepu()
        if DEBUG:
            print(f"[DEBUG] region_prepu_len={len(region_prepu)} (primeras 20):")
            for l in region_prepu[:20]: print("   ", l)

        header_stop = re.compile(
            r"^(P\s*/\s*U|P\.\s*U\.|PU|Precio\s*Unitario"
            r"|Importe$|^Base$|^Tasa$|^I\.?E\.?P\.?S\.?$|^I\.?V\.?A\.?$"
            r"|Importe\s*Base|Importe\s+I\.?E\.?P\.?S|Importe\s+I\.?V\.?A)",
            re.I,
        )

        def is_qty_str(s):
            if not self._RE_QTY.match(s): 
                return False
            q = _D(s if "." in s else f"{s}.00")
            return q is not None and q not in self._TAX_RATES

        # --- Modo A: “columnar zip” (pre-P/U): qty list + (clave → desc) list ---
        items, qtys, descs = [], [], []
        i = 0
        while i < len(region_prepu):
            s = region_prepu[i].strip()

            # cantidades válidas (solo enteros o .00; sin 16.00/26.50)
            if is_qty_str(s):
                q = _D(s if "." in s else f"{s}.00")
                qtys.append(q)
                i += 1
                continue

            # clave SAT seguida de la línea de descripción
            if self._RE_SAT_CLAVE.match(s) and (i + 1) < len(region_prepu):
                d = region_prepu[i + 1].strip()
                # corta si la “descripción” es header o dinero o qty
                if (not header_stop.match(d)
                    and not self._RE_MONEY_SIMPLE.match(d)
                    and not self._RE_MONEY_COMMA.match(d)
                    and not self._RE_QTY.match(d)):
                    descs.append(d)
                    i += 2
                    continue

            i += 1

        n = min(len(qtys), len(descs))
        for k in range(n):
            items.append({"cantidad": qtys[k], "h87": False, "clave": None, "descripcion": descs[k]})

        # --- Fallback pre-P/U (una sola línea de desc después de qty) ---
        if not items:
            k = 0
            while k < len(region_prepu):
                s = region_prepu[k].strip()
                if is_qty_str(s):
                    q = _D(s if "." in s else f"{s}.00")
                    k += 1
                    # opcional H87 / clave
                    if k < len(region_prepu) and self._RE_H87.match(region_prepu[k]): k += 1
                    if k < len(region_prepu) and self._RE_SAT_CLAVE.match(region_prepu[k]): k += 1
                    # toma UNA línea de descripción válida
                    desc = ""
                    while k < len(region_prepu):
                        nxt = region_prepu[k].strip()
                        if (not nxt): k += 1; continue
                        if (self._RE_QTY.match(nxt) or self._RE_H87.match(nxt)
                            or self._RE_SAT_CLAVE.match(nxt) or header_stop.match(nxt)
                            or self._RE_MONEY_SIMPLE.match(nxt) or self._RE_MONEY_COMMA.match(nxt)):
                            break
                        desc = nxt; k += 1; break
                    items.append({"cantidad": q, "h87": False, "clave": None, "descripcion": desc})
                    continue
                k += 1

        # --- Plan C: post-P/U (solo si sigue vacío) ---
        if not items and idx_pu is not None:
            region_post = lines[idx_pu + 1: min(end_idx, idx_pu + 80)]
            # igual que Modo A pero post-P/U
            qtys, descs = [], []
            i = 0
            while i < len(region_post):
                s = region_post[i].strip()
                if is_qty_str(s):
                    q = _D(s if "." in s else f"{s}.00"); qtys.append(q); i += 1; continue
                if self._RE_SAT_CLAVE.match(s) and (i + 1) < len(region_post):
                    d = region_post[i + 1].strip()
                    if (not header_stop.match(d)
                        and not self._RE_MONEY_SIMPLE.match(d)
                        and not self._RE_MONEY_COMMA.match(d)
                        and not self._RE_QTY.match(d)):
                        descs.append(d); i += 2; continue
                i += 1
            n = min(len(qtys), len(descs))
            for k in range(n):
                items.append({"cantidad": qtys[k], "h87": False, "clave": None, "descripcion": descs[k]})

        if DEBUG:
            print(f"[DEBUG] items={len(items)}")
            for it in items:
                print("   [item]", it)

        # --------- Tokens P/U e Importe (post-P/U) ---------
        scan_from = (idx_pu + 1) if idx_pu is not None else (idx_desc or 0)
        window = lines[scan_from: end_idx]
        tokens = []
        for st in ((l or "").strip() for l in window):
            if not st: 
                continue
            if self._RE_MONEY_COMMA.match(st) or self._RE_MONEY_SIMPLE.match(st):
                val = _D(st)
                if val is not None and val not in self._TAX_RATES:
                    tokens.append((val, bool(self._RE_MONEY_COMMA.match(st))))

        # Nunca cantidades como tokens
        qty_set = {it.get("cantidad") for it in items if it.get("cantidad") is not None}
        tokens = [(v, hasc) for (v, hasc) in tokens if v not in qty_set]

        if DEBUG:
            print(f"[DEBUG] tokens={len(tokens)}  sample={tokens[:12]}")

        pu_cands   = [(i, v) for i, (v, hasc) in enumerate(tokens) if (not hasc) and v < Decimal("1000")]
        imp_cands0 = [(i, v, hasc) for i, (v, hasc) in enumerate(tokens) if hasc or v >= Decimal("1000")]

        pu_ptr = imp_ptr = 0
        pu_vals, imp_vals = [], []

        for it in items:
            q = it.get("cantidad") or Decimal("1")
            imp_cands = list(imp_cands0)
            # Para cantidades pequeñas o medianas, incluir valores intermedios como candidatos de importe
            # Esto captura importes que son < 1000 y sin coma (ej: 576.54)
            if q <= Decimal("20"):  # Ampliado de 3 a 20 para cubrir más casos
                # Candidatos adicionales: valores sin coma entre 100 y 5000
                extra = [(i, v, False) for i, (v, hasc) in enumerate(tokens) 
                         if (not hasc) and Decimal("100") <= v < Decimal("5000")]
                seen = {i for (i, _, _) in imp_cands}
                for i, v, hasc in extra:
                    if i not in seen: imp_cands.append((i, v, hasc))

            best = None
            # Buscar en ventana de P/U
            for i in range(pu_ptr, min(pu_ptr + 8, len(pu_cands))):
                _, pu_v = pu_cands[i]
                if pu_v >= Decimal("5000"): 
                    continue
                # Buscar en TODA la lista de importes (no solo desde imp_ptr)
                # porque imp_cands cambia con los candidatos extras
                for j in range(len(imp_cands)):
                    _, imp_v, _ = imp_cands[j]
                    rel = abs((pu_v * q) - imp_v) / (imp_v if imp_v else Decimal("1"))
                    if rel <= Decimal("0.05"):
                        cand = (rel, i, j, pu_v, imp_v)
                        if best is None or cand < best: best = cand

            if best:
                _, i, j, pu_v, imp_v = best
                pu_vals.append(pu_v); imp_vals.append(imp_v)
                pu_ptr = i + 1
                # Solo actualizar imp_ptr si el match está en los candidatos originales
                if j < len(imp_cands0):
                    imp_ptr = j + 1
            else:
                if imp_ptr < len(imp_cands):
                    imp_v = imp_cands[imp_ptr][1]
                    pu_v = (imp_v / q).quantize(Decimal("0.01"))
                    pu_vals.append(pu_v); imp_vals.append(imp_v); imp_ptr += 1
                elif pu_ptr < len(pu_cands):
                    pu_v = pu_cands[pu_ptr][1]
                    imp_v = (pu_v * q).quantize(Decimal("0.01"))
                    pu_vals.append(pu_v); imp_vals.append(imp_v); pu_ptr += 1
                else:
                    pu_vals.append(None); imp_vals.append(None)

        conceptos = []
        for idx, it in enumerate(items):
            desc = (it.get("descripcion") or "").strip()
            if not desc: 
                continue
            q = it["cantidad"]
            pu = pu_vals[idx] if idx < len(pu_vals) else None
            imp = imp_vals[idx] if idx < len(imp_vals) else None
            if pu is None or imp is None: 
                continue
            rel = abs((pu * q) - imp) / (imp if imp else Decimal("1"))
            if rel <= Decimal("0.05"):
                conceptos.append({
                    "descripcion": desc,
                    "cantidad": q,
                    "precio_unitario": pu.quantize(Decimal("0.01")),
                    "importe": imp.quantize(Decimal("0.01")),
                })

        if conceptos:
            data["conceptos"] = conceptos
        return data
