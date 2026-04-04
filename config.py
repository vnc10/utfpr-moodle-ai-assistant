import os

# Gemini AI
GEMINI_API_KEY = os.environ.get("GOOGLE_API_KEY")
GEMINI_MODEL = "gemini-2.5-flash-lite"
GEMINI_MODEL_PRO = "models/gemini-3.1-pro-preview"

# UTFPR Moodle
BASE_URL = "https://moodle.utfpr.edu.br"
LOGIN_URL = f"{BASE_URL}/login/token.php"
API_URL = f"{BASE_URL}/webservice/rest/server.php"

# Extensoes proibidas (binarios que a IA nao consegue ler)
FORBIDDEN_EXTENSIONS = ('.exe', '.o', '.out', '.bin', '.app', '.msi', '.pyc')

# Extensoes de codigo-fonte legiveis como texto
TEXT_CODE_EXTENSIONS = ('.c', '.cpp', '.txt', '.py', '.h', '.java', '.docx')

# Extensoes de midia que o Gemini aceita via upload
MEDIA_EXTENSIONS = ('.pdf', '.png', '.jpg', '.jpeg')

# Pastas do curso que contem material do professor (padrao)
TEACHER_FOLDERS_DEFAULT = ["Slides", "Atividades"]

# Mapeamento de pastas por disciplina (substring do nome -> pastas permitidas)
TEACHER_FOLDERS_BY_COURSE = {
    "redes de computadores": ["Bimestre"],
}

# Retry config para erros de quota do Gemini
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 30

# Google Drive OAuth
GOOGLE_CREDENTIALS_FILE = "credentials.json"
GOOGLE_TOKEN_FILE = "token.json"
GOOGLE_DRIVE_SCOPES = ["https://www.googleapis.com/auth/drive.file"]
