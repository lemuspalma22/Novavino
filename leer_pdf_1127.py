import pdfplumber

pdf_path = "LEPR970522CD0_Factura_1127_E9DA14FE-E047-465F-A7B0-314647B8D87C.pdf"

with pdfplumber.open(pdf_path) as pdf:
    for page_num, page in enumerate(pdf.pages, 1):
        print(f"=== PÁGINA {page_num} ===")
        text = page.extract_text()
        print(text)
        print("\n" + "="*80 + "\n")
