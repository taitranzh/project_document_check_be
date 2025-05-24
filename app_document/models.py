from django.db import models
from django.db.models import JSONField
from django.contrib.postgres.fields import ArrayField
from app_auth.models import User

# User: Mô hình người dùng, có thể là quản trị viên hoặc người kiểm tra đạo văn.
# Document: Mô hình tài liệu do người dùng tải lên.
# PlagiarismCheck: Lưu kết quả kiểm tra đạo văn, tỷ lệ trùng lặp và nguồn trùng lặp.
# UserActivity: Ghi nhận lịch sử hoạt động của người dùng.


class Catalog(models.Model):
    name = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)  
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class DocumentType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)  
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Document(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, blank=True, null=True)
    title = models.CharField(max_length=255, blank=True, null=True)
    author = models.CharField(max_length=255, blank=True, null=True)
    catalog = models.ForeignKey(
        Catalog, on_delete=models.SET_NULL, blank=True, null=True)
    document_type = models.ForeignKey(
        DocumentType, on_delete=models.SET_NULL, blank=True, null=True)

    publication_year = models.PositiveIntegerField()
    file = models.FileField(upload_to='media/documents/')
    original_filename = models.CharField(max_length=255, blank=True, null=True)
    file_extension = models.CharField(max_length=20, blank=True, null=True)
    content = models.TextField(blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    # def save(self, *args, **kwargs):
    #     # Nếu có file và chưa lưu tên gốc hoặc đuôi file
    #     if self.file and not self.original_filename:
    #         filename = os.path.basename(self.file.name)
    #         self.original_filename = filename
    #         _, ext = os.path.splitext(filename)
    #         self.file_extension = ext.lower()
    #     super().save(*args, **kwargs)


class PlagiarismCheck(models.Model):
    document = models.ForeignKey(
        Document, on_delete=models.CASCADE, related_name='checks')
    checked_at = models.DateTimeField(auto_now_add=True)

    plagiarism_percentage = models.FloatField()

    duplicate_sources = JSONField(blank=True, null=True)

    highlights = ArrayField(
        models.TextField(),
        blank=True,
        null=True,
        help_text="List of matched text snippets"
    )

    report_file = models.FileField(upload_to='reports/', null=True, blank=True)

    def __str__(self):
        return f"{self.document.title} - {self.plagiarism_percentage}%"
