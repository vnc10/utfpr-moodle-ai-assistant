import mimetypes
import os
import sys
import time

try:
    from google import genai
    from google.genai import types
except ImportError:
    print("A biblioteca google-genai nao esta instalada.")
    print("Execute: pip install google-genai")
    sys.exit(1)

from config import (
    GEMINI_API_KEY,
    GEMINI_MODEL,
    TEACHER_FOLDERS_DEFAULT,
    TEACHER_FOLDERS_BY_COURSE,
    TEXT_CODE_EXTENSIONS,
    MEDIA_EXTENSIONS,
    MAX_RETRIES,
    RETRY_DELAY_SECONDS,
)

client = genai.Client(api_key=GEMINI_API_KEY)


def upload_file(filepath):
    """Faz upload de um arquivo para o Gemini e aguarda processamento."""
    mime_type = mimetypes.guess_type(filepath)[0] or "application/octet-stream"
    with open(filepath, "rb") as f:
        g_file = client.files.upload(
            file=f,
            config=types.UploadFileConfig(
                display_name=os.path.basename(filepath),
                mime_type=mime_type,
            ),
        )
    while g_file.state.name == "PROCESSING":
        time.sleep(2)
        g_file = client.files.get(name=g_file.name)
    return g_file


def delete_files(file_list):
    """Remove uma lista de arquivos da nuvem do Gemini."""
    for g_file in file_list:
        try:
            client.files.delete(name=g_file.name)
        except Exception:
            pass


def _get_teacher_folders(course_name):
    """Retorna as pastas permitidas para contexto com base na disciplina."""
    name_lower = course_name.lower()
    for keyword, folders in TEACHER_FOLDERS_BY_COURSE.items():
        if keyword in name_lower:
            return folders
    return TEACHER_FOLDERS_DEFAULT


def load_teacher_context(course_name):
    """Faz upload dos PDFs do professor (slides/atividades) como contexto."""
    context_files = []
    allowed_folders = _get_teacher_folders(course_name)
    print(f"\n[AI CONTEXT] Scanning '{course_name}' for teacher PDFs...")
    print(f"   Folders filter: {allowed_folders}")

    for root, dirs, files in os.walk(course_name):
        if "Submissions_" in root:
            continue

        folder_name = os.path.basename(root)
        is_allowed = any(name in folder_name for name in allowed_folders)
        if not is_allowed and folder_name != course_name:
            continue

        for f in files:
            if not f.lower().endswith(".pdf"):
                continue
            filepath = os.path.join(root, f)
            print(f"   -> Uploading {f} to Gemini...")
            try:
                context_files.append(upload_file(filepath))
            except Exception as e:
                print(f"      [WARNING] Could not upload {f}: {e}")

    print(f"Context loaded: {len(context_files)} files uploaded.")
    return context_files


def read_student_files(student_dir):
    """Le os arquivos do aluno e retorna texto e uploads para o Gemini."""
    student_text = ""
    uploaded_files = []

    for root, dirs, files in os.walk(student_dir):
        for filename in files:
            filepath = os.path.join(root, filename)
            ext = filename.lower()

            if any(ext.endswith(e) for e in TEXT_CODE_EXTENSIONS):
                try:
                    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                        student_text += f"\nFILE: {filename}\n{f.read()}\n"
                except Exception:
                    pass

            elif any(ext.endswith(e) for e in MEDIA_EXTENSIONS):
                print(f"      [UPLOADING TO GEMINI] {filename}...")
                try:
                    uploaded_files.append(upload_file(filepath))
                except Exception as e:
                    print(f"      [WARNING] Could not upload {filename}: {e}")

    return student_text, uploaded_files


def _get_course_context(course_name):
    """Retorna a descricao do publico-alvo com base no nome da disciplina."""
    name_lower = course_name.lower()
    if "redes de computadores" in name_lower:
        return (
            "para alunos do curso Tecnico em Informatica integrado ao Ensino Medio"
        )
    if "estrutura de dados" in name_lower or "programação estruturada" in name_lower:
        return (
            "para alunos do curso superior de Engenharia Eletronica"
        )
    if "informática" in name_lower and "alimentos" in name_lower:
        return (
            "para alunos do curso superior Tecnico em Alimentos"
        )
    return "para alunos universitarios"


