import sys
import requests

from config import LOGIN_URL, API_URL


def authenticate(username, password):
    """Autentica no Moodle e retorna o token de acesso."""
    print("\nAuthenticating...")
    data = {
        "username": username,
        "password": password,
        "service": "moodle_mobile_app",
    }
    response = requests.post(LOGIN_URL, data=data)
    result = response.json()

    if "token" in result:
        print("Login successful!")
        return result["token"]

    print("Login failed:", result.get("error", "Unknown error"))
    sys.exit(1)


def list_courses(token):
    """Retorna a lista de cursos visiveis do usuario."""
    print("Fetching your courses...\n")
    data = {
        "wstoken": token,
        "wsfunction": "core_course_get_enrolled_courses_by_timeline_classification",
        "moodlewsrestformat": "json",
        "classification": "all",
    }
    response = requests.post(API_URL, data=data)
    all_courses = response.json().get("courses", [])
    return [course for course in all_courses if course.get("visible")]


def get_course_content(token, course_id):
    """Retorna o conteudo completo de um curso (secoes e modulos)."""
    data = {
        "wstoken": token,
        "wsfunction": "core_course_get_contents",
        "moodlewsrestformat": "json",
        "courseid": course_id,
    }
    return requests.post(API_URL, data=data).json()


def get_course_assignments(token, course_id):
    """Retorna um dicionario {assignment_id: intro/descricao} para o curso."""
    data = {
        "wstoken": token,
        "wsfunction": "mod_assign_get_assignments",
        "moodlewsrestformat": "json",
        "courseids[0]": course_id,
    }
    result = requests.post(API_URL, data=data).json()

    assign_intros = {}
    for course in result.get("courses", []):
        for assign in course.get("assignments", []):
            assign_intros[assign["id"]] = assign.get("intro", "")
    return assign_intros


def get_submissions(token, assignment_id):
    """Retorna a lista de submissoes de uma atividade."""
    data = {
        "wstoken": token,
        "wsfunction": "mod_assign_get_submissions",
        "moodlewsrestformat": "json",
        "assignmentids[0]": assignment_id,
    }
    result = requests.post(API_URL, data=data).json()

    assignments = result.get("assignments", [])
    if not assignments:
        return []
    return assignments[0].get("submissions", [])


def post_grade(token, assignment_id, user_id, feedback_html, grade=10.0):
    """Envia nota e feedback para o Moodle."""
    data = {
        "wstoken": token,
        "wsfunction": "mod_assign_save_grade",
        "moodlewsrestformat": "json",
        "assignmentid": assignment_id,
        "userid": user_id,
        "grade": grade,
        "applytoall": 1,
        "attemptnumber": -1,
        "addattempt": 0,
        "workflowstate": "graded",
        "plugindata[assignfeedbackcomments_editor][text]": feedback_html,
        "plugindata[assignfeedbackcomments_editor][format]": 1,
    }

    try:
        response = requests.post(API_URL, data=data)
        result = response.json()

        if result is None:
            print(f"      [SUCCESS] Nota e feedback salvos no Moodle!")
        elif isinstance(result, dict) and "exception" in result:
            print(f"      [MOODLE ERROR] {result.get('message')}")
        else:
            print(f"      [MOODLE RESPONSE] {result}")
    except Exception as e:
        print(f"      [HTTP ERROR] Falha ao comunicar com o Moodle: {e}")
