from rest_framework import serializers
from .models import (
    Catalog,
    DocumentType,
    Document
)


class CatalogSerializer(serializers.ModelSerializer):
    class Meta:
        model = Catalog
        fields = '__all__'


class DocumentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentType
        fields = '__all__'


class DocumentUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = '__all__'