def generate_feedback(course_name, assignment_desc, student_text, student_files, context_files):
    """Gera feedback via Gemini com retry automatico para erros de quota."""
    public = _get_course_context(course_name)

    system_instruction = (
        f"Você é um professor universitário formado em Ciência da Computação "
        f"lecionando a disciplina de '{course_name}' {public}.\n"
        f"A NOTA DO ALUNO SERÁ SEMPRE 10, independentemente da qualidade da entrega.\n"
        f"Sua função é gerar um feedback amigável, educado e construtivo em português.\n"
        f"Utilize os PDFs de contexto fornecidos para manter a terminologia usada em sala de aula.\n\n"
        f"ATENÇÃO - REGRAS ESTRITAS DE FORMATAÇÃO:\n"
        f"1. A resposta DEVE ser escrita INTEIRAMENTE em HTML.\n"
        f"2. É ESTRITAMENTE PROIBIDO o uso de Markdown. NÃO use asteriscos (**) para negrito, use a tag <strong>. NÃO use hifens ou asteriscos (*) para listas, use <ul> e <li>.\n"
        f"3. Use a tag <br> ou <p> para quebras de linha.\n"
        f"4. NÃO envolva a resposta em blocos de código (como ```html), retorne o HTML diretamente.\n\n"
        f"Por fim, não cite nomes próprios. Ao se identificar no final do feedback, assine apenas como 'Professor'."
    )

    prompt = f"ENUNCIADO DA TAREFA:\n{assignment_desc}\n\nCONTEUDO DO ALUNO:\n{student_text}"
    contents = [prompt] + context_files + student_files

    for attempt in range(MAX_RETRIES):
        try:
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.2,
                ),
            )

            feedback = response.text.replace("```html", "").replace("```", "").strip()
            feedback += (
                "<br><br><hr><p><em>* Este feedback foi gerado automaticamente "
                "por IA com base no material da disciplina.</em></p>"
            )
            return feedback

        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                print(
                    f"      [QUOTA EXCEEDED] Tentativa {attempt + 1}/{MAX_RETRIES}. "
                    f"Esperando {RETRY_DELAY_SECONDS}s..."
                )
                time.sleep(RETRY_DELAY_SECONDS)
            else:
                print(f"      [AI ERROR] Failed to generate feedback: {e}")
                break

    return None


def generate_lesson_plan(course_name, sections, context_files):
    """Generates a lesson plan via Gemini based on the course structure and materials."""
    public = _get_course_context(course_name)

    system_instruction = (
        f"Voce e um professor universitario formado em Ciencia da Computacao "
        f"lecionando a disciplina de '{course_name}' {public}.\n"
        f"Sua funcao e gerar um roteiro de aula detalhado e bem estruturado em portugues.\n"
        f"Utilize os PDFs de contexto fornecidos para manter a terminologia usada em sala de aula.\n"
        f"O roteiro deve incluir: objetivos da aula, topicos a serem abordados, "
        f"metodologia sugerida, atividades praticas e referencias.\n"
        f"Gere a resposta APENAS usando HTML simples (<h1>, <h2>, <p>, <ul>, <li>, <strong>, <br>, <hr>).\n"
        f"NAO use blocos de codigo Markdown.\n"
        f"Alem disso meu nome e Vinicius Petris, se for citar o nome do professor no roteiro."
    )

    course_structure = ""
    for section in sections:
        course_structure += f"\nSECAO: {section['name']}\n"
        for mod in section['modules']:
            course_structure += f"  - {mod}\n"

    prompt = f"ESTRUTURA DO CURSO:\n{course_structure}\n\nGere um roteiro de aula completo para esta disciplina."
    contents = [prompt] + context_files

    for attempt in range(MAX_RETRIES):
        try:
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.4,
                ),
            )

            return response.text.replace("```html", "").replace("```", "").strip()

        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                print(
                    f"      [QUOTA EXCEEDED] Attempt {attempt + 1}/{MAX_RETRIES}. "
                    f"Waiting {RETRY_DELAY_SECONDS}s..."
                )
                time.sleep(RETRY_DELAY_SECONDS)
            else:
                print(f"      [AI ERROR] Failed to generate lesson plan: {e}")
                break

    return None
