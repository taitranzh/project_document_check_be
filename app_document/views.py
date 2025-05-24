from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views import View
from django.urls import reverse
# from User.is_authenticate import is_not_authenticated

from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from .serializers import (
    CatalogSerializer,
    DocumentTypeSerializer,
    DocumentUploadSerializer
)

from .models import (
    Catalog,
    DocumentType,
    Document
)
from .plagiarism import handle_upload, check_plagiarism
from .permissions import IsAdminOrReadOnly


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


class PlagiarismCheckAPI(APIView):
    def post(self, request):
        file = request.FILES['file']
        content = handle_upload(file)

        # Save Document
        doc = Document.objects.create(
            title=file.name,
            file=file,
            content=content
        )

        # Find Plagiarism
        matches = check_plagiarism(content)
        data = [
            {
                'title': m.title,
                'matched_percent': round(m.rank * 100, 2),
                'excerpt': m.content[:300]
            }
            for m in matches
        ]

        return Response({'matches': data})


class FileUploadAPI(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, format=None):
        serializer = DocumentUploadSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "File uploaded successfully", "data": serializer.data})
        return Response(serializer.errors, status=400)


class HomeAPI(APIView):
    def get(self, request):
        return Response('Project Document Check Started')
