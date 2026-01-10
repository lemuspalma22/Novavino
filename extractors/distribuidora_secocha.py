import re
from compras.models import Proveedor
from .extractor_base import ExtractorBase
from .utils_extractores import (
    extraer_uuid,
    extraer_fecha_emision,
    extraer_total,
)

class ExtractorDistribuidoraSecocha(ExtractorBase):
    def parse(self):
        proveedor, _ = Proveedor.objects.get_or_create(nombre="Distribuidora Secocha")

        # Folio: suele aparecer como “Folio:” con número cercano
                # Buscar folio tipo "Factura : FSA - 7085"
        folio_match = re.search(r"Factura\s*:\s*FSA\s*[-–]\s*(\d+)", self.text, re.IGNORECASE)
        if not folio_match:
            raise ValueError("❌ No se encontró el folio en la factura de Secocha.")
        folio = folio_match.group(1)

        uuid = extraer_uuid(self.text)
        fecha = extraer_fecha_emision(self.text)
        total = extraer_total(self.text)

        # Productos (ajustar si cambia formato)
        productos = []
        producto_matches = re.findall(
            r"\d{8}\s+H87\s+(\d{1,3}\.\d{2})\s+\d+\s+([^\n]+?)\s+\d+\s+\d+\s+(\d{1,3}\.\d{2})\s+([\d,]+\.\d{2})",
            self.text
        )

        for cantidad, nombre_detectado, precio_unitario, _ in producto_matches:
            productos.append({
                "nombre_detectado": nombre_detectado.strip(),
                "cantidad": float(cantidad),
                "precio_unitario": float(precio_unitario.replace(",", ""))
            })


        return {
            "uuid": uuid,
            "folio": folio,
            "fecha": fecha,
            "total": total,
            "proveedor": proveedor,
            "productos": productos
        }
