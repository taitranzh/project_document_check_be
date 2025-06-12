import math
import re
from collections import Counter
from pyvi import ViTokenizer
from .models import Document, Term, Posting


# Danh sách stopword tiếng Việt (có thể mở rộng thêm)
VIETNAMESE_STOPWORDS = {
    "và", "là", "của", "có", "cho", "đến", "trên", "không", "những",
    "một", "đã", "với", "trong", "để", "các", "khi", "từ", "này", "như",
    "vì", "nên", "vậy", "những", "rằng", "nữa", "vẫn", "ra", "vào",
}


def preprocess(text: str) -> list[str]:
    """
    Tiền xử lý văn bản tiếng Việt:
    1. Lowercase toàn bộ.
    2. Loại bỏ ký tự không phải chữ số/chữ chữ (giữ lại dấu tiếng Việt).
    3. Dùng ViTokenizer để tách từ (kết quả sẽ là một chuỗi, các từ được nối bằng dấu underscore).
    4. Tách thành list từ (split theo khoảng trắng).
    5. Loại bỏ stopwords tiếng Việt.
    Trả về danh sách các token (từ) đã xử lý.
    """
    # 1. Lowercase
    text = text.lower()

    # 2. Loại bỏ ký tự không cần thiết: chỉ giữ lại chữ (có dấu) và chữ số, thay các ký tự khác bằng khoảng trắng
    # kí tự \w sẽ khớp với chữ/số/underscore, vẫn giữ được dấu tiếng Việt
    text = re.sub(r"[^\w\s]", " ", text)

    # 3. Tách từ tiếng Việt
    #    ViTokenizer.tokenize("tôi đang học lập trình") → "tôi_đang là học_lập_trình"
    segmented = ViTokenizer.tokenize(text)

    # 4. Tách thành list token
    tokens = segmented.split() # ['a_b", "là", "a_b_c"]

    # 5. Bỏ stopword
    tokens = [tok for tok in tokens if tok not in VIETNAMESE_STOPWORDS] # ['a_b", "a_b_c"]

    return tokens


def index_document(document: Document):
    """
    Xây dựng inverted index cho Document (tính TF và cập nhật DF cho Term).
    """
    tokens = preprocess(document.content)
    term_frequencies = Counter(tokens)
    doc_len = len(tokens)
    document.doc_length = doc_len
    document.save(update_fields=['doc_length'])

    seen_terms = set()
    for term_text, freq in term_frequencies.items():
        term_obj, created = Term.objects.get_or_create(text=term_text)
        if term_text not in seen_terms:
            term_obj.doc_freq += 1
            term_obj.save(update_fields=['doc_freq'])
            seen_terms.add(term_text)

        # Tạo hoặc cập nhật Posting
        Posting.objects.update_or_create(
            term=term_obj,
            document=document,
            defaults={'term_freq': freq}
        )


def compute_idf(term_text: str) -> float:
    """
    IDF = log10( N / (1 + df(term) ) )
    """
    total_docs = Document.objects.count()
    try:
        term_obj = Term.objects.get(text=term_text)
        df = term_obj.doc_freq
    except Term.DoesNotExist:
        df = 0
    # +1 để tránh chia cho 0
    return math.log((total_docs / (1 + df) + 1e-9), 10)


def get_doc_tfidf_vector(doc_id: int) -> dict[str, float]:
    """
    Tính vector TF–IDF cho document với doc_id.
    """
    try:
        document = Document.objects.get(id=doc_id)
    except Document.DoesNotExist:
        return {}

    postings = Posting.objects.filter(document=document).select_related('term')
    if document.doc_length == 0:
        return {}

    tfidf_vector: dict[str, float] = {}
    for post in postings:
        term_text = post.term.text
        tf = post.term_freq / document.doc_length
        idf_val = compute_idf(term_text)
        tfidf_vector[term_text] = tf * idf_val
    return tfidf_vector


def cosine_similarity(vec1: dict[str, float], vec2: dict[str, float]) -> float:
    """
    Tính cosine similarity giữa hai vector TF–IDF (dạng dict term→weight).
    """
    dot = 0.0
    for term, w1 in vec1.items():
        w2 = vec2.get(term, 0.0)
        dot += w1 * w2

    mag1 = math.sqrt(sum(w * w for w in vec1.values()))
    mag2 = math.sqrt(sum(w * w for w in vec2.values()))
    if mag1 == 0 or mag2 == 0:
        return 0.0
    return dot / (mag1 * mag2)


def search_corpus(text: str, top_n: int = 5, exclude_doc_id: int = None) -> list[tuple[Document, float]]:
    """
    Kiểm tra đạo văn: 
    - Tiền xử lý text bằng preprocess (tiếng Việt).
    - Tính TF–IDF cho query.
    - Lấy tập các document đã lưu trong database (có ít nhất một term chung).
    - Tính cosine similarity giữa vector query và mỗi document, trả về top_n kết quả.
    - Có thể loại document có id == exclude_doc_id.
    """
    tokens = preprocess(text)
    if not tokens:
        return []

    # Tạo vector TF–IDF của query
    q_tf = Counter(tokens)
    q_len = len(tokens)
    query_vec: dict[str, float] = {}
    for term_text, freq in q_tf.items():
        tf = freq / q_len
        idf_val = compute_idf(term_text)
        query_vec[term_text] = tf * idf_val

    # Lấy candidate document IDs
    candidate_ids = set()
    for term_text in set(tokens):
        try:
            term_obj = Term.objects.get(text=term_text)
            postings = Posting.objects.filter(
                term=term_obj).values_list('document_id', flat=True)
            candidate_ids.update(postings)
        except Term.DoesNotExist:
            continue

    # Tính similarity cho mỗi document
    scored: list[tuple[Document, float]] = []
    for doc_id in candidate_ids:
        if exclude_doc_id is not None and doc_id == exclude_doc_id:
            continue  # Bỏ chính document hiện tại

        doc_vec = get_doc_tfidf_vector(doc_id)
        score = cosine_similarity(query_vec, doc_vec)
        if score > 0:
            doc = Document.objects.get(id=doc_id)
            scored.append((doc, score))

    # Sắp xếp giảm dần theo score
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:top_n]
