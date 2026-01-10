class ExtractorBase:
    def __init__(self, text, pdf_path):
        self.text = text
        self.pdf_path = pdf_path

    def parse(self):
        raise NotImplementedError("Cada extractor debe implementar el método parse()")
