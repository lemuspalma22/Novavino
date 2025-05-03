import re
from datetime import datetime
from compras.models import Proveedor
from .extractor_base import ExtractorBase
from .utils_extractores import (
    extraer_folio,
    extraer_uuid,
    extraer_fecha_emision,
    extraer_total,
)


class ExtractorSecretosDeLaVid(ExtractorBase):
    def parse(self):
        proveedor, _ = Proveedor.objects.get_or_create(nombre="Secretos de la Vid S de RL de CV")

        folio = extraer_folio(self.text)
        uuid = extraer_uuid(self.text)
        fecha = extraer_fecha_emision(self.text)
        total = extraer_total(self.text)

        # Extraer productos
        productos = []
        producto_matches = re.findall(
            r"(\d+\.\d+)\s+[^\n]+\n([^\n]+)\s+\d{2}\.\d{2}\s+([\d,]+\.\d{2})",
            self.text
        )
        for cantidad, nombre_detectado, precio in producto_matches:
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
