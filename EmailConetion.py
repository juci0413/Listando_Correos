import os
import imaplib
import email
from email.header import decode_header
import base64
from dotenv import load_dotenv
import google.auth
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

# Obtener las credenciales de las variables de entorno
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')

# Si modificas estos SCOPES, elimina el archivo token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def authenticate_gmail():
    creds = None
    # El archivo token.json almacena los tokens de acceso y actualización del usuario,
    # y se crea automáticamente cuando el flujo de autorización se completa por primera vez.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # Si no hay credenciales (válidas) disponibles, permite que el usuario inicie sesión.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Guarda las credenciales para la próxima ejecución
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

def fetch_emails():
    creds = authenticate_gmail()
    service = build('gmail', 'v1', credentials=creds)
    
    # Llama a la API de Gmail
    results = service.users().messages().list(userId='me', labelIds=['INBOX'], q='is:unread').execute()
    messages = results.get('messages', [])
    
    if not messages:
        print('No hay mensajes nuevos.')
    else:
        for message in messages:
            msg = service.users().messages().get(userId='me', id=message['id']).execute()
            payload = msg.get('payload', {})
            headers = payload.get('headers', [])
            
            for header in headers:
                name = header.get('name')
                value = header.get('value')
                if name.lower() in ['from', 'to', 'subject', 'date']:
                    print(f'{name}: {value}')
            
            parts = payload.get('parts', [])
            for part in parts:
                mime_type = part.get('mimeType')
                if mime_type == 'text/plain':
                    body = part.get('body', {}).get('data')
                    if body:
                        decoded_body = base64.urlsafe_b64decode(body).decode('utf-8')
                        print(f'Cuerpo: {decoded_body}')

fetch_emails()
