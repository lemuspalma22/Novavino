import dotenv
dotenv.load_dotenv()
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

# 1. Autenticación
gauth = GoogleAuth()
gauth.LoadCredentialsFile("token.json")

if gauth.credentials is None:
    gauth.LocalWebserverAuth()  # Abre navegador para login la primera vez
elif gauth.access_token_expired:
    gauth.Refresh()
else:
    gauth.Authorize()

gauth.SaveCredentialsFile("token.json")

drive = GoogleDrive(gauth)

# 2. ID de carpeta de Google Drive
# Copia el ID de la URL: https://drive.google.com/drive/folders/**TU_ID**
FOLDER_ID = "1o9SkoeJ66qoBEbmyzXXhs1I67PQStTWV"  # 👈 Reemplaza esto

# 3. Buscar archivos PDF en la carpeta
query = f"'{FOLDER_ID}' in parents and mimeType='application/pdf' and trashed=false"
file_list = drive.ListFile({'q': query}).GetList()

print("\n📄 Archivos PDF encontrados:")
for file in file_list:
    print(f"- {file['title']} (ID: {file['id']})")
