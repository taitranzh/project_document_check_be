from django.db import models
from django.db.models import JSONField
from django.contrib.postgres.fields import ArrayField
from app_auth.models import User
from django.utils.translation import gettext_lazy as _
from django.db.models.signals import post_delete
from django.dispatch import receiver


# User: Mô hình người dùng, có thể là quản trị viên hoặc người kiểm tra đạo văn.
# Document: Mô hình tài liệu do người dùng tải lên.
# PlagiarismCheck: Lưu kết quả kiểm tra đạo văn, tỷ lệ trùng lặp và nguồn trùng lặp.
# UserActivity: Ghi nhận lịch sử hoạt động của người dùng.


class Catalog(models.Model):
    name = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)   # Ngày tạo
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class DocumentType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)   # Ngày tạo
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Document(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        blank=True,
        null=True
    )
    title = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    author = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    catalog = models.ForeignKey(
        Catalog,
        on_delete=models.SET_NULL,
        blank=True,
        null=True
    )
    document_type = models.ForeignKey(
        DocumentType,
        on_delete=models.SET_NULL,
        blank=True,
        null=True
    )

    publication_year = models.PositiveIntegerField(
        blank=True,
        null=True
    )
    file = models.FileField(
        _('Tệp văn bản'),
        upload_to='documents/%Y/%m/%d/',
        help_text=_('Tệp văn bản (txt, pdf, docx)')
    )
    original_filename = models.CharField(max_length=255, blank=True, null=True)
    file_extension = models.CharField(max_length=20, blank=True, null=True)
    content = models.TextField(blank=True, null=True)
    doc_length = models.IntegerField(default=0)
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

    # @receiver(post_delete, sender=Document)
    # def delete_file_on_document_delete(sender, instance, **kwargs):
    #     """
    #     Khi một Document bị xóa, xóa luôn file trên disk (nếu có).
    #     """
    #     if instance.file:
    #         instance.file.delete(save=False)


class Term(models.Model):
    """
    A unique term (word) in the corpus.
    - text: the term string (lowercase)
    - doc_freq: number of documents containing this term
    """
    text = models.CharField(max_length=100, primary_key=True)
    doc_freq = models.IntegerField(default=0)

    def __str__(self):
        return self.text


class Posting(models.Model):
    """
    A posting (inverted index entry) linking a term to a document.
    - term: foreign key to Term
    - document: foreign key to Document
    - term_freq: frequency of this term in the document
    """
    term = models.ForeignKey(
        Term,
        on_delete=models.CASCADE,
        related_name='postings'
    )
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='postings'
    )
    term_freq = models.IntegerField()

    class Meta:
        unique_together = ('term', 'document')

    def __str__(self):
        return f"({self.term.text}, Doc {self.document.id}) → tf={self.term_freq}"


class PlagiarismCheck(models.Model):
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='checks'
    )
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
