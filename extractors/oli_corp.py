import re
from compras.models import Proveedor
from .extractor_base import ExtractorBase
from .utils_extractores import (
    extraer_uuid,
    extraer_fecha_emision,
    extraer_total,
)

class ExtractorOliCorp(ExtractorBase):
    def parse(self):
        proveedor, _ = Proveedor.objects.get_or_create(nombre="OLI Corp")

                # Buscar "Folio" en línea y número debajo (puede estar hasta 5 líneas abajo)
        lines = self.text.splitlines()
        folio = None
        for i, line in enumerate(lines):
            if re.fullmatch(r"Folio", line.strip(), re.IGNORECASE):
                for offset in range(1, 6):  # busca en las siguientes 5 líneas
                    if i + offset < len(lines):
                        candidate = lines[i + offset].strip()
                        if re.fullmatch(r"\d{1,6}", candidate):
                            folio = candidate
                            break
                break
        if not folio:
            raise ValueError("❌ No se encontró el folio en la factura de OLI Corp.")


        uuid = extraer_uuid(self.text)
        fecha = extraer_fecha_emision(self.text)
        total = extraer_total(self.text)

        productos = []
        producto_matches = re.findall(
            r"\d{8}\s+\d{2}\s+([^\n]+?)\s+(\d{1,3}\.\d{1,2})\s+H87-[^\s]+\s+\$\s*([\d,]+\.\d{2})",
            self.text
        )

        for nombre_detectado, cantidad, precio in producto_matches:
            productos.append({
                "nombre_detectado": nombre_detectado.strip(),
                "cantidad": float(cantidad),
                "precio_unitario": float(precio.replace(",", ""))
            })

        return {
            "uuid": uuid,
            "folio": folio,
            "fecha": fecha,
            "total": total,
            "proveedor": proveedor,
            "productos": productos
        }
