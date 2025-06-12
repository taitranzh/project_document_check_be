from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    Catalog,
    DocumentType,
    Document,
    PlagiarismCheck
)
import os

User = get_user_model()


class DocumentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentType
        fields = '__all__'
        extra_kwargs = {
            'id': {'read_only': True}
        }

class CatalogSerializer(serializers.ModelSerializer):
    class Meta:
        model = Catalog
        fields = '__all__'
        extra_kwargs = {
            'id': {'read_only': True}
        }



class DocumentSerializer(serializers.ModelSerializer):
    catalog_name = serializers.CharField(source='catalog.name', read_only=True)
    document_type_name = serializers.CharField(source='document_type.name', read_only=True)
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), required=False, allow_null=True
    )
    catalog = serializers.PrimaryKeyRelatedField(
        queryset=Catalog.objects.all(), required=False, allow_null=True
    )
    document_type = serializers.PrimaryKeyRelatedField(
        queryset=DocumentType.objects.all(), required=False, allow_null=True
    )

    plagiarism_percentage = serializers.SerializerMethodField()
    plagiarism_check_id = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = [
            'id',
            'user',
            'title',
            'author',
            'catalog',
            'catalog_name',             
            'document_type',
            'document_type_name', 
            'publication_year',
            'file',
            'original_filename',
            'file_extension',
            'content',
            'doc_length',
            'uploaded_at',
            'plagiarism_check_id',
            'plagiarism_percentage',  # thêm field này
        ]
        read_only_fields = ['original_filename',
                            'file_extension', 'uploaded_at']

    def get_plagiarism_percentage(self, obj):
        latest_check = obj.checks.order_by('-checked_at').first()
        if latest_check:
            return latest_check.plagiarism_percentage
        return None
    
    def get_plagiarism_check_id(self, obj):
        latest_check = obj.checks.order_by('-checked_at').first()
        if latest_check:
            return latest_check.id
        return None

    def create(self, validated_data):
        """
        Override create để tự động lấy original filename, extension,
        và tính doc_length (nếu đã có content).
        """
        uploaded_file = validated_data.get('file', None)
        if uploaded_file:
            filename = os.path.basename(uploaded_file.name)
            name, ext = os.path.splitext(filename)
            validated_data['original_filename'] = filename
            validated_data['file_extension'] = ext.lower()

        # Nếu bạn muốn tự tính doc_length dựa vào content (hãy chắc content đã được set sẵn)
        content = validated_data.get('content', '')
        validated_data['doc_length'] = len(content)

        document = super().create(validated_data)
        return document

    def update(self, instance, validated_data):
        """
        Khi update mà có thay đổi file mới, cập nhật lại original_filename, file_extension.
        """
        uploaded_file = validated_data.get('file', None)
        if uploaded_file:
            filename = os.path.basename(uploaded_file.name)
            name, ext = os.path.splitext(filename)
            validated_data['original_filename'] = filename
            validated_data['file_extension'] = ext.lower()

        # Cập nhật doc_length nếu content thay đổi
        if 'content' in validated_data:
            validated_data['doc_length'] = len(
                validated_data.get('content', ''))

        return super().update(instance, validated_data)


class DocumentUploadSerializer(serializers.ModelSerializer):
    file = serializers.FileField()

    class Meta(DocumentSerializer.Meta):
        fields = DocumentSerializer.Meta.fields 


class PlagiarismCheckSerializer(serializers.ModelSerializer):
    document_title = serializers.CharField(
        source='document.title', read_only=True)
    matched_percent = serializers.SerializerMethodField()

    class Meta:
        model = PlagiarismCheck
        fields = [
            'id',
            'document_id',
            'document_title',
            'checked_at',
            'plagiarism_percentage',
            'matched_percent',
        ]

    def get_matched_percent(self, obj):
        if not obj.duplicate_sources:
            return 0.0
        try:
            return max(src.get('matched_percent', 0) for src in obj.duplicate_sources)
        except Exception:
            return 0.0
