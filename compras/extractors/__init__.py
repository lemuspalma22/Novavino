# compras/extractors/__init__.py

# Bridge para extractores por proveedor: intenta primero importar el extractor
# desde 'compras.extractors' (si algún día lo mueves ahí), y si no, usa el que
# ya tienes en 'Project/extractors'.
extract_vieja_bodega = None

# 1) Si existe en esta app (compras/extractors/vieja_bodega.py)
try:
    from .vieja_bodega import extract_vieja_bodega as _fn
    extract_vieja_bodega = _fn
except Exception:
    pass

# 2) Si existe como clase en Project/extractors/vieja_bodega.py
if extract_vieja_bodega is None:
    try:
        from extractors.vieja_bodega import ExtractorViejaBodega
        def extract_vieja_bodega(pdf_path: str) -> dict:
            return ExtractorViejaBodega(pdf_path).parse()
    except Exception:
        extract_vieja_bodega = None
