# import chardet
# import io
# import PyPDF2
# import pdfplumber
# from pdfminer.high_level import extract_text_to_fp
from difflib import SequenceMatcher
import os
import tempfile
from django.core.files.uploadedfile import UploadedFile
from pypdf import PdfReader
from docx import Document as DocxDocument


def extract_text_from_file(uploaded_file: UploadedFile) -> str:
    """
    Nhận UploadedFile (.txt, .pdf, .docx), 
    phát hiện định dạng theo đuôi tên và gọi hàm tương ứng.
    """
    # file_path = document.file.path
    # ext = os.path.splitext(file_path)[1].lower()

    name = uploaded_file.name.lower()
    if name.endswith('.txt'):
        return _extract_txt(uploaded_file)
    elif name.endswith('.pdf'):
        return _extract_pdf(uploaded_file)
    elif name.endswith('.docx'):
        return _extract_docx(uploaded_file)
    else:
        raise ValueError("Unsupported file type. Use .txt, .pdf, or .docx")


def _extract_txt(uploaded_file: UploadedFile) -> str:
    data = uploaded_file.read()
    try:
        return data.decode('utf-8')
    except UnicodeDecodeError:
        return data.decode('latin-1', errors='ignore')


def _extract_pdf(uploaded_file: UploadedFile) -> str:
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
        for chunk in uploaded_file.chunks():
            tmp.write(chunk)
        tmp_path = tmp.name

   
    text = ""
    try:
        reader = PdfReader(tmp_path)
        for page in reader.pages:
            page_text = page.extract_text() or ""
            text += page_text + "\n"
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass

    return text


def _extract_docx(uploaded_file: UploadedFile) -> str:
    with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as tmp:
        for chunk in uploaded_file.chunks():
            tmp.write(chunk)
        tmp_path = tmp.name

    text = ""
    try:
        doc = DocxDocument(tmp_path)
        paragraphs = [para.text for para in doc.paragraphs]
        text = "\n".join(paragraphs)
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass

    return text


def find_matches(input_text, db_text):
    matcher = SequenceMatcher(None, input_text, db_text)
    matches = []
    for block in matcher.get_matching_blocks():
        i, j, size = block
        if size > 20:  # chỉ highlight đoạn trùng lớn hơn 20 ký tự
            matched = db_text[j:j+size]
            matches.append(matched)
    return matches


def calculate_similarity(text1, text2):
    matcher = SequenceMatcher(None, text1, text2)
    ratio = matcher.ratio()  # trả về giá trị 0..1
    return round(ratio * 100, 2)  # % trùng lặp


def extract_matching_blocks(text1, text2, threshold=10):
    matcher = SequenceMatcher(None, text1, text2)
    matches = []
    for block in matcher.get_matching_blocks():
        i, j, size = block
        if size >= threshold:
            matched = text1[i:i+size]
            matches.append(matched)
    return matches


def find_plagiarism(text):
    """
    Ví dụ đơn giản: highlight những câu trùng lặp trong cùng text (SequenceMatcher).
    Với production, em có thể gọi API bên ngoài hoặc dùng thông tin từ database tài liệu mẫu.
    """
    sentences = [s.strip() for s in text.split('.') if len(s.strip()) > 30]
    highlights = []
    for i in range(len(sentences)):
        for j in range(i+1, len(sentences)):
            sm = SequenceMatcher(None, sentences[i], sentences[j])
            if sm.ratio() > 0.9:
                # tìm vị trí trong text gốc
                idx1 = text.find(sentences[i])
                highlights.append({
                    "start": idx1,
                    "end": idx1 + len(sentences[i]),
                    "score": sm.ratio()
                })
    return highlights