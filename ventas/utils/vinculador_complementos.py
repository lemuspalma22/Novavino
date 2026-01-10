# ventas/utils/vinculador_complementos.py
from decimal import Decimal
from datetime import timedelta
from django.db import transaction
from ventas.models import Factura, PagoFactura, ComplementoPago, DocumentoRelacionado


class VinculadorComplementos:
    """
    Clase para vincular automáticamente ComplementoPago con PagoFactura existentes.
    Implementa lógica de matching con validación.
    """
    
    TOLERANCIA_MONTO = Decimal("0.01")  # Tolerancia de centavos
    TOLERANCIA_DIAS = 3  # ±3 días de diferencia permitida
    
    def __init__(self, complemento: ComplementoPago):
        self.complemento = complemento
        self.resultados = []
        self.errores = []
    
    def vincular_automaticamente(self) -> dict:
        """
        Intenta vincular automáticamente los documentos relacionados del complemento
        con los PagoFactura correspondientes.
        
        Returns:
            dict con:
            {
                "vinculados": int,
                "pendientes": int,
                "errores": list[str],
                "detalles": list[dict]
            }
        """
        with transaction.atomic():
            docs_relacionados = self.complemento.documentos_relacionados.all()
            
            if not docs_relacionados:
                return {
                    "vinculados": 0,
                    "pendientes": 0,
                    "errores": ["El complemento no tiene documentos relacionados"],
                    "detalles": []
                }
            
            vinculados = 0
            pendientes = 0
            detalles = []
            
            for doc_rel in docs_relacionados:
                resultado = self._vincular_documento(doc_rel)
                detalles.append(resultado)
                
                if resultado["vinculado"]:
                    vinculados += 1
                else:
                    pendientes += 1
            
            # Marcar complemento para revisión si hay pendientes
            if pendientes > 0:
                self.complemento.requiere_revision = True
                motivos = [d["motivo"] for d in detalles if not d["vinculado"]]
                self.complemento.motivo_revision = "\n".join(motivos)
                self.complemento.save(update_fields=["requiere_revision", "motivo_revision"])
            
            return {
                "vinculados": vinculados,
                "pendientes": pendientes,
                "errores": self.errores,
                "detalles": detalles
            }
    
    def _vincular_documento(self, doc_rel: DocumentoRelacionado) -> dict:
        """
        Intenta vincular un DocumentoRelacionado específico con un PagoFactura.
        
        Returns:
            dict con resultado del intento de vinculación
        """
        factura = doc_rel.factura
        monto = doc_rel.importe_pagado
        fecha_pago = self.complemento.fecha_pago
        
        # Buscar candidatos de PagoFactura sin vincular
        candidatos = self._buscar_candidatos(factura, monto, fecha_pago)
        
        if len(candidatos) == 0:
            return {
                "vinculado": False,
                "factura": factura.folio_factura,
                "monto": monto,
                "motivo": f"No se encontró PagoFactura para factura {factura.folio_factura} "
                         f"con monto ${monto} cerca de {fecha_pago}",
                "pago_id": None
            }
        
        if len(candidatos) == 1:
            # Match único - vincular automáticamente
            pago = candidatos[0]
            doc_rel.pago_factura = pago
            doc_rel.save(update_fields=["pago_factura"])
            
            return {
                "vinculado": True,
                "factura": factura.folio_factura,
                "monto": monto,
                "motivo": f"Vinculado automáticamente con PagoFactura #{pago.pk}",
                "pago_id": pago.pk
            }
        
        # Múltiples candidatos - requiere revisión manual
        return {
            "vinculado": False,
            "factura": factura.folio_factura,
            "monto": monto,
            "motivo": f"Hay {len(candidatos)} pagos similares para factura {factura.folio_factura}. "
                     f"Seleccionar manualmente entre: {', '.join([f'#{p.pk}' for p in candidatos])}",
            "pago_id": None
        }
    
    def _buscar_candidatos(self, factura: Factura, monto: Decimal, fecha_pago) -> list:
        """
        Busca PagoFactura candidatos que cumplan los criterios de matching.
        
        Criterios:
        - Misma factura
        - Monto similar (±TOLERANCIA_MONTO)
        - Fecha cercana (±TOLERANCIA_DIAS)
        - Sin complemento ya vinculado
        """
        fecha_min = fecha_pago - timedelta(days=self.TOLERANCIA_DIAS)
        fecha_max = fecha_pago + timedelta(days=self.TOLERANCIA_DIAS)
        
        monto_min = monto - self.TOLERANCIA_MONTO
        monto_max = monto + self.TOLERANCIA_MONTO
        
        candidatos = PagoFactura.objects.filter(
            factura=factura,
            monto__gte=monto_min,
            monto__lte=monto_max,
            fecha_pago__gte=fecha_min,
            fecha_pago__lte=fecha_max,
            documento_relacionado__isnull=True  # Sin complemento vinculado
        )
        
        return list(candidatos)


def vincular_complemento(complemento: ComplementoPago) -> dict:
    """
    Función de conveniencia para vincular un complemento.
    
    Usage:
        resultado = vincular_complemento(complemento)
        if resultado["pendientes"] > 0:
            print("Requiere revisión manual")
    """
    vinculador = VinculadorComplementos(complemento)
    return vinculador.vincular_automaticamente()
