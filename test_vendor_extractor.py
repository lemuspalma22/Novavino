from process_drive_invoices import try_vendor_extractors

pdf = r"VBM041202DD1FB24468.pdf"
data = try_vendor_extractors(pdf)

print("Extractor retornó:", "None" if not data else "OK")
if data:
    print("Proveedor:", data.get("proveedor"))
    print("Folio:", data.get("folio"))
    print("UUID:", data.get("uuid"))
    print("Total:", data.get("total"))
    conceptos = data.get("conceptos") or []
    print("Conceptos:", len(conceptos))
    for i, c in enumerate(conceptos, 1):
        print(f"{i:02d}. {c.get('descripcion')} | Cant: {c.get('cantidad')} | PU: {c.get('precio_unitario')} | Importe: {c.get('importe')}")