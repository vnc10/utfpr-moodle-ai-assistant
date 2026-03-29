import getpass
import os

from downloader import sanitize_filename, download_material
from gemini_ai import load_teacher_context, delete_files
from grader import process_submissions
from moodle_api import authenticate, list_courses, get_course_content, get_course_assignments


def select_course(courses):
    """Exibe a lista de cursos e retorna o curso selecionado."""
    for i, course in enumerate(courses):
        print(f"[{i}] {course['fullname']}")
    choice = int(input("\nSelect course number: "))
    return courses[choice]


def ask_options():
    """Pergunta ao usuario quais operacoes deseja executar."""
    dl_materials = input("\nDownload class materials? (y/n): ").lower() == 'y'
    dl_submissions = input("Download student submissions? (y/n): ").lower() == 'y'

    use_ai = False
    upload_context = False
    if dl_submissions:
        use_ai = input("Use AI to grade (10.0)? (y/n): ").lower() == 'y'
        if use_ai:
            upload_context = input("Upload slides as context? (y/n): ").lower() == 'y'

    return dl_materials, dl_submissions, use_ai, upload_context


def process_course(token, course_name, content, assign_descriptions, dl_materials, dl_submissions, use_ai, context_files):
    """Itera pelas secoes do curso, baixando materiais e processando submissoes."""
    os.makedirs(course_name, exist_ok=True)

    for section in content:
        if not section.get("visible", 1):
            continue

        section_name = sanitize_filename(section.get("name", "Unnamed"))
        section_dir = os.path.join(course_name, section_name)

        for module in section.get("modules", []):
            if not module.get("visible", 1):
                continue

            mod_type = module.get("modname")

            if mod_type == "assign":
                module["description"] = assign_descriptions.get(module.get("instance"), "")

            if dl_materials:
                os.makedirs(section_dir, exist_ok=True)
                download_material(module, token, section_dir)

            if dl_submissions and mod_type == "assign":
                os.makedirs(section_dir, exist_ok=True)
                assign_name = sanitize_filename(module.get("name", ""))
                subs_dir = os.path.join(section_dir, f"Submissions_{assign_name}")
                os.makedirs(subs_dir, exist_ok=True)
                process_submissions(
                    token, module.get("instance"), module.get("description"),
                    subs_dir, course_name, context_files, use_ai,
                )


def main():
    print("=== UTFPR Moodle AI Assistant (Gemini) ===")
    username = input("Enter your username/RA: ")
    password = getpass.getpass("Enter your password: ")

    token = authenticate(username, password)

    courses = list_courses(token)
    if not courses:
        print("No courses found.")
        return

    selected = select_course(courses)
    course_name = sanitize_filename(selected['fullname'])

    content = get_course_content(token, selected['id'])
    assign_descriptions = get_course_assignments(token, selected['id'])

    dl_materials, dl_submissions, use_ai, upload_context = ask_options()

    context_files = []
    if upload_context:
        context_files = load_teacher_context(course_name)

    process_course(
        token, course_name, content, assign_descriptions,
        dl_materials, dl_submissions, use_ai, context_files,
    )

    if context_files:
        print("\nCleaning up teacher's context files from Gemini API...")
        delete_files(context_files)

    print("\nAll tasks finished!")


if __name__ == "__main__":
    main()
