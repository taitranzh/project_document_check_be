from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    HomeAPI,
    CatalogViewSet,
    DocumentTypeViewSet,
    DocumentViewSet,
    PlagiarismCheckAPIView,
    DashboardView,
    PlagiarismCheckDetailAPIView,
    PlagiarismCheckListAPIView,
    DocumentExportPDFView
)

router = DefaultRouter()
router.register(
    r'catalogs',
    CatalogViewSet,
    basename='catalog'
)
router.register(
    r'document-types',
    DocumentTypeViewSet,
    basename='documenttype'
)
router.register(
    r'documents',
    DocumentViewSet,
    basename='document'
)

urlpatterns = [
    path('', HomeAPI.as_view(), name='Index'),
    path('api/', include(router.urls)),
    path(
        'plagiarism-checks/',
        PlagiarismCheckListAPIView.as_view(),
        name='plagiarism-check-list'
    ),

    path(
        'documents/<int:pk>/check/<int:check_id>/detail/',
        PlagiarismCheckDetailAPIView.as_view(),
        name='plagiarism-check-detail'
    ),

    path(
        'dashboard/overview/',
        DashboardView.as_view(),
        name='dashboard-overview'
    ),
    path(
        'dashboard/statistics/',
        DashboardView.as_view(),
        name='dashboard-statistics'
    ),

    path('upload/', PlagiarismCheckAPIView.as_view(), name='pdf-upload'),
    path(
        'api/documents/<int:pk>/download_pdf/',
        DocumentExportPDFView.as_view(),
        name='document-export-pdf'
    ),
]
