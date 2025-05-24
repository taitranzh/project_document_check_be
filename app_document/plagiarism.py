from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank

from .models import Document
from .utils import read_docx, read_pdf, read_txt

def handle_upload(file):
    ext = file.name.split('.')[-1].lower()
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp:
        tmp.write(file.read())
        tmp_path = tmp.name

    if ext == 'docx':
        content = read_docx(tmp_path)
    elif ext == 'pdf':
        content = read_pdf(tmp_path)
    elif ext == 'txt':
        content = read_txt(tmp_path)
    else:
        raise ValueError("Unsupported file type")
    
    return content

def check_plagiarism(content):
    query = SearchQuery(content)
    results = Document.objects.annotate(
        rank=SearchRank(SearchVector('content'), query)
    ).filter(rank__gte=0.1).order_by('-rank')  # Chỉ lấy kết quả tương đồng

    return results