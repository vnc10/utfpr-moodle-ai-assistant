import getpass
import os

from downloader import sanitize_filename, download_material
from gemini_ai import (
    load_teacher_context, delete_files, generate_lesson_plan, markdown_to_docx,
    list_slide_pdfs, upload_single_slide, find_all_lesson_plans,
    _read_docx_as_text,
)
from google_drive import upload_to_google_docs
from grader import process_submissions
from moodle_api import authenticate, list_courses, get_course_content, get_course_assignments


def select_course(courses):
    """Displays the course list and returns the selected course."""
    for i, course in enumerate(courses):
        print(f"[{i}] {course['fullname']}")
    choice = int(input("\nSelect course number: "))
    return courses[choice]


def select_action():
    """Displays the action menu and returns the selected option."""
    print("\n--- Action Menu ---")
    print("[0] Download materials")
    print("[1] Grade exercise lists")
    print("[2] Generate lesson plan")
    choice = int(input("\nSelect action number: "))
    return choice


def ask_grading_options():
    """Asks the user for grading-specific options."""
    use_ai = input("\nUse AI to grade (10.0)? (y/n): ").lower() == 'y'
    upload_context = False
    if use_ai:
        upload_context = input("Upload slides as context? (y/n): ").lower() == 'y'
    return use_ai, upload_context


def download_materials(token, course_name, content):
    """Downloads all class materials from the course."""
    os.makedirs(course_name, exist_ok=True)

    for section in content:
        if not section.get("visible", 1):
            continue

        section_name = sanitize_filename(section.get("name", "Unnamed"))
        section_dir = os.path.join(course_name, section_name)

        for module in section.get("modules", []):
            if not module.get("visible", 1):
                continue

            os.makedirs(section_dir, exist_ok=True)
            download_material(module, token, section_dir)


def grade_exercises(token, course_name, content, assign_descriptions):
    """Downloads submissions and grades them with AI."""
    use_ai, upload_context = ask_grading_options()

    context_files = []
    if upload_context:
        context_files = load_teacher_context(course_name)

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
            if mod_type != "assign":
                continue

            module["description"] = assign_descriptions.get(module.get("instance"), "")

            os.makedirs(section_dir, exist_ok=True)
            assign_name = sanitize_filename(module.get("name", ""))
            subs_dir = os.path.join(section_dir, f"Submissions_{assign_name}")
            os.makedirs(subs_dir, exist_ok=True)
            process_submissions(
                token, module.get("instance"), module.get("description"),
                subs_dir, course_name, context_files, use_ai,
            )

    if context_files:
        print("\nCleaning up teacher's context files from Gemini API...")
        delete_files(context_files)


def select_slide(slides):
    """Displays the slide list and returns the selected path."""
    print("\n--- Available Slides ---")
    for i, path in enumerate(slides):
        print(f"[{i}] {os.path.basename(path)}")
    choice = int(input("\nSelect slide number: "))
    return slides[choice]


def select_lesson_plans(course_name):
    """Displays existing lesson plans and lets the user select which to use as context."""
    plans = find_all_lesson_plans(course_name)
    if not plans:
        print("\nNo previous lesson plans found.")
        return []

    print("\n--- Available Lesson Plans ---")
    for i, path in enumerate(plans):
        print(f"[{i}] {os.path.basename(path)}")
    print(f"\nSelect plans to use as context (e.g. 0,2,3 or 'all' or press Enter for none):")
    choice = input(">> ").strip()

    if not choice:
        return []
    if choice.lower() == "all":
        return plans

    selected = []
    for idx in choice.split(","):
        idx = idx.strip()
        if idx.isdigit() and 0 <= int(idx) < len(plans):
            selected.append(plans[int(idx)])
    return selected


def load_selected_lesson_plans(selected_paths):
    """Reads selected .docx lesson plans and returns their text content."""
    if not selected_paths:
        return ""

    all_text = ""
    print(f"\n[AI CONTEXT] Loading {len(selected_paths)} selected lesson plan(s)...")
    for filepath in selected_paths:
        filename = os.path.basename(filepath)
        print(f"   -> Reading {filename}...")
        try:
            text = _read_docx_as_text(filepath)
            all_text += f"\n\n--- ROTEIRO ANTERIOR: {filename} ---\n{text}"
        except Exception as e:
            print(f"      [WARNING] Could not read {filename}: {e}")

    return all_text


def create_lesson_plan(course_name):
    """Generates a lesson plan based on a selected slide and previous plans."""
    slides = list_slide_pdfs(course_name)
    if not slides:
        print("\nNo slides found. Download materials first.")
        return

    selected_path = select_slide(slides)

    slide_file = upload_single_slide(selected_path)
    if not slide_file:
        print("\nFailed to upload slide.")
        return

    selected_plans = select_lesson_plans(course_name)
    previous_plans_text = load_selected_lesson_plans(selected_plans)

    print("\nGenerating lesson plan with AI...")
    lesson_plan = generate_lesson_plan(course_name, slide_file, previous_plans_text)

    if lesson_plan:
        roteiros_dir = os.path.join(course_name, "Roteiros")
        os.makedirs(roteiros_dir, exist_ok=True)

        all_plans = find_all_lesson_plans(course_name)
        next_num = len(all_plans) + 1
        filename = f"Roteiro_Aula_{next_num:02d}.docx"
        output_path = os.path.join(roteiros_dir, filename)

        markdown_to_docx(lesson_plan, output_path)
        print(f"\nLesson plan saved to: {output_path}")

        upload = input("\nUpload to Google Docs? (y/n): ").lower() == 'y'
        if upload:
            print("Uploading to Google Docs...")
            try:
                doc_url = upload_to_google_docs(output_path)
                print(f"Google Docs: {doc_url}")
            except Exception as e:
                print(f"[ERROR] Failed to upload to Google Docs: {e}")
    else:
        print("\nFailed to generate lesson plan.")

    print("\nCleaning up context files from Gemini API...")
    delete_files([slide_file])


def main():
    print("=== UTFPR Moodle AI Assistant (Gemini) ===")
    username = input("Enter your username/RA: ")
    password = getpass.getpass("Enter your password: ")

    token = authenticate(username, password)

    courses = list_courses(token)
    if not courses:
        print("No courses found.")
        return

    while True:
        selected = select_course(courses)
        course_name = sanitize_filename(selected['fullname'])

        content = get_course_content(token, selected['id'])
        assign_descriptions = get_course_assignments(token, selected['id'])

        action = select_action()

        if action == 0:
            download_materials(token, course_name, content)
        elif action == 1:
            grade_exercises(token, course_name, content, assign_descriptions)
        elif action == 2:
            create_lesson_plan(course_name)
        else:
            print("Invalid option.")
            continue

        print("\nAll tasks finished!")

        again = input("\nBack to course selection? (y/n): ").lower()
        if again != 'y':
            break


if __name__ == "__main__":
    main()
