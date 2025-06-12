from django.http import FileResponse, Http404
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views import View
from django.urls import reverse
# from User.is_authenticate import is_not_authenticated

from rest_framework import viewsets, permissions, filters, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from .serializers import (
    CatalogSerializer,
    DocumentTypeSerializer,
    DocumentSerializer,
    DocumentUploadSerializer,
    PlagiarismCheckSerializer,
)

from .utils import extract_text_from_file, extract_matching_blocks
from .models import (
    Catalog,
    DocumentType,
    Document,
    PlagiarismCheck
)
from .plagiarism import search_corpus, index_document
from app_auth.permissions import IsAdminOrReadOnly


class HomeAPI(APIView):
    def get(self, request):
        return Response('Project Document Check Started')


class CatalogViewSet(viewsets.ModelViewSet):
    queryset = Catalog.objects.all()
    serializer_class = CatalogSerializer
    permission_classes = [IsAdminOrReadOnly]

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({"message": "Delete successfully"}, status=status.HTTP_200_OK)


class DocumentTypeViewSet(viewsets.ModelViewSet):
    queryset = DocumentType.objects.all()
    serializer_class = DocumentTypeSerializer
    permission_classes = [IsAdminOrReadOnly]

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({"message": "Delete successfully"}, status=status.HTTP_200_OK)


class DocumentViewSet(viewsets.ModelViewSet):
    """
    CRUD cho Document:
    - list: GET /api/documents/
    - retrieve: GET /api/documents/{pk}/
    - create: POST /api/documents/
    - update: PUT /api/documents/{pk}/
    - partial_update: PATCH /api/documents/{pk}/
    - destroy: DELETE /api/documents/{pk}/
    """
    queryset = Document.objects.all().order_by('-uploaded_at')
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    parser_classes = (MultiPartParser, FormParser)  # để hỗ trợ upload file

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'author', 'catalog__name', 'document_type__name']
    ordering_fields = ['uploaded_at', 'publication_year']

    def perform_create(self, serializer):
        """
        Nếu bạn muốn tự động gán user hiện tại là người upload,
        hãy dùng: serializer.save(user=self.request.user)
        Nếu không, có thể bỏ qua để dùng như truyền payload bình thường.
        """
        user = self.request.user if self.request.user.is_authenticated else None
        serializer.save(user=user)


class PlagiarismCheckAPIView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, format=None):
        uploaded_files = request.FILES.getlist('files')
        if not uploaded_files:
            return Response({"detail": "No files provided."}, status=status.HTTP_400_BAD_REQUEST)

        results = []
        for file in uploaded_files:
            try:
                text = extract_text_from_file(file)

                doc = Document.objects.create(
                    title=file.name,
                    file=file,
                    content=text,
                    user=request.user if request.user.is_authenticated else None,
                    doc_length=len(text),
                    original_filename=file.name,
                    file_extension=file.name.split('.')[-1],
                )

                index_document(doc)

                # Search corpus
                matches = search_corpus(text, top_n=5, exclude_doc_id=doc.id)

                if matches:
                    matched_doc, score = matches[0]
                    db_text = matched_doc.content

                    matched_blocks = extract_matching_blocks(text, db_text)

                    plagiarism_check = PlagiarismCheck.objects.create(
                        document=doc,
                        plagiarism_percentage=round(score * 100, 2),
                        duplicate_sources=[{
                            "source_id": matched_doc.id,
                            "source_title": matched_doc.title,
                            "matched_percent": round(score * 100, 2),
                            "highlights": matched_blocks
                        }],
                        highlights=matched_blocks
                    )

                    # Render HTML highlight
                    highlighted_ranges = []
                    last_idx = 0
                    for match in matched_blocks:
                        start_idx = text.find(match, last_idx)
                        if start_idx != -1:
                            highlighted_ranges.append({
                                "start": start_idx,
                                "end": start_idx + len(match)
                            })
                            last_idx = start_idx + len(match)

                    highlighted_ranges.sort(key=lambda x: x['start'])
                    last_idx = 0
                    html_content = ""
                    for hl in highlighted_ranges:
                        html_content += text[last_idx:hl['start']]
                        html_content += f'<span style="background-color: yellow;">{text[hl["start"]:hl["end"]]}</span>'
                        last_idx = hl['end']
                    html_content += text[last_idx:]

                    results.append({
                        "file_name": file.name,
                        "document_id": doc.id,
                        "plagiarism_check_id": plagiarism_check.id,
                        "plagiarism_percentage": plagiarism_check.plagiarism_percentage,
                        "html_content": html_content,
                        "highlights": highlighted_ranges
                    })
                else:
                    plagiarism_check = PlagiarismCheck.objects.create(
                        document=doc,
                        plagiarism_percentage=0.0,
                        duplicate_sources=[],
                        highlights=[]
                    )
                    results.append({
                        "file_name": file.name,
                        "document_id": doc.id,
                        "plagiarism_check_id": plagiarism_check.id,
                        "plagiarism_percentage": 0.0,
                        "html_content": text,
                        "highlights": []
                    })

            except Exception as e:
                results.append({
                    "file_name": file.name,
                    "error": str(e)
                })

        return Response({"results": results})


