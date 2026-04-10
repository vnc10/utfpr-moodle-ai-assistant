import os
import re
import zipfile

import rarfile

import requests

from config import FORBIDDEN_EXTENSIONS


def sanitize_filename(name):
    """Remove caracteres invalidos para nomes de arquivo."""
    return re.sub(r'[\\/*?:"<>|]', "", name).strip()


def download_file(url, filepath):
    """Baixa um arquivo de uma URL e salva no caminho especificado."""
    try:
        response = requests.get(url, stream=True, verify=False)
        response.raise_for_status()
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except Exception as e:
        print(f"   [ERROR] Failed to download {os.path.basename(filepath)}: {e}")
        return False


def _resolve_google_url(raw_url):
    """Converte URLs do Google Docs/Slides para links de exportacao em PDF."""
    if "docs.google.com/presentation/d/" in raw_url:
        base = raw_url.split("/edit")[0].split("/view")[0].split("/pub")[0]
        return f"{base}/export/pdf", "download"
    if "docs.google.com/document/d/" in raw_url:
        base = raw_url.split("/edit")[0].split("/view")[0]
        return f"{base}/export?format=pdf", "download"
    return None, "unsupported"


def _collect_urls_from_module(module, token):
    """Extrai URLs para download a partir de um modulo do Moodle."""
    urls = []
    mod_type = module.get("modname")
    contents = module.get("contents", [])

    if contents:
        file_url = contents[0].get("fileurl")
        if file_url:
            if mod_type == "url":
                urls.append({"url": file_url, "type": "external", "ext": ".pdf"})
            elif mod_type == "resource":
                separator = "&" if "?" in file_url else "?"
                ext = os.path.splitext(contents[0].get("filename", ""))[1] or ".pdf"
                urls.append({
                    "url": f"{file_url}{separator}token={token}",
                    "type": "native",
                    "ext": ext,
                })

    description = module.get("description", "")
    if description:
        for link in re.findall(r'https?://[^\s<\"\']+', description):
            urls.append({"url": link, "type": "external", "ext": ".pdf"})

    return urls


def download_material(module, token, save_dir):
    """Baixa o material de um modulo do Moodle (PDFs, slides, docs)."""
    mod_name = sanitize_filename(module.get("name", "Unnamed_File"))
    urls = _collect_urls_from_module(module, token)

    if not urls:
        return

    for index, item in enumerate(urls):
        raw_url = item["url"]
        suffix = f"_{index + 1}" if len(urls) > 1 else ""
        filename = f"{mod_name}{suffix}{item['ext']}"

        if item["type"] == "native":
            filepath = os.path.join(save_dir, filename)
            if os.path.exists(filepath):
                print(f"   [SKIPPED] {filename} (Already exists)")
                continue
            print(f"   [DOWNLOADING] {filename}...")
            download_file(raw_url, filepath)
            continue

        # URLs externas (Google Docs/Slides)
        resolved_url, kind = _resolve_google_url(raw_url)

        if kind == "download" and resolved_url:
            filepath = os.path.join(save_dir, filename)
            if os.path.exists(filepath):
                print(f"   [SKIPPED] {filename} (Already exists)")
                continue
            print(f"   [DOWNLOADING] {filename}...")
            download_file(resolved_url, filepath)


def download_submission_file(file_info, token, student_dir):
    """Baixa um arquivo de submissao de aluno. Retorna True se valido."""
    fileurl = file_info.get("fileurl")
    filename = file_info.get("filename")

    if not fileurl or filename == ".":
        return False

    if any(filename.lower().endswith(ext) for ext in FORBIDDEN_EXTENSIONS):
        return False

    filepath = os.path.join(student_dir, filename)

    if not os.path.exists(filepath):
        separator = "&" if "?" in fileurl else "?"
        print(f"      [DOWNLOADING] {filename}...")
        success = download_file(f"{fileurl}{separator}token={token}", filepath)

        if success and filename.lower().endswith(".zip"):
            try:
                with zipfile.ZipFile(filepath, 'r') as zip_ref:
                    zip_ref.extractall(student_dir)
            except Exception as e:
                print(f"      [ERROR] Failed to extract {filename}: {e}")

        if success and filename.lower().endswith(".rar"):
            try:
                with rarfile.RarFile(filepath, 'r') as rar_ref:
                    rar_ref.extractall(student_dir)
            except Exception as e:
                print(f"      [ERROR] Failed to extract {filename}: {e}")

    return True
