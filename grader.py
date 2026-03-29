import os

from downloader import download_submission_file
from gemini_ai import read_student_files, generate_feedback, delete_files
from moodle_api import get_submissions, post_grade


def _should_skip_submission(submission):
    """Verifica se a submissao deve ser pulada."""
    if submission.get("status") != "submitted":
        return True
    user_id = submission.get("userid")
    if submission.get("gradingstatus") == "graded" and str(user_id):
        print(f"   [SKIPPED] User {user_id} already graded.")
        return True
    return False


def _download_all_submission_files(submission, token, student_dir):
    """Baixa todos os arquivos validos de uma submissao. Retorna True se algum e valido."""
    has_valid_files = False
    user_id = submission.get("userid")

    for plugin in submission.get("plugins", []):
        if plugin.get("type") != "file":
            continue
        for filearea in plugin.get("fileareas", []):
            for file_info in filearea.get("files", []):
                if download_submission_file(file_info, token, student_dir):
                    has_valid_files = True
                else:
                    filename = file_info.get("filename", "?")
                    if filename != ".":
                        print(f"   [SKIPPED BINARY] User {user_id} -> {filename}")

    return has_valid_files


def _evaluate_and_grade(token, assignment_id, user_id, student_dir, assignment_desc, course_name, context_files):
    """Avalia a submissao com IA e envia nota para o Moodle."""
    student_text, student_uploads = read_student_files(student_dir)

    if not student_text.strip() and not student_uploads:
        return

    print(f"   [AI EVALUATION] Analyzing User {user_id}...")
    feedback = generate_feedback(course_name, assignment_desc, student_text, student_uploads, context_files)

    if feedback:
        print(f"   [MOODLE POST] Sending Grade (10) for User {user_id}...")
        post_grade(token, assignment_id, user_id, feedback, grade=100.0)

    delete_files(student_uploads)


def process_submissions(token, assignment_id, assignment_desc, save_dir, course_name, context_files, use_ai):
    """Processa todas as submissoes de uma atividade: download, avaliacao e nota."""
    submissions = get_submissions(token, assignment_id)

    for submission in submissions:
        user_id = submission.get("userid")

        if _should_skip_submission(submission):
            continue

        student_dir = os.path.join(save_dir, f"Student_{user_id}")
        os.makedirs(student_dir, exist_ok=True)

        has_valid_files = _download_all_submission_files(submission, token, student_dir)

        if not has_valid_files:
            print(f"   [WARNING] User {user_id} sent ONLY invalid/binary files. Skipping.")
            continue

        if use_ai:
            _evaluate_and_grade(
                token, assignment_id, user_id, student_dir,
                assignment_desc, course_name, context_files,
            )
