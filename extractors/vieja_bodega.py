import re
from compras.models import Proveedor
from .extractor_base import ExtractorBase
from .utils_extractores import (
    extraer_uuid,
    extraer_fecha_emision,
    extraer_total,
)

class ExtractorViejaBodega(ExtractorBase):
    def parse(self):
        proveedor, _ = Proveedor.objects.get_or_create(nombre="Vieja Bodega de México")

        # Extraer folio
        folio_match = re.search(r"Folio Interno:\s*(\d+)", self.text)
        if not folio_match:
            raise ValueError("❌ No se encontró 'Folio Interno:' en el texto OCR.")
        folio = folio_match.group(1)

        # Extraer campos comunes
        uuid = extraer_uuid(self.text)
        fecha = extraer_fecha_emision(self.text)
        total = extraer_total(self.text)

        # Extraer productos
        productos = []
        producto_matches = re.findall(
            r"(\d{1,3}\.\d{2})\s+V\.T\.\s+(.*?)\s+\d{1,3}\.\d{2}\s+([\d,]+\.\d{2})",
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
