from docx import Document
import PyPDF2
import pdfplumber


def read_docx(file_path):
    doc = Document(file_path)
    content = "\n".join([para.text for para in doc.paragraphs])
    return content


def read_pdf(file_path):
    text = ""
    with open(file_path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            text += page.extract_text()
    return text


def read_pdf_plumber(file_path):
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text()
    return text


def read_txt(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()
