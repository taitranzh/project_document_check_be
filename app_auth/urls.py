from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenBlacklistView
from django.urls import path, include
from .views import (
    ChangePasswordView,
    CustomTokenObtainPairView,
    RegisterView,
    ProfileView,
    UpdateProfileView,
    AdminUserViewSet,
    NonAdminUserViewSet
)

router = DefaultRouter()
router.register(
    r'admin-users',
    AdminUserViewSet,
    basename='adminuser'
)
router.register(
    r'customer-users',
    NonAdminUserViewSet,
    basename='nonadminuser'
)

urlpatterns = [
    path("", include(router.urls)),
    path("register/", RegisterView.as_view(), name="register"),
    path("profile/", ProfileView.as_view(), name="profile"),
    path("update-profile/", UpdateProfileView.as_view(), name="update_profile"),
    path("change-password/", ChangePasswordView.as_view(), name="change_password"),

    path("token/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("token/logout/", TokenBlacklistView.as_view(), name="token_blacklist"),
]
