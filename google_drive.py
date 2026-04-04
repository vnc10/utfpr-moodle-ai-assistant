import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from config import GOOGLE_CREDENTIALS_FILE, GOOGLE_TOKEN_FILE, GOOGLE_DRIVE_SCOPES


def _get_credentials():
    """Obtém credenciais OAuth2, abrindo o navegador se necessário."""
    creds = None

    if os.path.exists(GOOGLE_TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(GOOGLE_TOKEN_FILE, GOOGLE_DRIVE_SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(GOOGLE_CREDENTIALS_FILE, GOOGLE_DRIVE_SCOPES)
            creds = flow.run_local_server(port=0)

        with open(GOOGLE_TOKEN_FILE, "w") as token:
            token.write(creds.to_json())

    return creds


def upload_to_google_docs(filepath):
    """Faz upload de um .docx para o Google Drive convertendo para Google Docs.
    Retorna a URL do documento criado."""
    creds = _get_credentials()
    service = build("drive", "v3", credentials=creds)

    file_metadata = {
        "name": os.path.splitext(os.path.basename(filepath))[0],
        "mimeType": "application/vnd.google-apps.document",
    }

    media = MediaFileUpload(
        filepath,
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )

    file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields="id, webViewLink",
    ).execute()

    return file.get("webViewLink")
