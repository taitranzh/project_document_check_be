from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    CatalogViewSet,
    DocumentTypeViewSet,
    HomeAPI,
    FileUploadAPI
)

router = DefaultRouter()
router.register(r'catalogs', CatalogViewSet, basename='catalog')
router.register(r'document-types', DocumentTypeViewSet,
                basename='documenttype')

urlpatterns = [
    path('', HomeAPI.as_view(), name='Index'),
    path('api/', include(router.urls)),
    path('upload/', FileUploadAPI.as_view(), name='pdf-upload'),
]
