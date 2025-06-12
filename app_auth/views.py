from rest_framework import viewsets, status
from .permissions import IsSuperAdmin
from .serializers import AdminUserSerializer
from .models import User
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth.hashers import check_password

from .serializers import CustomTokenObtainPairSerializer


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class RegisterView(APIView):
    def post(self, request):
        data = request.data
        try:
            user = User.objects.create_user(
                username=data['username'],
                email=data['email'],
                password=data['password']
            )
            return Response({"message": "Đăng ký thành công"}, status=201)
        except Exception as e:
            return Response({"error": str(e)}, status=400)


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({
            "username": request.user.username,
            "email": request.user.email,
            "is_admin": request.user.is_admin,

            "first_name": request.user.first_name,
            "last_name": request.user.last_name,
            "last_login": request.user.last_login,
            "date_joined": request.user.date_joined,
        })


class UpdateProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            "username": user.username,
            "email": user.email,
            "is_admin": user.is_admin,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "last_login": user.last_login,
            "date_joined": user.date_joined,
        })

    def post(self, request):
        user = request.user
        data = request.data

        user.first_name = data.get("first_name", user.first_name)
        user.last_name = data.get("last_name", user.last_name)
        user.username = data.get("username", user.username)
        user.email = data.get("email", user.email)

        user.save()

        return Response({"message": "Cập nhật thông tin thành công"})


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        data = request.data

        old_password = data.get("old_password")
        new_password = data.get("new_password")
        confirm_password = data.get("confirm_password")

        if not user.check_password(old_password):
            return Response({"error": "Mật khẩu cũ không đúng"}, status=400)

        if new_password != confirm_password:
            return Response({"error": "Xác nhận mật khẩu mới không khớp"}, status=400)

        user.set_password(new_password)
        user.save()
        return Response({"message": "Đổi mật khẩu thành công"}, status=200)


class AdminUserViewSet(viewsets.ModelViewSet):
    """
    API CRUD cho User, chỉ hiển thị và thao tác với các user có is_admin=True
    Chỉ admin mới được truy cập.
    """
    serializer_class = AdminUserSerializer
    permission_classes = [IsSuperAdmin]

    def get_queryset(self):
        # Chỉ lấy những user là admin
        return User.objects.filter(is_admin=True)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


# class NonAdminUserViewSet(viewsets.ReadOnlyModelViewSet):
class NonAdminUserViewSet(viewsets.ModelViewSet):
    """
    API ReadOnly cho User, chỉ hiển thị danh sách những user không phải admin
    Chỉ admin mới được truy cập.
    """
    queryset = User.objects.filter(is_admin=False)
    serializer_class = AdminUserSerializer
    permission_classes = [IsSuperAdmin]

    # def destroy(self, request, *args, **kwargs):
    #     instance = self.get_object()
    #     self.perform_destroy(instance)
    #     return Response(status=status.HTTP_204_NO_CONTENT)
