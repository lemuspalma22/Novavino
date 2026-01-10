import dotenv
dotenv.load_dotenv()
from compras.extractors.pdf_reader import extract_text_from_pdf
from extractors.secretos_delavid import ExtractorSecretosDeLaVid
from extractors.vieja_bodega import ExtractorViejaBodega
from extractors.distribuidora_secocha import ExtractorDistribuidoraSecocha
from extractors.oli_corp import ExtractorOliCorp
from extractors.extractor_base import ExtractorBase



def extract_invoice_data(pdf_path):
    text = extract_text_from_pdf(pdf_path)

    # Despachador por RFC o nombre clave
    if "SVI180726AHA" in text or "SECRETOS DE LA VID" in text:
        extractor = ExtractorSecretosDeLaVid(text, pdf_path)
    elif "VBM041202DD1" in text or "VIEJA BODEGA" in text:
        extractor = ExtractorViejaBodega(text, pdf_path)
    elif "DSE190423J82" in text or "DISTRIBUIDORA SECOCHA" in text:
        extractor = ExtractorDistribuidoraSecocha(text, pdf_path)
    elif "CDO200903RR1" in text or "OLI CORP" in text:
        extractor = ExtractorOliCorp(text, pdf_path)
    else:
        # Mensaje claro indicando que debe registrarse manualmente
        raise ValueError(
            "Esta factura no pertenece a ningún proveedor con extractor automático. "
            "Proveedores soportados: Secretos de la Vid, Vieja Bodega, Distribuidora Secocha, Oli Corp. "
            "Por favor, registra esta factura manualmente desde el admin de Compras."
        )

    return extractor.parse()