class DashboardView(APIView):
    def get(self, request):
        return Response({
            "total_documents": Document.objects.count(),
        })


class PlagiarismCheckDetailAPIView(APIView):
    def get(self, request, pk, check_id):
        try:
            check = PlagiarismCheck.objects.get(id=check_id, document_id=pk)
            text = check.document.content

            # Hàm tính màu dựa theo % matched
            def get_highlight_color(percent):
                percent = max(0, min(percent, 100))  # Clamp từ 0 → 100
                if percent < 20:
                    return '#ccffcc'  # xanh nhạt
                elif percent < 50:
                    return '#ffff99'  # vàng
                elif percent < 80:
                    return '#ff6666'  # đỏ
                else:
                    return 'yellow'  # cam

            # Render lại html content từ highlights
            highlighted_ranges = []
            for match in check.highlights or []:
                start_idx = text.find(match)
                if start_idx != -1:
                    highlighted_ranges.append({
                        "start": start_idx,
                        "end": start_idx + len(match)
                    })

            highlighted_ranges.sort(key=lambda x: x['start'])
            last_idx = 0
            html_content = ""

            # Tính matched_percent cao nhất (nếu có)
            matched_percent = 0.0
            if check.duplicate_sources:
                try:
                    matched_percent = max(
                        src.get('matched_percent', 0) for src in check.duplicate_sources
                    )
                except Exception:
                    matched_percent = 0.0

            # Tổng số văn bản đã so sánh (số document trong search_corpus lúc tạo check)
            total_compared_docs = len(check.duplicate_sources or [])

            # Render html content với màu
            for hl in highlighted_ranges:
                html_content += text[last_idx:hl['start']]
                # hiện tại fallback % chung
                color = get_highlight_color(matched_percent)
                html_content += (
                    f'<span style="background-color: {color};">'
                    f'{text[hl["start"]:hl["end"]]}'
                    f'</span>'
                )
                last_idx = hl['end']
            html_content += text[last_idx:]

            return Response({
                "document_id": pk,
                "plagiarism_check_id": check_id,
                "plagiarism_percentage": check.plagiarism_percentage,
                "matched_percent": matched_percent,
                "html_content": html_content,
                "highlights": highlighted_ranges,
                "doc_length": check.document.doc_length,
                "total_compared_docs": total_compared_docs
            })

        except PlagiarismCheck.DoesNotExist:
            return Response({"detail": "PlagiarismCheck not found."}, status=404)


class PlagiarismCheckListAPIView(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request):
        queryset = PlagiarismCheck.objects.all().order_by('checked_at')
        serializer = PlagiarismCheckSerializer(queryset, many=True)
        return Response(serializer.data)


class DocumentExportPDFView(View):
    def get(self, request, pk):
        try:
            document = Document.objects.get(id=pk)
        except Document.DoesNotExist:
            raise Http404("Không tìm thấy tài liệu.")

        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4

        p.setFont("Helvetica", 12)
        lines = document.content.split('\n')

        y = height - 50
        for line in lines:
            p.drawString(50, y, line)
            y -= 20
            if y < 50:
                p.showPage()
                p.setFont("Helvetica", 12)
                y = height - 50

        p.save()
        buffer.seek(0)

        return FileResponse(buffer, as_attachment=True, filename=f"{document.title or 'document'}.pdf", content_type='application/pdf')
