import os
import tempfile
import django

from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "crm_project.settings")
django.setup()

from compras.models import Compra, CompraProducto
from inventario.models import Producto, AliasProducto, ProductoNoReconocido
from factura_parser import extract_invoice_data

# === CONFIGURACIÓN ===
FOLDER_ID = '1o9SkoeJ66qoBEbmyzXXhs1I67PQStTWV'
PROCESADOS_FOLDER_ID = None  # O usa el ID de tu carpeta 'procesados' si deseas moverlos

# === AUTENTICACIÓN GOOGLE DRIVE ===
def get_drive():
    gauth = GoogleAuth("settings.yaml")
    gauth.LoadCredentialsFile("token.json")
    if gauth.credentials is None:
        gauth.LocalWebserverAuth()
    elif gauth.access_token_expired:
        gauth.Refresh()
    else:
        gauth.Authorize()
    gauth.SaveCredentialsFile("token.json")
    return GoogleDrive(gauth)

# === VERIFICAR SI YA FUE PROCESADO ===
def is_processed(uuid):
    return Compra.objects.filter(uuid=uuid).exists()

# === RESOLVER PRODUCTO CON ALIAS Y FALLBACK ===
def get_or_register_producto(nombre_detectado):
    try:
        return Producto.objects.get(nombre=nombre_detectado)
    except Producto.DoesNotExist:
        pass
    try:
        alias = AliasProducto.objects.get(alias__iexact=nombre_detectado)
        return alias.producto
    except AliasProducto.DoesNotExist:
        pass
    if not ProductoNoReconocido.objects.filter(nombre_detectado=nombre_detectado).exists():
        ProductoNoReconocido.objects.create(nombre_detectado=nombre_detectado)
        print(f"🟡 Producto no reconocido registrado: {nombre_detectado}")
    else:
        print(f"🟡 Ya registrado como no reconocido: {nombre_detectado}")
    return None

# === PROCESAR ARCHIVO PDF ===
def process_pdf_file(file, temp_path):
    file.GetContentFile(temp_path)

    try:
        data = extract_invoice_data(temp_path)

        # Validar que UUID exista antes de verificar duplicado
        uuid = file['id']
        data['uuid'] = uuid

        # Asegurar que folio y fecha estén presentes
        if not data.get("folio"):
            raise ValueError("❌ No se encontró el folio en la factura.")
        if not data.get("fecha"):
            raise ValueError("❌ No se encontró la fecha en la factura.")

        if is_processed(uuid):
            print(f"⏩ Ya procesado: {file['title']}")
            return False

        # Crear la compra
        compra = Compra.objects.create(**{k: v for k, v in data.items() if k != 'productos'})

        for prod in data.get('productos', []):
            producto = get_or_register_producto(prod['nombre_detectado'])
            if producto:
                CompraProducto.objects.create(
                    compra=compra,
                    producto=producto,
                    cantidad=prod['cantidad'],
                    precio_unitario=prod['precio_unitario'],
                    detectado_como=prod['nombre_detectado']
                )

        print(f"✅ Procesado: {file['title']}")
        return True

    except Exception as e:
        print(f"❌ Error procesando {file['title']}: {e}")
        return False


# === MOVER A CARPETA PROCESADOS (opcional) ===
def move_to_processed_folder(file):
    file['parents'] = [{'id': PROCESADOS_FOLDER_ID}]
    file.Upload()

# === FLUJO PRINCIPAL ===
def main():
    drive = get_drive()
    archivos = drive.ListFile({
        'q': f"'{FOLDER_ID}' in parents and mimeType='application/pdf' and trashed=false"
    }).GetList()

    total = len(archivos)
    procesados = 0
    ignorados = 0

    for archivo in archivos:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
            exito = process_pdf_file(archivo, tmp.name)

        if exito:
            procesados += 1
            if PROCESADOS_FOLDER_ID:
                move_to_processed_folder(archivo)
        else:
            ignorados += 1

    print("\n📊 Resumen:")
    print(f"📄 Archivos revisados: {total}")
    print(f"📦 Nuevas compras registradas: {procesados}")
    print(f"⏩ Ya procesadas anteriormente: {ignorados}")

if __name__ == "__main__":
    main()
