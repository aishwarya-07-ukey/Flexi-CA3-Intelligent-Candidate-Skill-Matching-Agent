from pypdf import PdfReader
from docx import Document


def extract_pdf_text(file_path):
    reader = PdfReader(file_path)
    text = ""

    for page in reader.pages:
        page_text = page.extract_text()

        if page_text:
            text += page_text + "\n"

    return text


def extract_docx_text(file_path):
    document = Document(file_path)
    text = ""

    for paragraph in document.paragraphs:
        text += paragraph.text + "\n"

    return text


def extract_txt_text(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()


def extract_resume_text(file_path):
    file_name = file_path.lower()

    if file_name.endswith(".pdf"):
        return extract_pdf_text(file_path)

    elif file_name.endswith(".docx"):
        return extract_docx_text(file_path)

    elif file_name.endswith(".txt"):
        return extract_txt_text(file_path)

    else:
        return "Unsupported file format."